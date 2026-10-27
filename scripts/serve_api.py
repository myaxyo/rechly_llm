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


@app.post("/api/text-to-invoice")
def text_to_invoice(req: TextToInvoiceRequest):
    """Domain 1: Extracts structured invoice JSON from colloquial German input."""
    raw = query_ollama([{"role": "user", "content": req.prompt}], model=req.model)
    return clean_json_response(raw)


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
    return clean_json_response(raw)


@app.post("/api/xrechnung")
def generate_xrechnung(req: XRechnungRequest):
    """Domain 6: Generates EN 16931 / XRechnung 3.0 JSON and optional UBL 2.1 XML."""
    prompt = f"Erstelle eine elektronische Rechnung im XRechnung 3.0 Standard: {req.prompt}"
    raw = query_ollama([{"role": "user", "content": prompt}], model=req.model)
    data = clean_json_response(raw)
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
    return clean_json_response(raw)


@app.post("/api/datev-buchungssatz")
def generate_datev_line(req: DatevBuchungssatzRequest):
    """Domain 8: Generates DATEV EXTF ASCII semicolon-separated booking row."""
    chart = req.chart.upper() if req.chart else "SKR03"
    prompt = f"Erzeuge den DATEV-Buchungssatz (EXTF-Zeile) für folgende Ausgabe in {chart}: '{req.receipt_text}'"
    raw = query_ollama([{"role": "user", "content": prompt}], model=req.model)
    return {"chart": chart, "receipt": req.receipt_text, "datev_extf_line": raw.strip()}


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
