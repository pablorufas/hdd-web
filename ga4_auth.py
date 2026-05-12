#!/usr/bin/env python3
"""
ga4_auth.py — Autorización OAuth2 para GA4 + consulta de métricas HdD
"""
import json, os, sys, warnings
warnings.filterwarnings("ignore")

PROPERTY_ID   = "properties/534765544"
SCOPES        = ["https://www.googleapis.com/auth/analytics.readonly",
                 "https://www.googleapis.com/auth/analytics.edit",
                 "https://www.googleapis.com/auth/webmasters.readonly"]
SECRETS_FILE  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "client_secrets.json")
TOKEN_FILE    = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".ga4_token.json")

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
            save(creds); return creds
        except Exception:
            pass

    flow = InstalledAppFlow.from_client_secrets_file(SECRETS_FILE, SCOPES)
    creds = flow.run_local_server(port=8080, open_browser=True)
    save(creds)
    return creds

def save(creds):
    with open(TOKEN_FILE, "w") as f:
        json.dump({
            "token": creds.token,
            "refresh_token": creds.refresh_token,
            "token_uri": creds.token_uri,
            "client_id": creds.client_id,
            "client_secret": creds.client_secret,
            "scopes": list(creds.scopes or []),
        }, f)

def query_report(client, date_range, metrics, dimensions=None):
    from google.analytics.data_v1beta.types import (
        DateRange, Metric, Dimension, RunReportRequest
    )
    req = RunReportRequest(
        property=PROPERTY_ID,
        date_ranges=[DateRange(start_date=date_range[0], end_date=date_range[1])],
        metrics=[Metric(name=m) for m in metrics],
        dimensions=[Dimension(name=d) for d in (dimensions or [])],
    )
    return client.run_report(req)

def main():
    print("\n" + "="*55)
    print("  HdD — GA4 Métricas de audiencia")
    print("="*55)
    print("\n  Abriendo navegador para autorizar...")

    creds = get_creds()
    print("  ✅  Autorizado\n")

    from google.analytics.data_v1beta import BetaAnalyticsDataClient
    client = BetaAnalyticsDataClient(credentials=creds)

    # ── 1. Resumen últimos 28 días ──────────────────────────
    r = query_report(client, ["28daysAgo","today"],
                     ["activeUsers","sessions","screenPageViews","newUsers"])
    row = r.rows[0].metric_values if r.rows else None
    if row:
        usuarios    = int(row[0].value)
        sesiones    = int(row[1].value)
        pageviews   = int(row[2].value)
        nuevos      = int(row[3].value)
        print(f"  📊  Últimos 28 días")
        print(f"      Usuarios activos : {usuarios:,}")
        print(f"      Nuevos usuarios  : {nuevos:,}")
        print(f"      Sesiones         : {sesiones:,}")
        print(f"      Páginas vistas   : {pageviews:,}")

    # ── 2. Últimos 7 días ───────────────────────────────────
    r7 = query_report(client, ["7daysAgo","today"],
                      ["activeUsers","sessions"])
    row7 = r7.rows[0].metric_values if r7.rows else None
    if row7:
        print(f"\n  📅  Últimos 7 días")
        print(f"      Usuarios activos : {int(row7[0].value):,}")
        print(f"      Sesiones         : {int(row7[1].value):,}")

    # ── 3. Top 5 artículos (28d) ────────────────────────────
    rt = query_report(client, ["28daysAgo","today"],
                      ["screenPageViews"], ["pagePath"])
    if rt.rows:
        print(f"\n  🏆  Top artículos (28 días)")
        rows = sorted(rt.rows, key=lambda r: int(r.metric_values[0].value), reverse=True)
        for row in rows[:5]:
            path  = row.dimension_values[0].value
            views = int(row.metric_values[0].value)
            print(f"      {views:>5,}  {path}")

    # ── 4. Canales de tráfico ───────────────────────────────
    rc = query_report(client, ["28daysAgo","today"],
                      ["sessions"], ["sessionDefaultChannelGroup"])
    if rc.rows:
        print(f"\n  📡  Canales de tráfico")
        rows = sorted(rc.rows, key=lambda r: int(r.metric_values[0].value), reverse=True)
        for row in rows[:6]:
            ch   = row.dimension_values[0].value
            ses  = int(row.metric_values[0].value)
            print(f"      {ses:>5,}  {ch}")

    # ── 5. PWA events ───────────────────────────────────────
    re = query_report(client, ["28daysAgo","today"],
                      ["eventCount"], ["eventName"])
    pwa_events = ["pwa_installed","pwa_install_prompt","pwa_install_choice","pwa_session"]
    pwa_rows = [r for r in re.rows if r.dimension_values[0].value in pwa_events]
    if pwa_rows:
        print(f"\n  📱  PWA (últimos 28 días)")
        for row in sorted(pwa_rows, key=lambda r: int(r.metric_values[0].value), reverse=True):
            ev  = row.dimension_values[0].value
            cnt = int(row.metric_values[0].value)
            print(f"      {cnt:>5,}  {ev}")
    else:
        print(f"\n  📱  PWA: sin datos todavía (normal si el banner es reciente)")

    print("\n" + "="*55 + "\n")

if __name__ == "__main__":
    main()
