"""Transparent website checks; warnings represent missing observations, not absolute failures."""
from datetime import datetime, timezone
from urllib.parse import urlparse
def audit_pages(pages: list[dict]) -> dict:
    if not pages: return {"score":None,"checks":[],"summary":"No pages were successfully analyzed."}
    checks=[]; first=pages[0]
    def add(key,label,status,evidence): checks.append({"key":key,"label":label,"status":status,"evidence":evidence})
    parsed=urlparse(first["url"])
    add("https","HTTPS", "pass" if parsed.scheme=="https" else "warning",f"URL scheme: {parsed.scheme}")
    add("title","Title tag","pass" if first.get("title") else "warning",first.get("title") or "No title detected")
    add("description","Meta description","pass" if first.get("meta_description") else "warning",first.get("meta_description") or "No meta description detected")
    h1=[h["text"] for h in first.get("headings",[]) if h.get("level")=="h1"]
    add("h1","H1 heading","pass" if h1 else "warning",h1 or "No H1 detected")
    add("viewport","Mobile viewport","pass" if first.get("has_mobile_viewport") else "warning","Viewport meta present" if first.get("has_mobile_viewport") else "Viewport meta not detected")
    link_count=len(first.get("internal_links",[]))
    add("navigation","Internal links","pass" if link_count else "warning",f"{link_count} internal links found")
    contact=any(p.get("emails") or p.get("phones") or "contact" in p["url"].lower() for p in pages)
    add("contact","Contact signals","pass" if contact else "unknown","Public contact or contact path detected" if contact else "No contact signals found in limited crawl")
    structured=any(p.get("json_ld") for p in pages)
    add("schema","Structured data","pass" if structured else "warning","JSON-LD detected" if structured else "No JSON-LD detected")
    warnings=sum(c["status"]=="warning" for c in checks)
    score=round(100*(len(checks)-warnings)/len(checks))
    return {"score":score,"checks":checks,"audited_at":datetime.now(timezone.utc).isoformat(),"pages_analyzed":len(pages),"scoring_note":"Preliminary heuristic score; not a ranking or guarantee."}
