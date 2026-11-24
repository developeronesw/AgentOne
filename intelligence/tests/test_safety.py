import pytest
from app.safety import normalize_url
@pytest.mark.parametrize("url",["ftp://example.com","http://localhost","http://127.0.0.1","http://user:pass@example.com","http://example.com:8088"])
def test_invalid_url_rejected(url):
    with pytest.raises(ValueError): normalize_url(url)
def test_fragment_removed():
    assert normalize_url("https://EXAMPLE.com/a#b")=="https://example.com/a"
