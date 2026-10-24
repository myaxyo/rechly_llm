import json
import threading
from contextlib import contextmanager
import requests
import pytest
import serve_demo as demo
from jsonschema import ValidationError

@contextmanager
def running_server():
    server = demo.create_server(port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f'http://127.0.0.1:{server.server_port}'
    finally:
        server.shutdown()
        server.server_close()
        thread.join()

def test_demo_http_and_schema_gate(monkeypatch):
    with running_server() as url:
        assert requests.get(url, timeout=5).status_code == 200
        example = requests.get(url + '/api/example', timeout=5).json()
        assert example['source'] == 'seed_fixture'
        assert example['totals']['gross_eur']
        monkeypatch.setattr(demo, 'query_model', lambda *_: json.dumps(example['draft']))
        response = requests.post(url + '/api/invoice', json={'prompt': example['prompt']}, timeout=5)
        assert response.status_code == 200
        assert response.json()['draft'] == example['draft']
        monkeypatch.setattr(demo, 'query_model', lambda *_: '{}')
        assert requests.post(url + '/api/invoice', json={'prompt': 'test'}, timeout=5).status_code == 502
        assert requests.post(url + '/api/invoice', json={'prompt': ''}, timeout=5).status_code == 400
        assert requests.post(url + '/api/invoice', json=[], timeout=5).status_code == 400
        assert requests.post(url + '/api/invoice', json={'prompt': 'test'}, headers={'Origin': 'http://evil.example'}, timeout=5).status_code == 403
        def unavailable(*_):
            raise ConnectionError('private details')
        monkeypatch.setattr(demo, 'query_model', unavailable)
        response = requests.post(url + '/api/invoice', json={'prompt': 'test'}, timeout=5)
        assert response.status_code == 503
        assert 'private details' not in response.text

def test_decimal_totals():
    invoice = {'items': [{'quantity': 3, 'price': 0.1, 'tax_rate_percent': 19},
                         {'quantity': 1, 'price': 100, 'tax_rate_percent': 7}]}
    assert demo.invoice_totals(invoice) == {'net_eur': '100.30', 'vat_eur': '7.06', 'gross_eur': '107.36'}
