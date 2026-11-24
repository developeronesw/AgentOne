from app.audit import audit_pages


def sample_page(**overrides):
    page = {
        "url": "https://example.com/", "title": "Example Business", "meta_description": "Description",
        "headings": [{"level": "h1", "text": "Welcome"}], "has_mobile_viewport": True,
        "internal_links": ["https://example.com/contact"], "emails": ["info@example.com"],
        "phones": [], "json_ld": [{"@type": "Organization"}], "text": "Example", "last_modified": None,
    }
    page.update(overrides)
    return page


def test_audit_healthy_sample_reports_passes():
    result = audit_pages([sample_page()])
    assert result["score"] == 100
    assert result["pages_analyzed"] == 1
    assert all(check["status"] == "pass" for check in result["checks"])


def test_audit_missing_tags_reports_warnings_not_crash():
    result = audit_pages([sample_page(title=None, meta_description=None, headings=[], has_mobile_viewport=False,
                                     internal_links=[], emails=[], json_ld=[])])
    keys = {check["key"] for check in result["checks"] if check["status"] == "warning"}
    assert {"title", "description", "h1", "viewport", "navigation", "schema"}.issubset(keys)
    assert result["score"] is not None and result["score"] < 100


def test_audit_empty_crawl_has_no_fake_score():
    result = audit_pages([])
    assert result["score"] is None
    assert result["checks"] == []
    assert "No pages" in result["summary"]


def test_audit_http_is_flagged():
    result = audit_pages([sample_page(url="http://example.com/")])
    https = next(check for check in result["checks"] if check["key"] == "https")
    assert https["status"] == "warning"
