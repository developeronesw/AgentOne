from app.extractor import parse_page,categorize
def test_html_extracts_basics():
    html="<html><head><title>Sample</title><meta name='description' content='desc'><meta name='viewport'></head><body><h1>Web Design</h1><p>Contact hello@example.com $125</p><a href='/about'>About</a></body></html>"
    p=parse_page("https://example.com",html)
    assert p["title"]=="Sample" and p["has_mobile_viewport"]
    assert "hello@example.com" in p["emails"] and "$125" in p["price_mentions"]
    assert any("/about" in x for x in p["internal_links"])
def test_category_signal():
    assert any(x["category"]=="web development" for x in categorize("website design and web development"))


def test_external_social_links_are_separated():
    html = "<html><body><a href='https://instagram.com/example'>Instagram</a><a href='/services'>Services</a></body></html>"
    page = parse_page("https://example.com", html)
    assert "https://instagram.com/example" in page["external_links"]
    assert "https://example.com/services" in page["internal_links"]


def test_malformed_html_still_extracts_basic_content():
    html = "<title>Unclosed page<h1>Services<p>Website development $1,200"
    page = parse_page("https://broken.example", html)
    assert page["title"] == "Unclosed page"
    assert "Website development" in page["text"]
    assert "$1,200" in page["price_mentions"]


def test_json_ld_is_preserved_and_parsed():
    html = '<html><head><script type="application/ld+json">{"@type":"Organization","name":"Demo Co"}</script></head><body><script>not content</script><p>Body text</p></body></html>'
    page = parse_page("https://demo.example", html)
    assert page["json_ld"][0]["name"] == "Demo Co"
    assert "not content" not in page["text"]
