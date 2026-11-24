"""Build an evidence-backed business profile from deterministic crawl observations."""
from __future__ import annotations
from collections import Counter
from urllib.parse import urlparse
from .extractor import categorize


CATEGORY_LABELS = {
    "web development": "Web development & design", "marketing": "Marketing", "consulting": "Consulting",
    "ecommerce": "E-commerce", "software": "Software & technology", "construction": "Construction & home services",
    "hospitality": "Hospitality", "healthcare": "Healthcare", "real estate": "Real estate",
    "education": "Education & training", "finance": "Finance", "retail": "Retail",
    "manufacturing": "Manufacturing", "logistics": "Logistics & transportation",
}

def build_profile(start_url: str, pages: list[dict]) -> dict:
    if not pages:
        return {"website": start_url, "status": "insufficient_data", "pages_analyzed": 0,
                "business_name": None, "business_description": None, "categories": [],
                "services_observed": [], "pricing_observations": [], "contact_observations": {},
                "location_observations": [], "social_profiles": [], "confidence": "low",
                "evidence_pages": []}
    host = urlparse(start_url).hostname or ""
    homepage = pages[0]
    texts = [p.get("text", "") for p in pages]
    combined = " ".join(texts)
    category_signals = categorize(combined)
    categories = [{"name": CATEGORY_LABELS.get(c["category"], c["category"]), "signal_key": c["category"],
                  "matched_terms": c["matched_terms"], "evidence_urls": [p["url"] for p in pages if any(t in p.get("text", "").lower() for t in c["matched_terms"]] )}
                 for c in category_signals]
    title = homepage.get("title") or ""
    business_name = None
    # Prefer common Schema.org organization/business types.
    def walk_jsonld(value):
        if isinstance(value, dict):
            typ = value.get("@type", "")
            if isinstance(typ, list): typ = " ".join(typ)
            if any(x in str(typ).lower() for x in ("organization", "localbusiness", "professionalservice")) and value.get("name"):
                yield value
            for child in value.values(): yield from walk_jsonld(child)
        elif isinstance(value, list):
            for child in value: yield from walk_jsonld(child)
    for page in pages:
        for data in page.get("json_ld", []):
            for obj in walk_jsonld(data):
                if obj.get("name"):
                    business_name = str(obj["name"])[:200]
                    break
            if business_name: break
        if business_name: break
    if not business_name:
        business_name = title.split("|")[0].split("—")[0].split("-")[0].strip() or None
    desc = homepage.get("meta_description")
    service_counts = Counter()
    service_evidence = {}
    for cat in categories:
        for term in cat["matched_terms"]:
            service_counts[term] += 1
            service_evidence[term] = sorted(set(service_evidence.get(term, []) + cat["evidence_urls"]))
    prices = sorted({price for p in pages for price in p.get("price_mentions", [])})[:50]
    emails = sorted({email for p in pages for email in p.get("emails", [])})
    phones = sorted({phone for p in pages for phone in p.get("phones", [])})
    socials = sorted({link for p in pages for link in p.get("external_links", []) if any(domain in link.lower() for domain in ("facebook.com", "instagram.com", "linkedin.com", "youtube.com", "tiktok.com", "x.com", "twitter.com"))})
    locations = sorted({text for p in pages for text in p.get("location_observations", [])})
    return {
        "website": start_url, "status": "observed", "pages_analyzed": len(pages),
        "business_name": business_name, "business_description": desc,
        "categories": categories,
        "services_observed": [{"term": t, "evidence_urls": service_evidence[t]} for t in sorted(service_counts)],
        "pricing_observations": prices, "contact_observations": {"emails": emails, "phones": phones},
        "location_observations": locations, "social_profiles": socials,
        "confidence": "medium" if len(pages) >= 3 else "low",
        "evidence_pages": [{"url": p["url"], "title": p.get("title"), "excerpt": p.get("text", "")[:350]} for p in pages]
    }
