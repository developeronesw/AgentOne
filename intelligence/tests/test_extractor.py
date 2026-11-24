from app.extractor import parse_page,categorize
def test_html_extracts_basics():
    html="<html><head><title>Sample</title><meta name='description' content='desc'><meta name='viewport'></head><body><h1>Web Design</h1><p>Contact hello@example.com $125</p><a href='/about'>About</a></body></html>"
    p=parse_page("https://example.com",html)
    assert p["title"]=="Sample" and p["has_mobile_viewport"]
    assert "hello@example.com" in p["emails"] and "$125" in p["price_mentions"]
    assert any("/about" in x for x in p["internal_links"])
def test_category_signal():
    assert any(x["category"]=="web development" for x in categorize("website design and web development"))
