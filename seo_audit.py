#!/usr/bin/env python3
"""
seo_audit.py — Extrae oportunidades SEO reales de Search Console
y analiza los artículos con mayor potencial de mejora.
"""
import json, os, sys, warnings, re
warnings.filterwarnings("ignore")

SITE_URL     = "https://horadedespertar.org/"
TOKEN_FILE   = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".ga4_token.json")
SECRETS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "client_secrets.json")
SCOPES       = [
    "https://www.googleapis.com/auth/analytics.readonly",
    "https://www.googleapis.com/auth/analytics.edit",
    "https://www.googleapis.com/auth/webmasters.readonly",
]

def get_creds():
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    creds = None
    if os.path.exists(TOKEN_FILE):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        except Exception:
            pass
    if creds and creds.valid:
        return creds
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            with open(TOKEN_FILE, "w") as f:
                json.dump({"token": creds.token, "refresh_token": creds.refresh_token,
                           "token_uri": creds.token_uri, "client_id": creds.client_id,
                           "client_secret": creds.client_secret, "scopes": list(creds.scopes or [])}, f)
            return creds
        except Exception:
            pass
    flow = InstalledAppFlow.from_client_secrets_file(SECRETS_FILE, SCOPES)
    creds = flow.run_local_server(port=8080, open_browser=True)
    with open(TOKEN_FILE, "w") as f:
        json.dump({"token": creds.token, "refresh_token": creds.refresh_token,
                   "token_uri": creds.token_uri, "client_id": creds.client_id,
                   "client_secret": creds.client_secret, "scopes": list(creds.scopes or [])}, f)
    return creds

def gsc_query(service, body):
    try:
        return service.searchanalytics().query(siteUrl=SITE_URL, body=body).execute()
    except Exception as e:
        return {"error": str(e)}

def main():
    creds = get_creds()
    import googleapiclient.discovery
    svc = googleapiclient.discovery.build("searchconsole", "v1", credentials=creds)

    print("\n" + "="*65)
    print("  HdD — OPORTUNIDADES SEO (Search Console)")
    print("="*65)

    # ── 1. Queries con impresiones pero CTR bajo (posición 1-15) ──
    r = gsc_query(svc, {
        "startDate": "2026-04-01", "endDate": "2026-05-12",
        "dimensions": ["query"], "rowLimit": 50,
        "dimensionFilterGroups": [{
            "filters": [{"dimension": "position", "operator": "lessThan", "expression": "20"}]
        }]
    })
    print("\n  🎯  Queries con potencial (posición < 20)")
    print(f"  {'Query':<45} {'Pos':>5}  {'Impr':>5}  {'Clicks':>6}  {'CTR':>5}")
    print(f"  {'-'*65}")
    opportunities = []
    for row in sorted(r.get("rows", []), key=lambda x: x["position"]):
        q     = row["keys"][0]
        pos   = row["position"]
        impr  = row["impressions"]
        cli   = row["clicks"]
        ctr   = row["ctr"] * 100
        print(f"  {q[:45]:<45} {pos:>5.1f}  {impr:>5}  {cli:>6}  {ctr:>4.1f}%")
        opportunities.append({"query": q, "pos": pos, "impr": impr, "clicks": cli, "ctr": ctr})

    # ── 2. Páginas con más impresiones pero pocos clicks ──────────
    rp = gsc_query(svc, {
        "startDate": "2026-04-01", "endDate": "2026-05-12",
        "dimensions": ["page"], "rowLimit": 20,
    })
    print("\n  📄  Páginas con más impresiones")
    print(f"  {'URL':<55} {'Pos':>5}  {'Impr':>5}  {'Clicks':>6}")
    print(f"  {'-'*73}")
    page_data = {}
    for row in sorted(r.get("rows", []), key=lambda x: -x["impressions"])[:15]:
        pass
    for row in sorted(rp.get("rows", []), key=lambda x: -x["impressions"])[:15]:
        url   = row["keys"][0].replace(SITE_URL.rstrip("/"), "")
        pos   = row["position"]
        impr  = row["impressions"]
        cli   = row["clicks"]
        print(f"  {url[:55]:<55} {pos:>5.1f}  {impr:>5}  {cli:>6}")
        page_data[url] = {"pos": pos, "impr": impr, "clicks": cli}

    # ── 3. Por query + página (qué query aterriza en qué página) ──
    rqp = gsc_query(svc, {
        "startDate": "2026-04-01", "endDate": "2026-05-12",
        "dimensions": ["query", "page"], "rowLimit": 30,
    })
    print("\n  🔗  Query → Página (mapeo completo)")
    print(f"  {'Query':<35}  {'Página':<40}  {'Pos':>5}  {'Impr':>5}")
    print(f"  {'-'*90}")
    query_page_map = []
    for row in sorted(rqp.get("rows", []), key=lambda x: x["position"])[:25]:
        q    = row["keys"][0]
        url  = row["keys"][1].replace(SITE_URL.rstrip("/"), "")
        pos  = row["position"]
        impr = row["impressions"]
        cli  = row["clicks"]
        print(f"  {q[:35]:<35}  {url[:40]:<40}  {pos:>5.1f}  {impr:>5}")
        query_page_map.append({"query": q, "url": url, "pos": pos, "impr": impr, "clicks": cli})

    # Guardar para análisis
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "seo_opportunities.json")
    with open(out, "w") as f:
        json.dump({"opportunities": opportunities, "pages": page_data, "query_page": query_page_map}, f, indent=2, ensure_ascii=False)
    print(f"\n  Datos guardados: {out}")
    print("="*65 + "\n")

if __name__ == "__main__":
    main()
