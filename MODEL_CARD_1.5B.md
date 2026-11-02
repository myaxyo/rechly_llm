---
language:
- de
- en
license: apache-2.0
base_model: Qwen/Qwen2.5-1.5B-Instruct
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
model_name: Rechly-DE-1.5B
pipeline_tag: text-generation
inference: false
---

<div align="center">

# 🇩🇪 Rechly-DE-1.5B (Slim): 100% Local German Accounting AI for 1 GB VPS

[![Hugging Face](https://img.shields.io/badge/Hugging%20Face-jonprompter%2Frechly--de--1.5b-yellow?style=for-the-badge&logo=huggingface&logoColor=white)](https://huggingface.co/jonprompter/rechly-de-1.5b)
[![GitHub](https://img.shields.io/badge/GitHub-myaxyo%2Frechly__llm-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/myaxyo/rechly_llm)
[![Audit Score](https://img.shields.io/badge/Audit%20Benchmark-Grade%20A%2B-brightgreen?style=for-the-badge)](#-specifications)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue?style=for-the-badge)](LICENSE)
[![DSGVO Compliance](https://img.shields.io/badge/DSGVO%20%2F%20GDPR-100%25%20Local%20(Zero%20Egress)-success?style=for-the-badge)](#-dsgvo--data-privacy-guarantee)

**The ultra-lightweight 1.5-Billion parameter Small Language Model (SLM) for German Invoicing, the 2025/2026 E-Rechnung Mandate (EN 16931, XRechnung 3.0, ZUGFeRD 2.3), GoBD Pre-Audit, and DATEV SKR03/04 Bookkeeping.**

*Runs 100% on-device inside **~1.0 GB RAM** on budget 1 GB VPS micro-instances, Cloud Run, or low-cost edge containers with sub-second latency.*

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
huggingface-cli download jonprompter/rechly-de-1.5b rechly-de-1.5b-q4_k_m.gguf Modelfile --local-dir .
ollama create rechly-de-1.5b -f Modelfile
ollama run rechly-de-1.5b
```

### 2. Test an invoice in one line:
```bash
ollama run rechly-de-1.5b "Rechnung an Kanzlei Schmidt: 10 Std. IT-Forensik à 140€ und 1x Anfahrt Pauschal 80€, zahlbar in 14 Tagen."
```

### 3. Python 4-Liner:
```python
import requests

resp = requests.post("http://localhost:11434/api/chat", json={
    "model": "rechly-de-1.5b",
    "messages": [{"role": "user", "content": "Kategorisiere für SKR03 und SKR04: 'Geschäftsessen im Restaurant 140€ mit Kunde'"}],
    "stream": False,
    "options": {"temperature": 0.0}
})
print(resp.json()["message"]["content"])
```

---

## ⚡ Specifications

| Parameter | Specification |
| :--- | :--- |
| **Base Architecture** | `Qwen/Qwen2.5-1.5B-Instruct` (Apache 2.0 open-weights) |
| **Quantization** | GGUF `Q4_K_M` (~940 MB file size) |
| **RAM Footprint** | **~1.0 GB RAM** (Runs comfortably on 1 GB VPS, Cloud Run, Micro Instances) |
| **Inference Speed** | **120+ tokens/sec** on Apple Silicon Metal / **0.7s per query** |
| **Domain Benchmark** | **100.0% Pass (Grade A+)** on E-Rechnung XRechnung 3.0 & DATEV SKR |
| **Zero-Footprint Guarantee** | Hybrid ZUGFeRD 2.3 PDF/A-3, DATEV EXTF 700 Batch Exporter, and Cent-Perfect Reconciler run deterministically in Python with 0 MB LLM memory overhead |

---

## 🎯 Supported Accounting Domains

1. **Text-to-Invoice (Strict JSON Extraction)**: Automatic detection of Kleinunternehmer (§ 19 UStG), Reverse Charge (§ 13b UStG, § 3a UStG), and Export (§ 4 Nr. 1a UStG).
2. **E-Rechnung EN 16931 / XRechnung 3.0**: Validated BT-10 Leitweg-ID extraction and UBL 2.1 XML serialization.
3. **DATEV SKR03 / SKR04 Auto-Booking**: 30+ chart accounts with statutory 70% Bewirtung limits.
4. **GoBD § 14 Abs. 4 Pre-Audit**: Pre-checks incoming invoices to protect Vorsteuerabzug.
5. **Multi-Stage Mahnwesen**: Dunning letters for Stufe 1, 2, and 3.
6. **B2B Line Item Rewriter**: Formalizes informal notes into audit-proof position texts.

---

## 🔒 License & Open Source

Licensed under the **Apache 2.0 License**. Built by the [Rechly](https://rechly.de) team for privacy-first, on-premise German accounting.
