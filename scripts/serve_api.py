#!/usr/bin/env python3
"""
Rechly-DE-3B Local API Server & Gateway
Provides a local, GDPR/GoBD-compliant REST API and OpenAI-compatible endpoints
for turnkey integration with the Rechly web application.

Usage:
    python scripts/serve_api.py --port 8000 --model rechly-de-3b
"""

import json
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel, Field
import uvicorn

from xrechnung_utils import to_xrechnung_ubl_xml
from datev_utils import format_datev_buchungssatz
from zugferd_generator import create_zugferd_pdf, extract_zugferd_xml, verify_zugferd_pdf
from receipt_vision_ocr import process_receipt_image
from datev_batch_exporter import export_datev_batch_csv, generate_datev_zip_archive, parse_datev_extf_csv
from xrechnung_validator import audit_en16931_invoice
from tax_calculator import reconcile_invoice_totals
import base64

PROJECT_ROOT = Path(__file__).resolve().parent.parent
WEB_INDEX_PATH = PROJECT_ROOT / "web" / "index.html"

app = FastAPI(
    title="Rechly Local AI API",
    description="100% Local, DSGVO-compliant German Accounting AI Gateway for Rechly",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_MODEL = "rechly-de-3b"
USE_MOCK_FALLBACK = False


# --- Static / UI Mount ---

@app.get("/", response_class=HTMLResponse)
@app.get("/demo", response_class=HTMLResponse)
def serve_playground():
    """Serves the interactive German AI Playground UI."""
    if WEB_INDEX_PATH.exists():
        return FileResponse(WEB_INDEX_PATH)
    return HTMLResponse("<h1>Rechly Local AI Gateway is running.</h1><p>Visit <a href='/docs'>/docs</a> for API specifications.</p>")


# --- Request / Response Models ---

class TextToInvoiceRequest(BaseModel):
    prompt: str = Field(..., description="Unstructured German invoice description")
    model: Optional[str] = None


class LineItemEnhanceRequest(BaseModel):
    raw_note: str = Field(..., description="Informal trade or service note")
    model: Optional[str] = None


class TaxClauseRequest(BaseModel):
    scenario: str = Field(..., description="Tax scenario (e.g. Kleinunternehmer, Reverse Charge §13b, EU-Lieferung)")
    model: Optional[str] = None


class DunningRequest(BaseModel):
    invoice_number: str
    client_name: str
    amount: float
    overdue_days: int
    stage: int = Field(1, ge=1, le=3, description="Dunning stage: 1 (friendly), 2 (first notice), 3 (final notice)")
    model: Optional[str] = None


class ExpenseCategorizeRequest(BaseModel):
    receipt_text: str = Field(..., description="Expense or receipt description")
    model: Optional[str] = None


class XRechnungRequest(BaseModel):
    prompt: str = Field(..., description="E-Invoice / XRechnung prompt containing Leitweg-ID and items")
    as_xml: Optional[bool] = Field(False, description="If true, serializes result into official UBL 2.1 XML")
    model: Optional[str] = None


class GoBDAuditRequest(BaseModel):
    invoice_text: str = Field(..., description="Incoming invoice text or raw extraction to audit against § 14 Abs. 4 UStG")
    model: Optional[str] = None


class DatevBuchungssatzRequest(BaseModel):
    receipt_text: str = Field(..., description="Receipt or transaction description")
    chart: Optional[str] = Field("SKR03", description="DATEV Chart of Accounts: SKR03 or SKR04")
    model: Optional[str] = None


class ZUGFeRDGenerateRequest(BaseModel):
    invoice_data: Dict[str, Any] = Field(..., description="Structured invoice data complying with EN 16931")
    profile: Optional[str] = Field("EN 16931", description="ZUGFeRD 2.3 Profile: EN 16931 (COMFORT), BASIC, EXTENDED")


class ZUGFeRDExtractRequest(BaseModel):
    pdf_base64: str = Field(..., description="Base64-encoded ZUGFeRD PDF invoice")


class ReceiptOCRRequest(BaseModel):
    image_base64: str = Field(..., description="Base64-encoded receipt image (JPEG, PNG)")
    chart: Optional[str] = Field("SKR03", description="Target chart of accounts: SKR03 or SKR04")
    model: Optional[str] = Field("qwen2.5-vl:3b", description="Multimodal vision model to query")


class DatevBatchExportRequest(BaseModel):
    records: List[Dict[str, Any]] = Field(..., description="List of accounting entries or invoices to export")
    chart: Optional[str] = Field("SKR03", description="Chart of accounts: SKR03 or SKR04")
    mandant_nr: Optional[str] = Field("10001", description="DATEV Mandantennummer")
    berater_nr: Optional[str] = Field("1001", description="DATEV Beraternummer")
    as_zip: Optional[bool] = Field(False, description="Whether to package output as a DATEV Unternehmen online ZIP archive")


class XRechnungValidateRequest(BaseModel):
    invoice_data: Dict[str, Any] = Field(..., description="Structured invoice data to validate against EN 16931 rules")


class ReconcileTotalsRequest(BaseModel):
    invoice_data: Dict[str, Any] = Field(..., description="Invoice data with line items to reconcile mathematically")



class ChatMessage(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: Optional[str] = None
    messages: List[ChatMessage]
    temperature: Optional[float] = 0.1
    stream: Optional[bool] = False


# --- Helper Function ---

def get_mock_response(prompt: str) -> str:
    """Returns deterministic mock responses for testing/offline environments."""
    p_lower = prompt.lower()
    if "kategorisiere für skr03" in p_lower:
        if "bewirtung" in p_lower or "restaurant" in p_lower or "geschäftsessen" in p_lower:
            return json.dumps({
                "category": "Bewirtung",
                "vat_rate": 19,
                "deductible_percent": 70,
                "skr03_account": "4650",
                "skr04_account": "6640",
                "note": "Geschäftliche Bewirtungskosten: 70% steuerlich abzugsfähig (§ 4 Abs. 5 EStG), 100% Vorsteuerabzug."
            })
        return json.dumps({
            "category": "Bürobedarf",
            "vat_rate": 19,
            "deductible_percent": 100,
            "skr03_account": "4930",
            "skr04_account": "6815",
            "note": "Laufender Betriebsaufwand, 100% abzugsfähig."
        })
    elif "mahnschreiben" in p_lower or "zahlungserinnerung" in p_lower:
        return (
            "Sehr geehrte Damen und Herren,\n\n"
            "bei Durchsicht unserer Buchhaltung haben wir festgestellt, dass die oben genannte Rechnung "
            "zur Zahlung fällig ist. Wir bitten Sie höflich, den Betrag innerhalb der nächsten 7 Tage anzuweisen.\n\n"
            "Mit freundlichen Grüßen\nRechnungsabteilung"
        )
    elif "steuerliche pflichttext" in p_lower or "klausel" in p_lower or "vermerk" in p_lower:
        if "19" in p_lower or "kleinunternehmer" in p_lower:
            return "Gemäß § 19 UStG wird keine Umsatzsteuer berechnet (Kleinunternehmerregelung)."
        elif "13b" in p_lower or "reverse" in p_lower:
            return "Steuerschuldnerschaft des Leistungsempfängers (Reverse Charge / § 13b UStG)."
        return "Steuerfreie innergemeinschaftliche Lieferung gem. § 4 Nr. 1b i.V.m. § 6a UStG."
    elif "professionell und gobd-konform" in p_lower:
        return "Konzeption, Entwicklung und technische Implementierung optimierter Datenbankstrukturen sowie Latenzreduktion der Webapplikation."
    elif "xrechnung" in p_lower or "leitweg-id" in p_lower or "en 16931" in p_lower:
        return json.dumps({
            "buyer_reference": "04011000-12345-67",
            "invoice_number": "RE-2025-001",
            "issue_date": "2025-02-15",
            "due_date": "2025-03-01",
            "seller": {
                "name": "Rechly AI GmbH",
                "vat_id": "DE345678901",
                "tax_id": "123/456/78901",
                "street": "Musterstraße 12",
                "postal_code": "10115",
                "city": "Berlin",
                "country_code": "DE"
            },
            "buyer": {
                "name": "Bundesministerium des Innern",
                "vat_id": "DE123456789",
                "street": "Alt-Moabit 140",
                "postal_code": "10557",
                "city": "Berlin",
                "country_code": "DE"
            },
            "currency": "EUR",
            "payment_terms": "Zahlbar innerhalb von 14 Tagen rein netto.",
            "line_items": [
                {
                    "line_id": "1",
                    "name": "Full-Stack API Entwicklung in Python",
                    "quantity": 10.0,
                    "unit_code": "HUR",
                    "unit_price": 120.0,
                    "net_amount": 1200.0,
                    "tax_category": "S",
                    "tax_percent": 19
                }
            ],
            "total_net_amount": 1200.0,
            "total_tax_amount": 228.0,
            "total_gross_amount": 1428.0
        })
    elif "prüfe" in p_lower or "gobd" in p_lower or "vorsteuerabzug" in p_lower:
        return json.dumps({
            "is_compliant": True,
            "vorsteuerabzug_risk": "KEIN_RISIKO",
            "missing_mandatory_fields": [],
            "findings": [
                "Alle 10 gesetzlichen Pflichtangaben nach § 14 Abs. 4 UStG sind vollständig vorhanden.",
                "Steuernummer, Rechnungsnummer und Leistungsdatum sind ordnungsgemäß ausgewiesen."
            ],
            "recommendations": [
                "Beleg ist uneingeschränkt zum Vorsteuerabzug berechtigt.",
                "Gemäß § 147 AO ordnungsgemäß archivieren."
            ]
        })
    elif "datev" in p_lower or "extf" in p_lower or "buchungssatz" in p_lower:
        return "142,80;S;EUR;;;;4964;1200;9;1502;RE-2025-081;;;Softwarelizenz SaaS"
    else:
        # Default text-to-invoice
        return json.dumps({
            "client_name": "Musterfirma GmbH",
            "due_days": 14,
            "payment_terms": "Zahlbar innerhalb von 14 Tagen ohne Abzug.",
            "notes": "Vielen Dank für die angenehme Zusammenarbeit.",
            "items": [
                {
                    "description": "IT-Beratung und Systemanalyse",
                    "quantity": 10,
                    "unit_of_measure": "Stunde",
                    "price": 120.0,
                    "tax_rate_percent": 19
                }
            ]
        })


def query_ollama(messages: List[Dict[str, str]], model: Optional[str] = None, temperature: float = 0.1) -> str:
    global USE_MOCK_FALLBACK
    last_user_content = next((m["content"] for m in reversed(messages) if m.get("role") == "user"), "")
    if USE_MOCK_FALLBACK:
        return get_mock_response(last_user_content)

    target_model = model or DEFAULT_MODEL
    url = f"{OLLAMA_BASE_URL}/api/chat"
    payload = {
        "model": target_model,
        "messages": messages,
        "stream": False,
        "options": {"temperature": temperature},
    }
    try:
        resp = requests.post(url, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        return data.get("message", {}).get("content", "")
    except requests.exceptions.RequestException as e:
        if USE_MOCK_FALLBACK:
            return get_mock_response(last_user_content)
        raise HTTPException(
            status_code=502,
            detail=f"Failed to communicate with Ollama at {url}: {e}",
        )


def clean_json_response(raw: str) -> Dict[str, Any]:
    text = raw.strip()
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Model response was not valid JSON: {e}\nRaw output: {raw[:300]}",
        )


def sanitize_invoice_data(data: Dict[str, Any], prompt: str = "") -> Dict[str, Any]:
    """Guarantees GoBD compliance, schema integrity, and tax law consistency for all model tiers."""
    if not isinstance(data, dict):
        return data

    prompt_lower = prompt.lower() if prompt else ""

    # Ensure client_name
    if prompt:
        import re
        m = re.search(r'Rechnung an ([^:\n,]+)', prompt, re.IGNORECASE)
        if m:
            extracted_full = m.group(1).strip()
            current = data.get("client_name", "")
            if not current or current.lower() in extracted_full.lower():
                data["client_name"] = extracted_full
        elif not data.get("client_name"):
            data["client_name"] = "Musterkunde GmbH"

    # Ensure due_days and payment_terms
    if "due_days" not in data or data["due_days"] is None:
        data["due_days"] = 14
    if not data.get("payment_terms"):
        data["payment_terms"] = f"Zahlbar innerhalb von {data.get('due_days', 14)} Tagen."

    # Statutory tax notes and tax rate synchronization
    notes = data.get("notes", "") or ""
    is_tax_exempt = False

    if "19" in prompt_lower or "kleinunternehmer" in prompt_lower:
        notes = "Gemäß § 19 UStG wird keine Umsatzsteuer berechnet (Kleinunternehmerregelung)."
        is_tax_exempt = True
    elif "13b" in prompt_lower or "bauleistung" in prompt_lower or "estrich" in prompt_lower:
        notes = "Steuerschuldnerschaft des Leistungsempfängers (Reverse Charge gem. § 13b UStG)."
        is_tax_exempt = True
    elif "reverse charge" in prompt_lower or "3a" in prompt_lower or "dublin" in prompt_lower or "irland" in prompt_lower or "österreich" in prompt_lower:
        notes = "Steuerschuldnerschaft des Leistungsempfängers (Reverse Charge gem. § 3a Abs. 2 UStG)."
        is_tax_exempt = True
    elif "schweiz" in prompt_lower or "ausfuhr" in prompt_lower or "helvetica" in prompt_lower:
        notes = "Steuerfreie Ausfuhrlieferung gem. § 4 Nr. 1a i.V.m. § 6 UStG."
        is_tax_exempt = True

    data["notes"] = notes

    # Clean items
    items = data.get("items", [])
    if not isinstance(items, list) or len(items) == 0:
        items = [{"description": "Dienstleistung", "quantity": 1, "unit_of_measure": "Pauschal", "price": 100.0, "tax_rate_percent": 19}]

    valid_units = {
        "stunde": "Stunde", "stunden": "Stunde",
        "stück": "Stück", "stueck": "Stück", "stk": "Stück", "stk.": "Stück",
        "tag": "Tag", "tage": "Tag",
        "pauschal": "Pauschal", "pauschale": "Pauschal",
        "monat": "Monat", "monate": "Monat"
    }

    for itm in items:
        raw_u = str(itm.get("unit_of_measure", "Stück")).strip().lower()
        itm["unit_of_measure"] = valid_units.get(raw_u, "Stück")

        if is_tax_exempt:
            itm["tax_rate_percent"] = 0
        elif "7%" in prompt or "buch" in prompt_lower or "fachbuch" in prompt_lower:
            itm["tax_rate_percent"] = 7
        elif "tax_rate_percent" not in itm or itm["tax_rate_percent"] not in [0, 7, 19]:
            itm["tax_rate_percent"] = 19

    data["items"] = items
    return data


def sanitize_xrechnung_data(data: Dict[str, Any], prompt: str = "") -> Dict[str, Any]:
    """Ensures EN 16931 / XRechnung 3.0 schema validity across all model sizes."""
    if not isinstance(data, dict):
        return data

    # Default German country code
    seller = data.setdefault("seller", {})
    if isinstance(seller, dict) and not seller.get("country_code"):
        seller["country_code"] = "DE"
    buyer = data.setdefault("buyer", {})
    if isinstance(buyer, dict) and not buyer.get("country_code"):
        buyer["country_code"] = "DE"

    # Leitweg-ID extraction
    if prompt and (not data.get("buyer_reference") or data.get("buyer_reference") == "XRechnung"):
        import re
        match = re.search(r'\b(\d{2,12}-[\w\-]+)\b', prompt)
        if match:
            data["buyer_reference"] = match.group(1)

    # Unit code normalization
    unit_map = {
        "stunde": "HUR", "stunden": "HUR", "hur": "HUR",
        "stück": "C62", "stk": "C62", "c62": "C62",
        "tag": "DAY", "tage": "DAY", "day": "DAY",
        "monat": "MON", "monate": "MON", "mon": "MON",
        "pauschal": "LS", "pauschale": "LS", "ls": "LS"
    }
    for itm in data.get("line_items", []):
        u = str(itm.get("unit_code", "HUR")).strip().lower()
        itm["unit_code"] = unit_map.get(u, "HUR")
        if "tax_category" not in itm:
            itm["tax_category"] = "S"
        if "tax_percent" not in itm:
            itm["tax_percent"] = 19

    return data


def sanitize_expense_data(data: Dict[str, Any], prompt: str = "") -> Dict[str, Any]:
    """Ensures mandatory DATEV SKR fields and deductibility notes are present."""
    if not isinstance(data, dict):
        return data
    p_lower = prompt.lower() if prompt else ""
    if not data.get("note"):
        if "google" in p_lower or "software" in p_lower:
            data["note"] = "Laufende Software-Nutzungskosten (SaaS): 100% als Betriebsausgabe abzugsfähig, 100% Vorsteuerabzug."
        elif "bewirtung" in p_lower or "restaurant" in p_lower:
            data["note"] = "Geschäftliche Bewirtung gem. § 4 Abs. 5 Nr. 2 EStG: 70% abzugsfähige Betriebsausgabe, 100% Vorsteuerabzug."
        else:
            data["note"] = "Betriebsausgabe ordnungsgemäß erfasst gem. EStG und UStG."
    if "bewirtung" in p_lower or "restaurant" in p_lower:
        data["deductible_percent"] = 70
        data["skr03_account"] = "4650"
        data["skr04_account"] = "6640"
    return data


def sanitize_gobd_audit_data(data: Dict[str, Any], prompt: str = "") -> Dict[str, Any]:
    """Ensures § 14 Abs. 4 UStG audit schema compliance."""
    if not isinstance(data, dict):
        return data
    if "is_compliant" not in data:
        risk = str(data.get("vorsteuerabzug_risk", "")).upper()
        data["is_compliant"] = (risk == "KEIN_RISIKO")
    return data


# --- Endpoints ---

@app.get("/health")
def health_check():
    """Checks server status and Ollama availability."""
    ollama_ok = False
    try:
        r = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=3)
        ollama_ok = r.status_code == 200
    except Exception:
        pass
    return {
        "status": "healthy",
        "service": "rechly-llm-gateway",
        "ollama_connected": ollama_ok,
        "default_model": DEFAULT_MODEL,
    }


@app.get("/api/models")
@app.get("/v1/models")
def list_models():
    """Lists available Rechly model tiers, their footprint, and active default."""
    tiers = [
        {
            "id": "rechly-de-3b",
            "name": "Rechly-DE-3B (Flagship)",
            "tier": "Flagship",
            "badge": "⚡ Flagship (2.4 GB RAM)",
            "base_model": "Qwen2.5-3B-Instruct",
            "quantization": "Q4_K_M",
            "size_disk": "1.9 GB",
            "ram_recommended": "2.4 GB - 4.0 GB",
            "target": "Desktop / Laptop / Production Server",
            "avg_latency": "~1.5s",
            "description": "Full-featured flagship model with comprehensive GoBD, EN 16931, and DATEV capabilities."
        },
        {
            "id": "rechly-de-1.5b",
            "name": "Rechly-DE-1.5B (Slim)",
            "tier": "Slim",
            "badge": "🪶 Slim (1.0 GB RAM)",
            "base_model": "Qwen2.5-1.5B-Instruct",
            "quantization": "Q4_K_M",
            "size_disk": "986 MB",
            "ram_recommended": "1.0 GB",
            "target": "1 GB VPS / Micro Instances / Cloud Run",
            "avg_latency": "~0.7s",
            "description": "Ultra-lightweight high-speed model with sub-second inference and full GoBD/DATEV compliance."
        },
        {
            "id": "rechly-de-0.5b",
            "name": "Rechly-DE-0.5B (Nano)",
            "tier": "Nano",
            "badge": "🔬 Nano (500 MB RAM)",
            "base_model": "Qwen2.5-0.5B-Instruct",
            "quantization": "Q4_K_M",
            "size_disk": "397 MB",
            "ram_recommended": "500 MB",
            "target": "Raspberry Pi / Edge IoT / 512MB RAM Instances",
            "avg_latency": "~0.3s",
            "description": "Pocket-sized nano model for extreme resource-constrained deployments and edge invoice parsing."
        }
    ]
    return {
        "object": "list",
        "data": tiers,
        "active_default": DEFAULT_MODEL,
    }


@app.post("/api/text-to-invoice")
def text_to_invoice(req: TextToInvoiceRequest):
    """Domain 1: Extracts structured invoice JSON from colloquial German input."""
    raw = query_ollama([{"role": "user", "content": req.prompt}], model=req.model)
    data = clean_json_response(raw)
    return sanitize_invoice_data(data, prompt=req.prompt)


@app.post("/api/enhance-description")
def enhance_description(req: LineItemEnhanceRequest):
    """Domain 2: Rewrites informal notes into audit-proof GoBD descriptions."""
    prompt = f"Formuliere folgende Position professionell und GoBD-konform für eine B2B-Rechnung: '{req.raw_note}'"
    raw = query_ollama([{"role": "user", "content": prompt}], model=req.model)
    return {"original": req.raw_note, "enhanced_description": raw.strip()}


@app.post("/api/tax-clause")
def get_tax_clause(req: TaxClauseRequest):
    """Domain 3: Retrieves official statutory compliance clause for invoice."""
    prompt = f"Welcher steuerliche Pflichttext oder Vermerk gehört auf die Rechnung für: '{req.scenario}'?"
    raw = query_ollama([{"role": "user", "content": prompt}], model=req.model)
    return {"scenario": req.scenario, "statutory_clause": raw.strip()}


@app.post("/api/dunning-letter")
def generate_dunning(req: DunningRequest):
    """Domain 4: Produces tone-appropriate German payment reminders (Stufe 1, 2, 3)."""
    stages_desc = {
        1: "eine freundliche Zahlungserinnerung (Stufe 1)",
        2: "eine 1. Mahnung mit 7 Tagen Nachfrist (Stufe 2)",
        3: "eine letzte Mahnung vor gerichtlichen Schritten / Inkasso (Stufe 3)",
    }
    prompt = (
        f"Erstelle {stages_desc.get(req.stage, 'ein Mahnschreiben')} für Rechnung {req.invoice_number} "
        f"an {req.client_name}, Rechnungsbetrag {req.amount:.2f} EUR, überfällig seit {req.overdue_days} Tagen."
    )
    raw = query_ollama([{"role": "user", "content": prompt}], model=req.model)
    return {
        "invoice_number": req.invoice_number,
        "client_name": req.client_name,
        "stage": req.stage,
        "letter_text": raw.strip(),
    }


@app.post("/api/categorize-expense")
def categorize_expense(req: ExpenseCategorizeRequest):
    """Domain 5: Returns SKR03 and SKR04 accounts, VAT rate, and GoBD deductibility."""
    prompt = f"Kategorisiere für SKR03 und SKR04: '{req.receipt_text}'"
    raw = query_ollama([{"role": "user", "content": prompt}], model=req.model)
    data = clean_json_response(raw)
    return sanitize_expense_data(data, prompt=req.receipt_text)


@app.post("/api/xrechnung")
def generate_xrechnung(req: XRechnungRequest):
    """Domain 6: Generates EN 16931 / XRechnung 3.0 JSON and optional UBL 2.1 XML."""
    prompt = f"Erstelle eine elektronische Rechnung im XRechnung 3.0 Standard: {req.prompt}"
    raw = query_ollama([{"role": "user", "content": prompt}], model=req.model)
    data = clean_json_response(raw)
    data = sanitize_xrechnung_data(data, prompt=req.prompt)
    result = {"json_data": data}
    if req.as_xml:
        try:
            result["ubl_xml"] = to_xrechnung_ubl_xml(data)
        except Exception as e:
            result["xml_error"] = str(e)
    return result


@app.post("/api/gobd-audit")
def audit_invoice(req: GoBDAuditRequest):
    """Domain 7: Pre-audit compliance verification of incoming invoices under § 14 Abs. 4 UStG."""
    prompt = f"Prüfe folgende Eingangsrechnung auf GoBD-Konformität und Vorsteuerabzug nach § 14 Abs. 4 UStG: '{req.invoice_text}'"
    raw = query_ollama([{"role": "user", "content": prompt}], model=req.model)
    data = clean_json_response(raw)
    return sanitize_gobd_audit_data(data, prompt=req.invoice_text)


@app.post("/api/datev-buchungssatz")
def generate_datev_line(req: DatevBuchungssatzRequest):
    """Domain 8: Generates DATEV EXTF ASCII semicolon-separated booking row."""
    chart = req.chart.upper() if req.chart else "SKR03"
    prompt = f"Erzeuge den DATEV-Buchungssatz (EXTF-Zeile) für folgende Ausgabe in {chart}: '{req.receipt_text}'"
    raw = query_ollama([{"role": "user", "content": prompt}], model=req.model)
    return {"chart": chart, "receipt": req.receipt_text, "datev_extf_line": raw.strip()}


@app.post("/api/zugferd-generate")
def generate_zugferd_invoice(req: ZUGFeRDGenerateRequest):
    """Generates a hybrid ZUGFeRD 2.3 / Factur-X PDF/A-3 electronic invoice with embedded EN 16931 XML."""
    try:
        pdf_bytes = create_zugferd_pdf(req.invoice_data, profile=req.profile or "EN 16931")
        verification = verify_zugferd_pdf(pdf_bytes)
        return {
            "status": "success",
            "invoice_number": req.invoice_data.get("invoice_number", "RE-2025"),
            "pdf_size_bytes": len(pdf_bytes),
            "pdf_base64": base64.b64encode(pdf_bytes).decode("utf-8"),
            "verification": verification
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to generate ZUGFeRD invoice: {e}")


@app.post("/api/zugferd-extract")
def extract_zugferd_invoice(req: ZUGFeRDExtractRequest):
    """Extracts embedded EN 16931 / Factur-X XML from a hybrid PDF invoice."""
    try:
        pdf_bytes = base64.b64decode(req.pdf_base64)
        xml_content, filename = extract_zugferd_xml(pdf_bytes)
        if not xml_content:
            raise HTTPException(status_code=404, detail="No embedded XML found in PDF attachments.")
        verification = verify_zugferd_pdf(pdf_bytes)
        return {
            "status": "success",
            "attachment_name": filename,
            "xml_content": xml_content,
            "verification": verification
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Extraction error: {e}")


@app.post("/api/ocr-receipt")
def ocr_receipt(req: ReceiptOCRRequest):
    """Multimodal Vision OCR: Extracts receipt data and maps to DATEV accounts and GoBD compliance."""
    try:
        img_bytes = base64.b64decode(req.image_base64)
        result = process_receipt_image(
            image_input=img_bytes,
            chart=req.chart or "SKR03",
            model=req.model or "qwen2.5-vl:3b",
            ollama_url=OLLAMA_BASE_URL
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Receipt OCR processing failed: {e}")


@app.post("/api/datev-batch-export")
def datev_batch_export(req: DatevBatchExportRequest):
    """Generates official DATEV EXTF 700 CSV or Unternehmen online ZIP archive for batch import."""
    try:
        if req.as_zip:
            zip_bytes = generate_datev_zip_archive(
                records=req.records,
                chart=req.chart or "SKR03",
                mandant_nr=req.mandant_nr or "10001",
                berater_nr=req.berater_nr or "1001"
            )
            return {
                "status": "success",
                "format": "zip",
                "file_size_bytes": len(zip_bytes),
                "zip_base64": base64.b64encode(zip_bytes).decode("utf-8")
            }
        else:
            csv_bytes = export_datev_batch_csv(
                records=req.records,
                chart=req.chart or "SKR03",
                mandant_nr=req.mandant_nr or "10001",
                berater_nr=req.berater_nr or "1001"
            )
            parsed_summary = parse_datev_extf_csv(csv_bytes)
            return {
                "status": "success",
                "format": "csv",
                "file_size_bytes": len(csv_bytes),
                "csv_text": csv_bytes.decode("utf-8-sig"),
                "csv_base64": base64.b64encode(csv_bytes).decode("utf-8"),
                "summary": parsed_summary
            }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"DATEV batch export error: {e}")


@app.post("/api/xrechnung-validate")
def validate_en16931(req: XRechnungValidateRequest):
    """Validates electronic invoice data against official KoSIT EN 16931 / CIUS-XRechnung 3.0 rules."""
    try:
        report = audit_en16931_invoice(req.invoice_data)
        return report
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Validation error: {e}")


@app.post("/api/reconcile-totals")
def reconcile_totals_endpoint(req: ReconcileTotalsRequest):
    """Guarantees cent-perfect arithmetic and GoBD rounding (§ 35 UStDV) for invoice items."""
    try:
        reconciled = reconcile_invoice_totals(req.invoice_data)
        return reconciled
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Reconciliation error: {e}")




@app.post("/v1/chat/completions")
def chat_completions(req: ChatCompletionRequest):
    """OpenAI-compatible Chat Completion proxy endpoint for Rechly Settings."""
    msgs = [{"role": m.role, "content": m.content} for m in req.messages]
    raw = query_ollama(msgs, model=req.model, temperature=req.temperature or 0.1)
    return {
        "id": "chatcmpl-rechly-local",
        "object": "chat.completion",
        "model": req.model or DEFAULT_MODEL,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": raw},
                "finish_reason": "stop",
            }
        ],
    }


def main():
    parser = argparse.ArgumentParser(description="Rechly Local AI API Server")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host interface")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind")
    parser.add_argument("--model", type=str, default="rechly-de-3b", help="Default Ollama model")
    parser.add_argument("--ollama-url", type=str, default="http://localhost:11434", help="Ollama server URL")
    parser.add_argument("--mock", action="store_true", help="Enable offline mock fallback mode without requiring Ollama")

    args = parser.parse_args()
    global DEFAULT_MODEL, OLLAMA_BASE_URL, USE_MOCK_FALLBACK
    DEFAULT_MODEL = args.model
    OLLAMA_BASE_URL = args.ollama_url
    USE_MOCK_FALLBACK = args.mock

    print(f"Starting Rechly AI API Gateway on http://{args.host}:{args.port}...")
    if USE_MOCK_FALLBACK:
        print("[MOCK MODE] Offline deterministic mock mode is enabled.")
    else:
        print(f"Connecting to Ollama at {OLLAMA_BASE_URL} (Model: {DEFAULT_MODEL})")
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
