#!/usr/bin/env python3
"""
seo_fix.py — Optimiza títulos y meta descriptions para SEO
Basado en datos reales de Search Console: queries, posiciones e impresiones.
"""
import os, re

BASEDIR = os.path.dirname(os.path.abspath(__file__))

# Diccionario: slug → (title_sin_hdd, description)
# Title con " — HdD" se añade automáticamente
# Description: 150-160 chars
OPTIMIZATIONS = {
    "primero-mayo-2026-ccoo-ugt-huelga-gasolineras-04-2026": {
        # Query: "huelga gasolineras malaga" (pos 7.4, 127 impr) — keyword al inicio
        "title": "Huelga gasolineras Málaga 1 Mayo 2026: claves del paro",
        "desc":  "50.000 trabajadores de gasolineras paran el 1 de Mayo en el puente más largo del año. Manifestaciones de CCOO y UGT en Málaga con la vivienda como eje central.",
    },
    "elecciones-andalucia-2026-pp-moreno-campana-04-2026": {
        # Query: "elecciones andalucia 2026" (pos 8.5, 49 impr)
        "title": "Elecciones Andalucía 17 mayo 2026: encuestas y análisis",
        "desc":  "PP favorito a la mayoría absoluta, PSOE con Montero, Vox en caída. Todo lo que necesitas saber sobre las elecciones andaluzas del 17 de mayo de 2026.",
    },
    "pib-q1-2026-espana-desaceleracion-iran-04-2026": {
        # Query: "pib españa 2026" / "crecimiento economico españa" (pos 8.3, 27 impr)
        "title": "PIB España Q1 2026: crece el 0,6%, el menor en tres años",
        "desc":  "El INE confirma que España creció el 0,6% en el primer trimestre de 2026, dos décimas menos que en Q4. Causas del frenazo y qué puede pasar en el segundo trimestre.",
    },
    "bce-tipos-25-euribor-hipotecas-abril-2026-04-2026": {
        # Posición 5.0, 0 clicks — título anterior tenía 84 chars, Google lo truncaba
        # Query: "euribor abril 2026" / "bce tipos" / "hipoteca variable"
        "title": "BCE tipos 2,5% (abril 2026): qué pasa con el euríbor",
        "desc":  "El BCE congela los tipos en el 2,5% en abril 2026 y el euríbor cierra en 2,74%. Si tienes hipoteca variable en España, te explicamos qué cambia y qué esperar.",
    },
    "vivienda-espana-precio-record-supera-burbuja-2007-mayo-2026": {
        # Query: "burbuja inmobiliaria españa" / "burbuja inmobiliaria 2007" (pos 13.2, 17 impr)
        "title": "Vivienda España supera burbuja de 2007: 3.014 €/m²",
        "desc":  "Por primera vez el precio de la vivienda en España supera los máximos de la burbuja de 2007: 3.014 €/m² con una subida del 14,3% interanual. ¿Hay riesgo de nueva crisis?",
    },
    "banco-espana-dependencia-tecnologica-cloud-eeuu-04-2026": {
        # Query: "banco españa cloud" / "riesgo banca tecnologico" (pos 9.2, 20 impr)
        "title": "Banco de España: banca depende del cloud de EE.UU.",
        "desc":  "El Banco de España alerta: ningún banco opera sin AWS, Azure o Google Cloud. Con la guerra de aranceles de Trump, esa dependencia se vuelve un riesgo sistémico urgente.",
    },
    "debate-rtve-andalucia-5-candidatos-4-mayo-2026": {
        # Título anterior: 87 chars (truncado por Google). Query: "debate andalucia" (pos 10.9, 20 impr)
        "title": "Debate Andalucía RTVE 4 mayo: cinco candidatos",
        "desc":  "El primer debate de las elecciones andaluzas del 17 de mayo en La 1 (21:45h). Cinco candidatos, 90 minutos. Analizamos qué necesita cada uno para ganar.",
    },
    "reforma-constitucional-aborto-articulo-43-congreso-04-2026": {
        # Query: "reforma constitucional aborto" / "aborto constitucion" (pos 7.9, 17 impr)
        "title": "Aborto en la Constitución 2026: qué se vota y por qué fallará",
        "desc":  "El Congreso vota blindar el aborto en la Constitución el 30 de abril. PP y Vox votan en contra. El Gobierno lo impulsa sin votos. Qué dice el artículo 43 y qué pasará.",
    },
    "ley-vivienda-pp-junts-desahucios-04-2026": {
        # Posición 4.5 pero solo 2 impr. Query: "ley vivienda 2026" / "desahucios"
        "title": "Ley Vivienda PP 2026: sin zonas tensionadas, desahucios más rápidos",
        "desc":  "El Congreso aprueba tramitar la Ley de Vivienda del PP con apoyo de Junts. Elimina zonas tensionadas, acelera desahucios y liberaliza licencias. Lo que cambia para ti.",
    },
}


