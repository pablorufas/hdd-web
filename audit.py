#!/usr/bin/env python3
"""
audit.py — Auditoría completa HdD: GA4 + Search Console + PageSpeed
Uso: python3 audit.py [--pagespeed-key TU_API_KEY]
"""
import json, os, sys, warnings, argparse, urllib.request, urllib.parse, time
warnings.filterwarnings("ignore")

PROPERTY_ID   = "properties/534765544"
SITE_URL      = "https://horadedespertar.org/"
SCOPES        = [
    "https://www.googleapis.com/auth/analytics.readonly",
    "https://www.googleapis.com/auth/analytics.edit",
    "https://www.googleapis.com/auth/webmasters.readonly",
]
SECRETS_FILE  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "client_secrets.json")
TOKEN_FILE    = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".ga4_token.json")

# ── Auth ──────────────────────────────────────────────────────────────────────
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
            creds.refresh(Request()); save_token(creds); return creds
        except Exception:
            pass
    flow = InstalledAppFlow.from_client_secrets_file(SECRETS_FILE, SCOPES)
    creds = flow.run_local_server(port=8080, open_browser=True)
    save_token(creds)
    return creds

def save_token(creds):
    with open(TOKEN_FILE, "w") as f:
        json.dump({
            "token": creds.token,
            "refresh_token": creds.refresh_token,
            "token_uri": creds.token_uri,
            "client_id": creds.client_id,
            "client_secret": creds.client_secret,
            "scopes": list(creds.scopes or []),
        }, f)

# ── GA4 ───────────────────────────────────────────────────────────────────────
def ga4_report(client, start, end, metrics, dimensions=None):
    from google.analytics.data_v1beta.types import DateRange, Metric, Dimension, RunReportRequest
    req = RunReportRequest(
        property=PROPERTY_ID,
        date_ranges=[DateRange(start_date=start, end_date=end)],
        metrics=[Metric(name=m) for m in metrics],
        dimensions=[Dimension(name=d) for d in (dimensions or [])],
        limit=50,
    )
    return client.run_report(req)

def run_ga4(creds):
    from google.analytics.data_v1beta import BetaAnalyticsDataClient
    client = BetaAnalyticsDataClient(credentials=creds)
    results = {}

    # Overview 28d
    r = ga4_report(client, "28daysAgo", "today",
                   ["activeUsers","sessions","screenPageViews","newUsers",
                    "bounceRate","averageSessionDuration","engagementRate"])
    if r.rows:
        mv = r.rows[0].metric_values
        results["overview_28d"] = {
            "usuarios":    int(mv[0].value),
            "sesiones":    int(mv[1].value),
            "pageviews":   int(mv[2].value),
            "nuevos":      int(mv[3].value),
            "bounce":      float(mv[4].value),
            "dur_media":   float(mv[5].value),
            "engagement":  float(mv[6].value),
        }

    # Overview 7d
    r7 = ga4_report(client, "7daysAgo", "today",
                    ["activeUsers","sessions","screenPageViews"])
    if r7.rows:
        mv7 = r7.rows[0].metric_values
        results["overview_7d"] = {
            "usuarios":  int(mv7[0].value),
            "sesiones":  int(mv7[1].value),
            "pageviews": int(mv7[2].value),
        }

    # Top páginas 28d
    rp = ga4_report(client, "28daysAgo", "today",
                    ["screenPageViews","activeUsers","averageSessionDuration"],
                    ["pagePath"])
    results["top_pages"] = []
    if rp.rows:
        rows = sorted(rp.rows, key=lambda r: int(r.metric_values[0].value), reverse=True)
        for row in rows[:10]:
            results["top_pages"].append({
                "path":     row.dimension_values[0].value,
                "views":    int(row.metric_values[0].value),
                "usuarios": int(row.metric_values[1].value),
                "dur":      float(row.metric_values[2].value),
            })

    # Canales
    rc = ga4_report(client, "28daysAgo", "today",
                    ["sessions","activeUsers"], ["sessionDefaultChannelGroup"])
    results["canales"] = []
    if rc.rows:
        for row in sorted(rc.rows, key=lambda r: int(r.metric_values[0].value), reverse=True):
            results["canales"].append({
                "canal":    row.dimension_values[0].value,
                "sesiones": int(row.metric_values[0].value),
                "usuarios": int(row.metric_values[1].value),
            })

    # Dispositivos
    rd = ga4_report(client, "28daysAgo", "today",
                    ["sessions"], ["deviceCategory"])
    results["dispositivos"] = {}
    if rd.rows:
        for row in rd.rows:
            results["dispositivos"][row.dimension_values[0].value] = int(row.metric_values[0].value)

    # Países top 5
    rco = ga4_report(client, "28daysAgo", "today",
                     ["activeUsers"], ["country"])
    results["paises"] = []
    if rco.rows:
        for row in sorted(rco.rows, key=lambda r: int(r.metric_values[0].value), reverse=True)[:5]:
            results["paises"].append({
                "pais": row.dimension_values[0].value,
                "usuarios": int(row.metric_values[0].value),
            })

    # Tendencia diaria 28d
    rday = ga4_report(client, "28daysAgo", "today",
                      ["activeUsers","sessions"], ["date"])
    results["diario"] = []
    if rday.rows:
        for row in sorted(rday.rows, key=lambda r: r.dimension_values[0].value):
            results["diario"].append({
                "fecha":   row.dimension_values[0].value,
                "usuarios": int(row.metric_values[0].value),
                "sesiones": int(row.metric_values[1].value),
            })

    # PWA events
    re = ga4_report(client, "28daysAgo", "today",
                    ["eventCount"], ["eventName"])
    pwa_keys = ["pwa_installed","pwa_install_prompt","pwa_install_choice","pwa_session"]
    results["pwa"] = {row.dimension_values[0].value: int(row.metric_values[0].value)
                      for row in re.rows if row.dimension_values[0].value in pwa_keys}

    # Retención: usuarios que vuelven
    rret = ga4_report(client, "28daysAgo", "today",
                      ["activeUsers"], ["newVsReturning"])
    results["retencion"] = {}
    if rret.rows:
        for row in rret.rows:
            results["retencion"][row.dimension_values[0].value] = int(row.metric_values[0].value)

    return results

