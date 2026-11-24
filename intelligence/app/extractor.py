"""Deterministic HTML extraction. Extracted signals are observations, not verified facts."""
from __future__ import annotations
import json, re
from urllib.parse import urljoin, urlparse
from selectolax.parser import HTMLParser

EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
PHONE_RE = re.compile(r"(?:\+?\d[\d().\-\s]{7,}\d)")
PRICE_RE = re.compile(r"(?:\$\s?\d+(?:,\d{3})*(?:\.\d{2})?|\d+(?:\.\d{2})?\s?(?:USD|dollars))", re.I)
TAXONOMY = {
 "web development":["web development","website development","web design","website design"],
 "marketing":["marketing","seo","social media marketing","advertising"],
 "consulting":["consulting","consultant","advisory"],
 "ecommerce":["e-commerce","ecommerce","online store","shop online"],
 "software":["software","saas","app development","application development"],
 "construction":["construction","contractor","remodeling","renovation"],
 "hospitality":["restaurant","catering","hotel","hospitality"],
 "healthcare":["healthcare","medical","clinic","patient"],
 "real estate":["real estate","realtor","property management"],
 "education":["education","training","courses","academy"],
 "finance":["financial","accounting","bookkeeping","insurance"],
 "retail":["retail","store","shop","products"],
 "manufacturing":["manufacturing","manufacturer","factory","production"],
 "logistics":["logistics","shipping","freight","delivery"],
}
def parse_page(url: str, html: str) -> dict:
    tree=HTMLParser(html)
    for n in tree.css("script,style,noscript,svg"): n.decompose()
    title=tree.css_first("title")
    desc=tree.css_first('meta[name="description"]')
    canonical=tree.css_first('link[rel="canonical"]')
    viewport=tree.css_first('meta[name="viewport"]')
    headings=[{"level":n.tag,"text":n.text(strip=True)} for n in tree.css("h1,h2,h3") if n.text(strip=True)][:60]
    text=tree.body.text(separator=" ",strip=True) if tree.body else tree.text(separator=" ",strip=True)
    text=re.sub(r"\s+"," ",text)[:30000]
    links=[]
    for a in tree.css("a[href]"):
        href=a.attributes.get("href","")
        dest=urljoin(url,href)
        if urlparse(dest).hostname==urlparse(url).hostname and urlparse(dest).scheme in {"http","https"}:
            links.append(dest.split("#")[0])
    emails=sorted(set(EMAIL_RE.findall(text)))
    phones=sorted(set(m.strip() for m in PHONE_RE.findall(text)))
    prices=sorted(set(PRICE_RE.findall(text)))[:50]
    jsonld=[]
    for node in tree.css('script[type="application/ld+json"]'):
        raw=node.text(strip=True)
        try:
            if raw and len(raw)<100000: jsonld.append(json.loads(raw))
        except (ValueError,TypeError): pass
    return {"url":url,"title":title.text(strip=True) if title else None,
      "meta_description":desc.attributes.get("content") if desc else None,
      "canonical":canonical.attributes.get("href") if canonical else None,
      "has_mobile_viewport":bool(viewport),"headings":headings,
      "text":text,"internal_links":sorted(set(links)),"emails":emails,
      "phones":phones[:25],"price_mentions":prices,"json_ld":jsonld[:20]}
def categorize(text: str) -> list[dict]:
    low=text.lower()
    out=[]
    for category,terms in TAXONOMY.items():
        matches=[t for t in terms if t in low]
        if matches: out.append({"category":category,"matched_terms":matches})
    return out
