"""Build conservative, evidence-backed business profiles from crawl observations.

This module never treats a missing observation as proof that information does not exist.
"""
from __future__ import annotations

from urllib.parse import urlparse
from .extractor import categorize

CATEGORY_LABELS = {
    "web development": "Web development & design",
    "marketing": "Marketing",
    "consulting": "Consulting",
    "ecommerce": "E-commerce",
    "software": "Software & technology",
    "construction": "Construction & home services",
    "hospitality": "Hospitality",
    "healthcare": "Healthcare",
    "real estate": "Real estate",
    "education": "Education & training",
    "finance": "Finance",
    "retail": "Retail",
    "manufacturing": "Manufacturing",
    "logistics": "Logistics & transportation",
}
SOCIAL_DOMAINS = (
    "facebook.com", "instagram.com", "linkedin.com", "youtube.com",
    "tiktok.com", "x.com", "twitter.com",
)


def _walk_jsonld(value):
    """Yield nested Schema.org organization-like objects from JSON-LD."""
    if isinstance(value, dict):
        raw_type = value.get("@type", "")
        types = raw_type if isinstance(raw_type, list) else [raw_type]
        normalized = [str(item).lower().replace(" ", "") for item in types]
        if any(
            item.endswith(("organization", "localbusiness", "professionalservice"))
            or "localbusiness" in item
            for item in normalized
        ) and value.get("name"):
            yield value
        for child in value.values():
            yield from _walk_jsonld(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_jsonld(child)


def _evidence_urls(pages: list[dict], terms: list[str]) -> list[str]:
    normalized_terms = [term.lower() for term in terms]
    return sorted({
        page.get("url", "")
        for page in pages
        if any(term in page.get("text", "").lower() for term in normalized_terms)
        and page.get("url")
    })


def build_profile(start_url: str, pages: list[dict]) -> dict:
    if not pages:
        return {
            "website": start_url, "status": "insufficient_data", "pages_analyzed": 0,
            "business_name": None, "business_name_source": None,
            "business_description": None, "categories": [], "services_observed": [],
            "pricing_observations": [], "contact_observations": {"emails": [], "phones": []},
            "location_observations": [], "social_profiles": [], "confidence": "low",
            "evidence_pages": [],
        }

    homepage = pages[0]
    category_signals = categorize(" ".join(page.get("text", "") for page in pages))
    categories = []
    for signal in category_signals:
        terms = signal["matched_terms"]
        categories.append({
            "name": CATEGORY_LABELS.get(signal["category"], signal["category"]),
            "signal_key": signal["category"],
            "matched_terms": terms,
            "evidence_urls": _evidence_urls(pages, terms),
        })

    business_name = None
    business_name_source = None
    for page in pages:
        for structured_data in page.get("json_ld", []):
            for obj in _walk_jsonld(structured_data):
                candidate = str(obj.get("name", "")).strip()
                if candidate:
                    business_name = candidate[:200]
                    business_name_source = "structured_data"
                    break
            if business_name:
                break
        if business_name:
            break

    if not business_name:
        title = (homepage.get("title") or "").strip()
        # Only a weak fallback: title text can be a slogan or page label.
        candidate = title.split("|")[0].split("—")[0].strip()
        if candidate:
            business_name = candidate[:200]
            business_name_source = "homepage_title"

    service_terms = sorted({
        term for category in categories for term in category["matched_terms"]
    })
    services = [
        {"term": term, "evidence_urls": _evidence_urls(pages, [term])}
        for term in service_terms
    ]
    prices = sorted({
        str(price).strip()
        for page in pages for price in page.get("price_mentions", [])
        if str(price).strip()
    })[:50]
    emails = sorted({
        str(value).strip().lower()
        for page in pages for value in page.get("emails", [])
        if str(value).strip()
    })
    phones = sorted({
        str(value).strip()
        for page in pages for value in page.get("phones", [])
        if str(value).strip()
    })
    social_links = set()
    for page in pages:
        for link in page.get("external_links", []):
            parsed = urlparse(link)
            host = (parsed.hostname or "").lower()
            if any(host == domain or host.endswith("." + domain) for domain in SOCIAL_DOMAINS):
                social_links.add(link)

    location_observations = sorted({
        str(value).strip()
        for page in pages for value in page.get("location_observations", [])
        if str(value).strip()
    })
    evidence_pages = [
        {"url": page.get("url"), "title": page.get("title"),
         "excerpt": page.get("text", "")[:350]}
        for page in pages if page.get("url")
    ]

    return {
        "website": start_url,
        "status": "observed",
        "pages_analyzed": len(pages),
        "business_name": business_name,
        "business_name_source": business_name_source,
        "business_description": homepage.get("meta_description"),
        "categories": categories,
        "services_observed": services,
        "pricing_observations": prices,
        "contact_observations": {"emails": emails, "phones": phones},
        "location_observations": location_observations,
        "social_profiles": sorted(social_links),
        "confidence": "medium" if len(pages) >= 3 else "low",
        "evidence_pages": evidence_pages,
    }