# ── Search Console ────────────────────────────────────────────────────────────
def run_search_console(creds):
    import googleapiclient.discovery
    service = googleapiclient.discovery.build("searchconsole", "v1", credentials=creds)
    results = {}

    def query(start, end, dims, row_limit=10):
        body = {
            "startDate": start, "endDate": end,
            "dimensions": dims, "rowLimit": row_limit,
        }
        try:
            return service.searchanalytics().query(siteUrl=SITE_URL, body=body).execute()
        except Exception as e:
            return {"error": str(e)}

    # Overview 28d
    ov = query("2026-04-14", "2026-05-11", ["date"], 28)
    clicks_total = sum(r["clicks"] for r in ov.get("rows", []))
    impr_total   = sum(r["impressions"] for r in ov.get("rows", []))
    results["overview"] = {"clicks": clicks_total, "impresiones": impr_total}

    # Top queries
    tq = query("2026-04-14", "2026-05-11", ["query"], 20)
    results["queries"] = []
    for row in tq.get("rows", []):
        results["queries"].append({
            "query":       row["keys"][0],
            "clicks":      row["clicks"],
            "impresiones": row["impressions"],
            "posicion":    round(row["position"], 1),
            "ctr":         round(row["ctr"] * 100, 1),
        })

    # Top páginas por clicks
    tp = query("2026-04-14", "2026-05-11", ["page"], 10)
    results["paginas"] = []
    for row in tp.get("rows", []):
        results["paginas"].append({
            "url":         row["keys"][0],
            "clicks":      row["clicks"],
            "impresiones": row["impressions"],
            "posicion":    round(row["position"], 1),
            "ctr":         round(row["ctr"] * 100, 1),
        })

    # Dispositivos
    td = query("2026-04-14", "2026-05-11", ["device"])
    results["dispositivos"] = {}
    for row in td.get("rows", []):
        results["dispositivos"][row["keys"][0]] = {
            "clicks": row["clicks"], "impresiones": row["impressions"]
        }

    return results

