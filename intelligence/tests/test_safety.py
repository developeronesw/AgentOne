import pytest
from app.safety import normalize_url, safe_target

@pytest.mark.parametrize("url",["ftp://example.com","http://localhost","http://user:pass@example.com","http://example.com:8088"])
def test_invalid_url_rejected_by_normalizer(url):
    with pytest.raises(ValueError): normalize_url(url)

def test_local_ip_is_blocked_by_target_validator():
    with pytest.raises(ValueError): safe_target("http://127.0.0.1")

def test_fragment_removed():
    assert normalize_url("https://EXAMPLE.com/a#b")=="https://example.com/a"
