"""Crawl a small, robots-aware site sample. Redirect destinations are checked before fetching."""
from __future__ import annotations
import urllib.robotparser
from urllib.parse import urljoin, urlparse
import httpx
from .safety import safe_target
from .extractor import parse_page

UA="AgentOneBot/0.1 (+https://developeronecms.com/agentone)"
async def safe_get(client: httpx.AsyncClient, url: str, redirects: int=4):
    current=safe_target(url)
    for _ in range(redirects+1):
        response=await client.get(current,follow_redirects=False)
        if response.status_code not in {301,302,303,307,308}: return response
        loc=response.headers.get("location")
        if not loc: return response
        current=safe_target(urljoin(current,loc))
    raise ValueError("Too many redirects.")
async def crawl_site(start_url: str, page_limit: int=8, timeout: float=12) -> dict:
    start=safe_target(start_url); origin=urlparse(start)
    async with httpx.AsyncClient(timeout=httpx.Timeout(timeout,connect=min(timeout,5)),headers={"User-Agent":UA},verify=True) as client:
        robots_url=f"{origin.scheme}://{origin.netloc}/robots.txt"
        robots_text=""
        try:
            rr=await safe_get(client,robots_url)
            if rr.status_code==200: robots_text=rr.text[:100000]
        except (httpx.HTTPError,ValueError): pass
        rp=urllib.robotparser.RobotFileParser(); rp.set_url(robots_url); rp.parse(robots_text.splitlines())
        sitemap_urls=[f"{origin.scheme}://{origin.netloc}/sitemap.xml"]
        sitemap_urls += [line.split(":",1)[1].strip() for line in robots_text.splitlines() if line.lower().startswith("sitemap:")]
        candidates=[]
        for sm_url in sitemap_urls[:5]:
            try:
                sm=await safe_get(client,sm_url)
                if sm.status_code==200 and "xml" in sm.headers.get("content-type","").lower():
                    import re
                    candidates.extend(re.findall(r"<loc>\s*(.*?)\s*</loc>",sm.text[:500000],re.I))
            except (httpx.HTTPError,ValueError): pass
        queue=[start]+[u for u in candidates if urlparse(u).hostname==origin.hostname]
        prioritize=("service","product","price","about","contact","portfolio","work","faq","team")
        pages=[]; visited=set(); errors=[]
        while queue and len(pages)<page_limit:
            url=queue.pop(0).split("#")[0]
            if url in visited: continue
            visited.add(url)
            parsed=urlparse(url)
            if parsed.hostname!=origin.hostname or not rp.can_fetch(UA,url): continue
            try:
                res=await safe_get(client,url)
                if res.status_code>=400:
                    errors.append({"url":url,"status":res.status_code}); continue
                if "html" not in res.headers.get("content-type","").lower(): continue
                page=parse_page(str(res.url),res.text[:1500000])
                page.update({"http_status":res.status_code,"last_modified":res.headers.get("last-modified")})
                pages.append(page)
                links=[u for u in page["internal_links"] if u not in visited]
                links.sort(key=lambda u:(not any(k in u.lower() for k in prioritize),len(u)))
                queue.extend(links[:100])
            except (httpx.HTTPError,ValueError,UnicodeError) as exc:
                errors.append({"url":url,"error":type(exc).__name__})
        return {"requested_url":start,"pages":pages,"errors":errors,"robots_checked":True,"page_limit":page_limit}