# ── PageSpeed ─────────────────────────────────────────────────────────────────
def run_pagespeed(api_key=None):
    urls = [
        "https://horadedespertar.org/",
        "https://horadedespertar.org/noticias.html",
        "https://horadedespertar.org/abalos-mascarillas-supremo-maquillaje-mayo-2026.html",
    ]
    results = {}
    for url in urls:
        for strategy in ["mobile", "desktop"]:
            params = {"url": url, "strategy": strategy}
            if api_key:
                params["key"] = api_key
            params["category"] = ["performance", "seo", "accessibility", "best-practices"]
            qs = "&".join(f"category={c}" for c in params.pop("category"))
            base = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed?" + urllib.parse.urlencode(params) + "&" + qs
            try:
                with urllib.request.urlopen(base, timeout=30) as resp:
                    data = json.loads(resp.read())
                cats = data.get("lighthouseResult", {}).get("categories", {})
                audits = data.get("lighthouseResult", {}).get("audits", {})

                key = f"{url}|{strategy}"
                results[key] = {
                    "url":           url,
                    "strategy":      strategy,
                    "performance":   round(cats.get("performance", {}).get("score", 0) * 100),
                    "seo":           round(cats.get("seo", {}).get("score", 0) * 100),
                    "accessibility": round(cats.get("accessibility", {}).get("score", 0) * 100),
                    "best_practices":round(cats.get("best-practices", {}).get("score", 0) * 100),
                    "lcp":           audits.get("largest-contentful-paint", {}).get("displayValue", ""),
                    "fid":           audits.get("total-blocking-time", {}).get("displayValue", ""),
                    "cls":           audits.get("cumulative-layout-shift", {}).get("displayValue", ""),
                    "opportunities": [],
                }
                for aid, aud in audits.items():
                    if aud.get("score") is not None and aud.get("score") < 0.9:
                        savings = aud.get("details", {}).get("overallSavingsMs", 0)
                        if savings > 200 or aud.get("score") < 0.5:
                            results[key]["opportunities"].append({
                                "id":    aid,
                                "title": aud.get("title", ""),
                                "score": round((aud.get("score") or 0) * 100),
                                "savings_ms": savings,
                            })
                time.sleep(1)  # rate limit
            except Exception as e:
                results[f"{url}|{strategy}"] = {"error": str(e)}

    return results

