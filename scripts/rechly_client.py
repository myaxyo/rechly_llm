#!/usr/bin/env python3
"""
Rechly AI Python Client SDK.
Turnkey integration helper for Rechly (rechly.de) and Python applications.
Supports calling either the Rechly API Gateway (http://localhost:8000)
or directly the Ollama daemon (http://localhost:11434).

Usage:
    from rechly_client import RechlyClient

    client = RechlyClient()
    invoice = client.text_to_invoice("Rechnung an Muster GmbH: 10 Std. Beratung à 120€")
    print(invoice)
"""

import json
from typing import Dict, Any, Optional
import requests


class RechlyClient:
    """Client for Rechly-DE-3B accounting AI."""

    def __init__(
        self,
        api_base_url: str = "http://localhost:8000",
        ollama_base_url: str = "http://localhost:11434",
        model: str = "rechly-de-3b",
        timeout: int = 60,
    ):
        self.api_base_url = api_base_url.rstrip("/")
        self.ollama_base_url = ollama_base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def is_gateway_available(self) -> bool:
        """Checks if the local Rechly API gateway is accessible."""
        try:
            r = requests.get(f"{self.api_base_url}/health", timeout=2)
            return r.status_code == 200
        except Exception:
            return False

    def is_ollama_available(self) -> bool:
        """Checks if Ollama daemon is accessible."""
        try:
            r = requests.get(f"{self.ollama_base_url}/api/tags", timeout=2)
            return r.status_code == 200
        except Exception:
            return False

    def _call_ollama_direct(self, prompt: str) -> str:
        """Direct query to Ollama when gateway is not active."""
        url = f"{self.ollama_base_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "options": {"temperature": 0.1},
        }
        resp = requests.post(url, json=payload, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json().get("message", {}).get("content", "")

    def _clean_json(self, raw: str) -> Dict[str, Any]:
        text = raw.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        return json.loads(text)

    # --- Core Domain Methods ---

    def text_to_invoice(self, prompt: str) -> Dict[str, Any]:
        """Domain 1: Extracts structured invoice JSON from colloquial German input."""
        if self.is_gateway_available():
            resp = requests.post(
                f"{self.api_base_url}/api/text-to-invoice",
                json={"prompt": prompt, "model": self.model},
                timeout=self.timeout,
            )
            resp.raise_for_status()
            return resp.json()
        raw = self._call_ollama_direct(prompt)
        return self._clean_json(raw)

    def enhance_description(self, raw_note: str) -> str:
        """Domain 2: Rewrites informal notes into audit-proof GoBD B2B descriptions."""
        if self.is_gateway_available():
            resp = requests.post(
                f"{self.api_base_url}/api/enhance-description",
                json={"raw_note": raw_note, "model": self.model},
                timeout=self.timeout,
            )
            resp.raise_for_status()
            return resp.json().get("enhanced_description", "")
        prompt = f"Formuliere folgende Position professionell und GoBD-konform für eine B2B-Rechnung: '{raw_note}'"
        return self._call_ollama_direct(prompt).strip()

    def get_tax_clause(self, scenario: str) -> str:
        """Domain 3: Retrieves official statutory compliance clause for invoice."""
        if self.is_gateway_available():
            resp = requests.post(
                f"{self.api_base_url}/api/tax-clause",
                json={"scenario": scenario, "model": self.model},
                timeout=self.timeout,
            )
            resp.raise_for_status()
            return resp.json().get("statutory_clause", "")
        prompt = f"Welcher steuerliche Pflichttext oder Vermerk gehört auf die Rechnung für: '{scenario}'?"
        return self._call_ollama_direct(prompt).strip()

    def generate_dunning_letter(
        self,
        invoice_number: str,
        client_name: str,
        amount: float,
        overdue_days: int,
        stage: int = 1,
    ) -> str:
        """Domain 4: Produces tone-appropriate German payment reminders (Stufe 1, 2, 3)."""
        if self.is_gateway_available():
            resp = requests.post(
                f"{self.api_base_url}/api/dunning-letter",
                json={
                    "invoice_number": invoice_number,
                    "client_name": client_name,
                    "amount": amount,
                    "overdue_days": overdue_days,
                    "stage": stage,
                    "model": self.model,
                },
                timeout=self.timeout,
            )
            resp.raise_for_status()
            return resp.json().get("letter_text", "")

        stages_desc = {
            1: "eine freundliche Zahlungserinnerung (Stufe 1)",
            2: "eine 1. Mahnung mit 7 Tagen Nachfrist (Stufe 2)",
            3: "eine letzte Mahnung vor gerichtlichen Schritten / Inkasso (Stufe 3)",
        }
        prompt = (
            f"Erstelle {stages_desc.get(stage, 'ein Mahnschreiben')} für Rechnung {invoice_number} "
            f"an {client_name}, Rechnungsbetrag {amount:.2f} EUR, überfällig seit {overdue_days} Tagen."
        )
        return self._call_ollama_direct(prompt).strip()

    def categorize_expense(self, receipt_text: str) -> Dict[str, Any]:
        """Domain 5: Returns SKR03 and SKR04 accounts, VAT rate, and GoBD deductibility."""
        if self.is_gateway_available():
            resp = requests.post(
                f"{self.api_base_url}/api/categorize-expense",
                json={"receipt_text": receipt_text, "model": self.model},
                timeout=self.timeout,
            )
            resp.raise_for_status()
            return resp.json()
        prompt = f"Kategorisiere für SKR03 und SKR04: '{receipt_text}'"
        raw = self._call_ollama_direct(prompt)
        return self._clean_json(raw)
