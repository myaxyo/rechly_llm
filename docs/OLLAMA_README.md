# Short Summary / Description (for Ollama "Edit Summary"):
```text
100% Local, DSGVO-compliant German Accounting AI for GoBD Invoicing, UStG Clauses & DATEV SKR03/SKR04 Bookkeeping.
```

---

# Ollama README Markdown (Copy & Paste below into Ollama Web Editor):

```markdown
# Rechly-DE-3B: 100% Local German Accounting AI Model 🇩🇪

**Rechly-DE-3B** is a specialized, lightweight (3 Billion parameters), privacy-first German accounting language model engineered specifically for **[Rechly](https://rechly.de)** and the German open-source AI ecosystem.

Operating **100% locally** with zero external API calls, Rechly-DE-3B ensures complete **DSGVO / GDPR compliance** for sensitive financial records, invoices, and client data.

---

## ⚡ Specifications

- **Base Architecture**: `Qwen/Qwen2.5-3B-Instruct`
- **Quantization**: GGUF `Q4_K_M` (~1.84 GB)
- **RAM Footprint**: **< 2.5 GB RAM** (Runs comfortably on MacBook Air or 4GB VPS)
- **Inference Speed**: **60–80+ tokens/sec** via Ollama on Apple Silicon Metal
- **Compliance Standards**: German **GoBD**, **UStG** (§ 19 Kleinunternehmer, § 13b Reverse-Charge, Innergemeinschaftlich), **DATEV SKR03 / SKR04**
- **Evaluation Score**: **100% Pass Rate (8/8)** on the official 5-domain GoBD benchmark

---

## 🚀 Quickstart

Run directly in your terminal:
```bash
ollama run jonprompter/Rechly-DE-3B
```

---

## 🎯 5 Core Accounting Capabilities

### 1. Text-to-Invoice (Strict GoBD JSON)
Extracts recipient details, due dates, payment terms, and itemized lines with tax rates into strict JSON:

```bash
ollama run jonprompter/Rechly-DE-3B "Rechnung an Kanzlei Schmidt & Partner: 12 Stunden IT-Beratung à 120€ und 1x Server-Setup Pauschal 250€, zahlbar in 14 Tagen mit 2% Skonto."
```

**Output:**
```json
{
  "client_name": "Kanzlei Schmidt & Partner",
  "due_days": 14,
  "payment_terms": "14 Tage mit 2% Skonto",
  "notes": "",
  "items": [
    {
      "description": "IT-Beratung",
      "quantity": 12,
      "unit_of_measure": "Stunde",
      "price": 120.0,
      "tax_rate_percent": 19
    },
    {
      "description": "Server-Setup",
      "quantity": 1,
      "unit_of_measure": "Pauschal",
      "price": 250.0,
      "tax_rate_percent": 19
    }
  ]
}
```

---

### 2. B2B Line Item Rewriter
Converts raw, informal trade notes into audit-proof, GoBD-compliant service descriptions:

```bash
ollama run jonprompter/Rechly-DE-3B "Formuliere folgende Position professionell und GoBD-konform für eine B2B-Rechnung: 'website schneller gemacht und datenbank geputzt'"
```

**Output:**
> *"Performance-Optimierung der Webpräsenz: Bereinigung und Indexierung relationaler Datenbanktabellen sowie messbare Ladezeitreduktion."*

---

### 3. German Tax & GoBD Statutory Clauses
Generates exact statutory compliance clauses mandated under German tax law:

```bash
ollama run jonprompter/Rechly-DE-3B "Welcher steuerliche Pflichttext gehört auf die Rechnung für Handwerkerleistungen an einen Generalunternehmer?"
```

**Output:**
> *"Steuerschuldnerschaft des Leistungsempfängers (Reverse Charge / § 13b Abs. 2 Nr. 4 i.V.m. Abs. 5 UStG)."*

---

### 4. Mahnwesen (3-Stage Dunning Letters)
Drafts tone-appropriate payment reminders and formal dunning letters:

```bash
ollama run jonprompter/Rechly-DE-3B "Erstelle eine freundliche Zahlungserinnerung für Rechnung RE-2026-0841 an Kreativstudio Alpha über 2.850 EUR, 14 Tage überfällig."
```

---

### 5. DATEV SKR03 / SKR04 Expense Categorization
Maps receipt text to 4-digit DATEV accounting codes with deductibility rules:

```bash
ollama run jonprompter/Rechly-DE-3B "Kategorisiere für SKR03 und SKR04: 'Geschäftsessen mit Neukunden im Restaurant Osteria 180€'"
```

**Output:**
```json
{
  "category": "Bewirtung",
  "vat_rate": 19,
  "deductible_percent": 70,
  "skr03_account": "4650",
  "skr04_account": "6640",
  "note": "Geschäftliche Bewirtungskosten: 70% steuerlich abzugsfähig (§ 4 Abs. 5 EStG), 100% Vorsteuerabzug."
}
```

---

## 🔗 Links & Resources

- **GitHub Repository**: [https://github.com/myaxyo/rechly_llm](https://github.com/myaxyo/rechly_llm)
- **Hugging Face Hub**: [https://huggingface.co/jonprompter/rechly-de-3b](https://huggingface.co/jonprompter/rechly-de-3b)
- **Official Product**: [Rechly Invoicing](https://rechly.de)
- **License**: Apache 2.0
```
