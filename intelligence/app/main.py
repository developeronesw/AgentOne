from __future__ import annotations
import os
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, HttpUrl, Field
from .crawler import crawl_site
from .audit import audit_pages
from .extractor import categorize
from .safety import safe_target
app=FastAPI(title="AgentOne Intelligence API",version="0.1.0")
KEY=os.getenv("API_KEY","")
LIMIT=max(1,min(int(os.getenv("CRAWL_MAX_PAGES","8")),20))
TIMEOUT=max(3,min(float(os.getenv("CRAWL_TIMEOUT_SECONDS","12")),30))
class AnalyzeRequest(BaseModel):
    url: HttpUrl
    max_pages: int|None=Field(default=None,ge=1,le=20)
@app.get("/health")
def health(): return {"status":"ok","service":"agentone-intelligence","version":"0.1.0"}
@app.post("/v1/analyze")
async def analyze(req: AnalyzeRequest,x_api_key: str|None=Header(default=None)):
    if not KEY: raise HTTPException(503,"Service API key is not configured.")
    if x_api_key!=KEY: raise HTTPException(401,"Unauthorized")
    try: url=safe_target(str(req.url))
    except ValueError as e: raise HTTPException(400,str(e))
    try: crawl=await crawl_site(url,req.max_pages or LIMIT,TIMEOUT)
    except Exception as e: raise HTTPException(502,f"Analysis failed ({type(e).__name__})")
    pages=crawl["pages"]; combined=" ".join(p["text"] for p in pages)
    category_signals=categorize(combined)
    emails=sorted({v for p in pages for v in p["emails"]})
    phones=sorted({v for p in pages for v in p["phones"]})
    terms=sorted({t for cat in category_signals for t in cat["matched_terms"]})
    services=[{"term":term,"evidence_pages":[p["url"] for p in pages if term.lower() in p["text"].lower()]} for term in terms]
    profile={"website":url,"page_count":len(pages),"page_urls":[p["url"] for p in pages],
      "category_signals":category_signals,"service_keyword_signals":services,
      "public_contact_observations":{"emails":emails,"phones":phones},
      "homepage_title":pages[0]["title"] if pages else None,
      "homepage_description":pages[0]["meta_description"] if pages else None,
      "price_mentions":sorted({v for p in pages for v in p["price_mentions"]})[:50],
      "structured_data":[v for p in pages for v in p["json_ld"]][:20]}
    return {"profile":profile,"website_audit":audit_pages(pages),
      "crawl_metadata":{"errors":crawl["errors"],"robots_checked":crawl["robots_checked"],"pages_requested_limit":crawl["page_limit"]},
      "evidence":[{"page_url":p["url"],"title":p["title"],"excerpt":p["text"][:350]} for p in pages]}