def escape_attr(s):
    return s.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;")


def update_file(slug, title_base, desc):
    fpath = os.path.join(BASEDIR, f"{slug}.html")
    if not os.path.exists(fpath):
        print(f"  ⚠️  No encontrado: {fpath}")
        return False

    html = open(fpath, encoding="utf-8").read()
    title_full = f"{title_base} — HdD"
    title_esc  = escape_attr(title_full)
    title_base_esc = escape_attr(title_base)
    desc_esc   = escape_attr(desc)

    # 1. <title>
    html = re.sub(r'<title>[^<]+</title>', f'<title>{title_esc}</title>', html)

    # 2. meta description
    html = re.sub(
        r'<meta name="description" content="[^"]*"',
        f'<meta name="description" content="{desc_esc}"',
        html
    )

    # 3. og:title
    html = re.sub(
        r'<meta property="og:title"\s+content="[^"]*"',
        f'<meta property="og:title"        content="{title_esc}"',
        html
    )

    # 4. og:description
    html = re.sub(
        r'<meta property="og:description"\s+content="[^"]*"',
        f'<meta property="og:description"  content="{desc_esc}"',
        html
    )

    # 5. twitter:title
    html = re.sub(
        r'<meta name="twitter:title"\s+content="[^"]*"',
        f'<meta name="twitter:title"        content="{title_esc}"',
        html
    )

    # 6. twitter:description
    html = re.sub(
        r'<meta name="twitter:description"\s+content="[^"]*"',
        f'<meta name="twitter:description"  content="{desc_esc}"',
        html
    )

    # 7. JSON-LD headline (sin " — HdD")
    html = re.sub(
        r'"headline":\s*"[^"]*"',
        f'"headline": "{title_base_esc}"',
        html
    )

    # 8. JSON-LD description
    html = re.sub(
        r'"description":\s*"[^"]*"',
        f'"description": "{desc_esc}"',
        html
    )

    open(fpath, "w", encoding="utf-8").write(html)
    t_len = len(title_full)
    d_len = len(desc)
    t_ok  = "✅" if t_len <= 65 else f"⚠️ {t_len}c"
    d_ok  = "✅" if 145 <= d_len <= 165 else f"⚠️ {d_len}c"
    print(f"  {t_ok} título ({t_len}c)  {d_ok} desc ({d_len}c)  → {slug[:50]}")
    return True


def main():
    print(f"\n{'='*60}")
    print(f"  HdD — SEO Fix: títulos y meta descriptions")
    print(f"{'='*60}\n")
    ok = 0
    for slug, data in OPTIMIZATIONS.items():
        if update_file(slug, data["title"], data["desc"]):
            ok += 1
    print(f"\n  ✅  {ok}/{len(OPTIMIZATIONS)} artículos actualizados")

    # Verificar longitudes
    print("\n  Resumen de títulos optimizados:")
    for slug, data in OPTIMIZATIONS.items():
        t = f"{data['title']} — HdD"
        d = data["desc"]
        flag_t = "" if len(t) <= 65 else f" ← {len(t)}c (largo)"
        flag_d = "" if 145 <= len(d) <= 165 else f" ← {len(d)}c"
        print(f"    {len(t):>2}c / {len(d):>3}c  {slug[:45]}{flag_t}{flag_d}")

    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    main()
