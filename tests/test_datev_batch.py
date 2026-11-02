import pytest
from scripts.datev_batch_exporter import (
    export_datev_batch_csv,
    generate_datev_zip_archive,
    parse_datev_extf_csv,
    calculate_bu_schluessel
)


@pytest.fixture
def sample_batch_records():
    return [
        {
            "merchant_name": "Adobe Systems Cloud",
            "invoice_number": "AD-2025-01",
            "date": "2025-02-10",
            "gross_amount": 59.99,
            "vat_rate": 19.0,
            "skr03_account": "4964",
            "skr04_account": "6837",
            "is_sales": False
        },
        {
            "merchant_name": "Mandant Kanzlei Beratung",
            "invoice_number": "RE-2025-44",
            "date": "2025-02-15",
            "gross_amount": 1785.00,
            "vat_rate": 19.0,
            "konto": "8400",
            "is_sales": True
        },
        {
            "merchant_name": "Deutsche Bahn ICE Ticket",
            "invoice_number": "DB-9901",
            "date": "2025-02-18",
            "gross_amount": 107.00,
            "vat_rate": 7.0,
            "skr03_account": "4673",
            "skr04_account": "6673",
            "is_sales": False
        }
    ]


def test_calculate_bu_schluessel():
    assert calculate_bu_schluessel(19.0, is_sales=False) == "9"
    assert calculate_bu_schluessel(7.0, is_sales=False) == "8"
    assert calculate_bu_schluessel(19.0, is_sales=True) == "3"
    assert calculate_bu_schluessel(7.0, is_sales=True) == "2"
    assert calculate_bu_schluessel(0.0, is_reverse_charge=True) == "94"


def test_export_datev_batch_csv(sample_batch_records):
    csv_bytes = export_datev_batch_csv(sample_batch_records, chart="SKR03")
    assert isinstance(csv_bytes, bytes)
    assert len(csv_bytes) > 200

    parsed = parse_datev_extf_csv(csv_bytes)
    assert parsed["is_valid"] is True
    assert parsed["format_version"] == 700
    assert parsed["total_records"] == 3
    assert abs(parsed["total_volume_eur"] - (59.99 + 1785.00 + 107.00)) < 0.05


def test_generate_datev_zip_archive(sample_batch_records):
    fake_pdf = b"%PDF-1.4 Fake PDF Content"
    zip_bytes = generate_datev_zip_archive(
        sample_batch_records,
        chart="SKR04",
        pdf_attachments={"AD-2025-01.pdf": fake_pdf}
    )
    assert isinstance(zip_bytes, bytes)
    assert len(zip_bytes) > 300

    import zipfile
    import io
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        names = zf.namelist()
        assert "EXTF_Buchungsstapel.csv" in names
        assert "belege/AD-2025-01.pdf" in names
