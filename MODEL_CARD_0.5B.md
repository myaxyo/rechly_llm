---
language:
- de
- en
license: apache-2.0
base_model: Qwen/Qwen2.5-0.5B-Instruct
tags:
- e-rechnung
- xrechnung
- zugferd
- factur-x
- en16931
- datev
- skr03
- skr04
- gobd
- ustg
- accounting
- finance
- tax
- invoice
- text-to-invoice
- german
- qwen2.5
- gguf
- ollama
- dsgvo
- gdpr
model_name: Rechly-DE-0.5B
pipeline_tag: text-generation
inference: false
---

<div align="center">

# 🇩🇪 Rechly-DE-0.5B (Nano): Ultra-Lightweight German Accounting AI for Edge & 500 MB RAM

[![Hugging Face](https://img.shields.io/badge/Hugging%20Face-jonprompter%2Frechly--de--0.5b-yellow?style=for-the-badge&logo=huggingface&logoColor=white)](https://huggingface.co/jonprompter/rechly-de-0.5b)
[![GitHub](https://img.shields.io/badge/GitHub-myaxyo%2Frechly__llm-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/myaxyo/rechly_llm)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue?style=for-the-badge)](LICENSE)
[![DSGVO Compliance](https://img.shields.io/badge/DSGVO%20%2F%20GDPR-100%25%20Local%20(Zero%20Egress)-success?style=for-the-badge)](#-dsgvo--data-privacy-guarantee)

**The pocket-sized 0.5-Billion parameter Nano Language Model for German Invoicing, the 2025/2026 E-Rechnung Mandate (EN 16931, XRechnung 3.0), and DATEV SKR03/04 Bookkeeping.**

*Runs 100% on-device inside **~500 MB RAM** on Raspberry Pi 4/5, budget 512MB RAM instances, or edge IoT appliances with near-instantaneous 0.3s response times.*

</div>

---

### 🏛️ The Rechly Model Family
- ⚡ **[Rechly-DE-3B (Flagship)](https://huggingface.co/jonprompter/rechly-de-3b)** — 3B params · 1.84 GB · Desktop & Production Server
- 🪶 **[Rechly-DE-1.5B (Slim)](https://huggingface.co/jonprompter/rechly-de-1.5b)** — 1.5B params · 940 MB · 1 GB VPS & Cloud Run
- 🔬 **[Rechly-DE-0.5B (Nano)](https://huggingface.co/jonprompter/rechly-de-0.5b)** — 0.5B params · 379 MB · Raspberry Pi & 512MB RAM

---

## ⚡ 10-Second Quickstart

### 1. Run with Ollama:
```bash
# Clone and build local Ollama model
huggingface-cli download jonprompter/rechly-de-0.5b rechly-de-0.5b-q4_k_m.gguf Modelfile --local-dir .
ollama create rechly-de-0.5b -f Modelfile
ollama run rechly-de-0.5b
```

### 2. Test an invoice in one line:
```bash
ollama run rechly-de-0.5b "Rechnung an Blumenladen Rose: 5 Stunden Schaufensterdeko à 55€, Kleinunternehmer ohne USt."
```

### 3. Python 4-Liner:
```python
import requests

resp = requests.post("http://localhost:11434/api/chat", json={
    "model": "rechly-de-0.5b",
    "messages": [{"role": "user", "content": "Kategorisiere für SKR03: 'Google Workspace Cloud monatlich 72€'"}],
    "stream": False,
    "options": {"temperature": 0.0}
})
print(resp.json()["message"]["content"])
```

---

## ⚡ Specifications

| Parameter | Specification |
| :--- | :--- |
| **Base Architecture** | `Qwen/Qwen2.5-0.5B-Instruct` (Apache 2.0 open-weights) |
| **Quantization** | GGUF `Q4_K_M` (~379 MB file size) |
| **RAM Footprint** | **~500 MB RAM** (Runs comfortably on Raspberry Pi, 512MB RAM devices, Edge IoT) |
| **Inference Speed** | **180+ tokens/sec** / **0.3s per query** |
| **Zero-Footprint Guarantee** | Hybrid ZUGFeRD 2.3 PDF/A-3, DATEV EXTF 700 Batch Exporter, and Cent-Perfect Reconciler run deterministically in Python with 0 MB LLM memory overhead |

---

## 🎯 Supported Accounting Domains

1. **Edge Text-to-Invoice Extraction**: Fast extraction of client name, prices, quantities, and due dates.
2. **DATEV Account Matching**: Quick lookups for SKR03 and SKR04 chart accounts.
3. **GoBD Pre-Auditing**: Edge validation of incoming supplier receipts.
4. **B2B Position Text Formalizer**: Rewrites colloquial notes into standard invoice descriptions.

---

## 🔒 License & Open Source

Licensed under the **Apache 2.0 License**. Built by the [Rechly](https://rechly.de) team for privacy-first, on-premise German accounting.
