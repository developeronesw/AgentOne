from app.profiler import build_profile

def test_empty_profile_is_explicitly_insufficient():
    result = build_profile("https://example.com", [])
    assert result["status"] == "insufficient_data"
    assert result["business_name"] is None

def test_profile_extracts_signals_and_evidence():
    pages = [{"url":"https://sample.com/","title":"Sample Studio - Web Design",
              "meta_description":"Website design services for small businesses",
              "text":"We offer website design, web development, SEO and marketing services.",
              "emails":["hello@sample.com"],"phones":[],"price_mentions":["$250"],"json_ld":[],
              "external_links":["https://instagram.com/sample"],"location_observations":[]},
             {"url":"https://sample.com/services","title":"Services","text":"SEO and website development services.",
              "emails":[],"phones":[],"price_mentions":[],"json_ld":[],"external_links":[],"location_observations":[]}]
    result = build_profile("https://sample.com", pages)
    assert result["status"] == "observed"
    assert result["business_name"]
    assert any("web development" == c["signal_key"] for c in result["categories"])
    assert "hello@sample.com" in result["contact_observations"]["emails"]
    assert result["pricing_observations"] == ["$250"]
    assert result["social_profiles"] == ["https://instagram.com/sample"]
