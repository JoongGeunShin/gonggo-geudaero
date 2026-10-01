import json
from pathlib import Path

import httpx
import pytest
import respx

from app.config import settings
from app.external.nts import NTS_URL, get_business_status

FIXTURE = json.loads((Path(__file__).parent / "fixtures" / "nts_status_ok.json").read_text(encoding="utf-8"))


@pytest.fixture
def with_key(monkeypatch):
    monkeypatch.setattr(settings, "nts_service_key", "test-key")


@respx.mock
def test_returns_first_record(with_key):
    respx.post(NTS_URL).mock(return_value=httpx.Response(200, json=FIXTURE))
    result = get_business_status("1234567890")
    assert result["b_stt_cd"] == "01"
    assert result["b_stt"] == "계속사업자"


@respx.mock
def test_sends_key_and_number_without_hyphens(with_key):
    route = respx.post(NTS_URL).mock(return_value=httpx.Response(200, json=FIXTURE))
    get_business_status("123-45-67890")
    request = route.calls.last.request
    assert request.url.params["serviceKey"] == "test-key"
    assert json.loads(request.content) == {"b_no": ["1234567890"]}


@respx.mock
def test_server_error_returns_none(with_key):
    respx.post(NTS_URL).mock(return_value=httpx.Response(500))
    assert get_business_status("1234567890") is None


@respx.mock
def test_timeout_returns_none(with_key):
    respx.post(NTS_URL).mock(side_effect=httpx.ConnectTimeout("timeout"))
    assert get_business_status("1234567890") is None


@respx.mock
def test_empty_data_returns_none(with_key):
    respx.post(NTS_URL).mock(return_value=httpx.Response(200, json={"status_code": "OK", "data": []}))
    assert get_business_status("1234567890") is None


@pytest.mark.parametrize("b_no", ["123456789", "12345678901", "123-45-6789a", ""])
def test_invalid_number_raises(b_no):
    with pytest.raises(ValueError):
        get_business_status(b_no)


@respx.mock
def test_missing_key_returns_none_without_calling(monkeypatch):
    monkeypatch.setattr(settings, "nts_service_key", "")
    route = respx.post(NTS_URL)
    assert get_business_status("1234567890") is None
    assert not route.called