# ── Imprimir informe ──────────────────────────────────────────────────────────
def print_report(ga4, gsc, ps):
    sep = "=" * 62
    print(f"\n{sep}")
    print("  HdD — AUDITORÍA COMPLETA")
    print(sep)

    # ── GA4 ──
    print("\n  ━━ GA4 — AUDIENCIA ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    o = ga4.get("overview_28d", {})
    o7 = ga4.get("overview_7d", {})
    ret = ga4.get("retencion", {})
    nuevos   = ret.get("new", ret.get("New", 0))
    vuelven  = ret.get("returning", ret.get("Returning", 0))
    print(f"  {'Métrica':<28} {'28 días':>10}  {'7 días':>10}")
    print(f"  {'-'*50}")
    print(f"  {'Usuarios activos':<28} {o.get('usuarios',0):>10,}  {o7.get('usuarios',0):>10,}")
    print(f"  {'Sesiones':<28} {o.get('sesiones',0):>10,}  {o7.get('sesiones',0):>10,}")
    print(f"  {'Páginas vistas':<28} {o.get('pageviews',0):>10,}  {o7.get('pageviews',0):>10,}")
    print(f"  {'Nuevos usuarios':<28} {o.get('nuevos',0):>10,}")
    print(f"  {'Tasa de rebote':<28} {o.get('bounce',0)*100:>9.1f}%")
    dur = o.get('dur_media', 0)
    print(f"  {'Duración media sesión':<28} {int(dur//60)}m {int(dur%60):02d}s")
    print(f"  {'Engagement rate':<28} {o.get('engagement',0)*100:>9.1f}%")
    if nuevos or vuelven:
        print(f"\n  Retención → Nuevos: {nuevos}  |  Vuelven: {vuelven}  ({vuelven/(nuevos+vuelven)*100:.0f}% retención)" if (nuevos+vuelven) else "")

    print(f"\n  Dispositivos: ", end="")
    for d, v in ga4.get("dispositivos", {}).items():
        print(f"{d}: {v}  ", end="")
    print()

    print(f"\n  Países top:")
    for p in ga4.get("paises", [])[:5]:
        print(f"    {p['pais']:<20} {p['usuarios']:>5,} usuarios")

    print(f"\n  Canales de tráfico:")
    for c in ga4.get("canales", []):
        bar = "█" * min(30, int(c['sesiones'] / max(1, ga4['overview_28d'].get('sesiones',1)) * 30))
        print(f"    {c['canal']:<30} {c['sesiones']:>5,}  {bar}")

    print(f"\n  Top páginas (28 días):")
    for p in ga4.get("top_pages", [])[:8]:
        dur_p = p.get('dur', 0)
        print(f"    {p['views']:>5,}  {p['path']:<50}  {int(dur_p//60)}m{int(dur_p%60):02d}s")

    pwa = ga4.get("pwa", {})
    if pwa:
        print(f"\n  PWA installs:")
        for ev, cnt in pwa.items():
            print(f"    {cnt:>5,}  {ev}")
    else:
        print(f"\n  PWA: sin datos aún (banner reciente)")

    # ── GSC ──
    print(f"\n  ━━ SEARCH CONSOLE — SEO ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    gsc_ov = gsc.get("overview", {})
    if "error" in gsc_ov:
        print(f"  ⚠️  Error GSC: {gsc_ov['error']}")
    else:
        print(f"  Clicks totales (28d): {gsc_ov.get('clicks',0):,}")
        print(f"  Impresiones   (28d): {gsc_ov.get('impresiones',0):,}")
        ctr = gsc_ov.get('clicks',0) / max(1, gsc_ov.get('impresiones',1)) * 100
        print(f"  CTR medio           : {ctr:.1f}%")

    queries = gsc.get("queries", [])
    if queries:
        print(f"\n  Top búsquedas:")
        print(f"    {'Query':<40} {'Clicks':>7}  {'Impr':>7}  {'Pos':>6}  {'CTR':>5}")
        print(f"    {'-'*70}")
        for q in queries[:10]:
            print(f"    {q['query'][:40]:<40} {q['clicks']:>7,}  {q['impresiones']:>7,}  {q['posicion']:>6.1f}  {q['ctr']:>4.1f}%")

    paginas_gsc = gsc.get("paginas", [])
    if paginas_gsc:
        print(f"\n  Top páginas SEO:")
        for p in paginas_gsc[:5]:
            slug = p['url'].replace("https://horadedespertar.org/", "/")
            print(f"    {slug:<50}  clicks:{p['clicks']}  pos:{p['posicion']}")

    # ── PageSpeed ──
    print(f"\n  ━━ PAGESPEED ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    printed = set()
    for key, data in ps.items():
        if "error" in data:
            print(f"  ⚠️  Error {key}: {data['error'][:80]}")
            continue
        url_short = data['url'].replace("https://horadedespertar.org", "")
        label = f"{url_short or '/'} [{data['strategy']}]"
        if label in printed: continue
        printed.add(label)
        perf = data['performance']
        seo  = data['seo']
        acc  = data['accessibility']
        bp   = data['best_practices']
        emoji_p = "🟢" if perf >= 90 else ("🟡" if perf >= 50 else "🔴")
        print(f"\n  {label}")
        print(f"    Perf {emoji_p} {perf:>3}  SEO {'🟢' if seo>=90 else '🟡'} {seo:>3}  "
              f"A11y {'🟢' if acc>=90 else '🟡'} {acc:>3}  BP {'🟢' if bp>=90 else '🟡'} {bp:>3}")
        print(f"    LCP: {data['lcp']:<12}  TBT: {data['fid']:<12}  CLS: {data['cls']}")
        opps = sorted(data.get("opportunities", []), key=lambda x: -x.get("savings_ms", 0))
        if opps:
            print(f"    Mejoras:")
            for op in opps[:4]:
                ms = f" ({op['savings_ms']}ms)" if op.get("savings_ms") else ""
                print(f"      ✗ {op['title'][:55]}{ms}")

    print(f"\n{sep}\n")

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pagespeed-key", default=None)
    parser.add_argument("--skip-pagespeed", action="store_true")
    parser.add_argument("--skip-gsc", action="store_true")
    args = parser.parse_args()

    print("\n  Autenticando...", end=" ", flush=True)
    creds = get_creds()
    print("✅")

    print("  GA4...", end=" ", flush=True)
    ga4 = run_ga4(creds)
    print("✅")

    gsc = {}
    if not args.skip_gsc:
        print("  Search Console...", end=" ", flush=True)
        try:
            gsc = run_search_console(creds)
            print("✅")
        except Exception as e:
            print(f"⚠️  {e}")

    ps = {}
    if not args.skip_pagespeed:
        print("  PageSpeed (puede tardar ~30s)...", end=" ", flush=True)
        try:
            ps = run_pagespeed(args.pagespeed_key)
            print("✅")
        except Exception as e:
            print(f"⚠️  {e}")

    # Guardar JSON completo
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "audit_result.json")
    with open(out, "w") as f:
        json.dump({"ga4": ga4, "gsc": gsc, "pagespeed": ps}, f, indent=2)

    print_report(ga4, gsc, ps)
    print(f"  Datos completos: {out}\n")

if __name__ == "__main__":
    main()
