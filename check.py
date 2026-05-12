#!/usr/bin/env python3
"""
check.py — Validador de artículos HdD
Corre ANTES de cada git push: python3 check.py
Detecta todos los bugs conocidos antes de que lleguen a producción.
"""

import re, glob, sys
from collections import defaultdict

# Artículos estándar (4 slides)
ARTICLES = [f for f in sorted(glob.glob('*.html'))
            if not f.startswith('_') and f not in
            ['index.html','noticias.html','educacion.html','newsletter.html',
             'manifiesto.html','aviso-legal.html','privacidad.html','cookies.html',
             'articulo-ejemplo.html','inflacion-explicada.html','oferta-y-demanda.html']]

# Artículos especiales: más de 4 slides, pueden no estar en noticias.html
SPECIAL_ARTICLES = [
    'caso-kitchen-investigacion-completa-semanal-04-2026.html',          # 9 slides
    'corrupcion-entorno-sanchez-guia-04-2026.html',                      # 8 slides
    'bbva-sabadell-opa-banca-04-2026.html',                              # duplicado
    'agentes-ia-que-son-como-funcionan-educacion-2026.html',             # 8 slides
    'inflacion-explicada.html',                                           # 7 slides
    'oferta-y-demanda.html',                                             # 6 slides
    'hantavirus-mv-hondius-cepa-andes-tenerife-espana-mayo-2026.html',  # 5 slides
    'caso-koldo-juicio-supremo-recta-final-sentencia-mayo-2026.html',   # 5 slides
    'trump-iran-tregua-derrumbe-propuesta-basura-mayo-2026.html',       # 5 slides
    'espana-ejercito-europeo-coalicion-voluntarios-albares-mayo-2026.html',  # 5 slides
    'iran-hayi-terrorismo-gig-economy-europa-sinagogas-mayo-2026.html',  # 5 slides
    'hantavirus-espanol-positivo-confirmado-gomez-ulla-sanchez-oms-mayo-2026.html',  # 5 slides
]

ALL_PAGES = [f for f in sorted(glob.glob('*.html')) if not f.startswith('_')
             and f != 'articulo-ejemplo.html']

errors   = defaultdict(list)  # {archivo: [errores]}
warnings = defaultdict(list)  # {archivo: [avisos]}

# ── Fecha map desde noticias.html (fuente de verdad) ─────────────────────────
noticias_html = open('noticias.html').read()
date_map = {}
# Paso 1: registrar todos los hrefs presentes en noticias.html (sin fecha requerida)
for href in re.findall(r'<a href="([^/"#][^"]*)" class="index-item"', noticias_html):
    href_file = href if href.endswith('.html') else href + '.html'
    date_map[href_file] = ""
# Paso 2: sobreescribir con fecha real cuando exista
for href, date in re.findall(
        r'<a href="([^/"#][^"]*)" class="index-item">(?:(?!<a href=).)*?<span class="date">([^<]+)</span>',
        noticias_html, re.DOTALL):
    href_file = href if href.endswith('.html') else href + '.html'
    date_map[href_file] = date

# ── Checks por artículo ───────────────────────────────────────────────────────
for f in ARTICLES:
    html = open(f).read()
    E = errors[f]
    W = warnings[f]

    # 1. Meta tags obligatorios
    if 'og:image' not in html:
        E.append("Falta og:image")
    if 'twitter:image' not in html:
        E.append("Falta twitter:image")
    if 'rel="canonical"' not in html:
        E.append("Falta canonical")
    if 'name="description"' not in html:
        E.append("Falta meta description")

    # 2. Favicon
    if 'favicon' not in html:
        E.append("Faltan links de favicon")

    # 3. GA, PWA, OneSignal
    if 'G-RTLZFW7HGF' not in html:
        E.append("Falta Google Analytics")
    if 'manifest.json' not in html:
        E.append("Falta PWA manifest")
    if 'OneSignal' not in html:
        E.append("Falta OneSignal")

    # 4. JSON-LD
    if 'NewsArticle' not in html:
        E.append("Falta JSON-LD NewsArticle")
    if 'BreadcrumbList' not in html:
        E.append("Falta JSON-LD BreadcrumbList")

    # 5. Tokens EDITAR sin reemplazar
    editar_count = html.count('EDITAR')
    if editar_count > 0:
        E.append(f"Contiene {editar_count} token(s) EDITAR sin reemplazar")

    # 6. Nota metodológica presente
    if 'Nota metod' not in html:
        E.append("Falta Nota metodológica en el slide de análisis")

    # 7. back-link presente
    if 'class="back-link"' not in html:
        W.append("Falta back-link '← Todas las noticias'")

    # 8. Lee también presente y ANTES de nota metodológica
    pos_lee  = html.find('Lee también')
    pos_nota = html.find('Nota metod')
    if pos_lee == -1:
        W.append("Falta sección 'Lee también'")
    elif pos_nota > -1 and pos_lee > pos_nota:
        E.append("'Lee también' aparece DESPUÉS de la nota metodológica (debe ir antes)")

    # 9. Lee también NO debe estar fuera del slides-view (fuera de </div><!-- /slides-view -->)
    slides_end = html.find('</div><!-- /slides-view -->')
    if slides_end == -1:
        slides_end = html.find('</main>')
    if pos_lee > -1 and pos_lee > slides_end:
        E.append("'Lee también' está fuera del slides-view (debe ir dentro del slide de análisis)")

    # 10. Fechas en Lee también no deben ser "01·04" (confusión slide-num)
    if pos_lee > -1:
        lee_block = html[pos_lee:pos_lee+2000]
        bad_dates = re.findall(r'<span class="date">0[1-4]·04·\d+</span>', lee_block)
        # Flag if ALL dates look like "slide N of 4" pattern (0X·04·YY)
        all_dates = re.findall(r'<span class="date">([^<]+)</span>', lee_block)
        suspicious = [d for d in all_dates if re.match(r'0[1-4]·0[1-4]·\d{2}$', d)]
        if len(suspicious) == len(all_dates) and all_dates:
            W.append(f"Fechas en 'Lee también' parecen slide-num ({suspicious}) — verifica que son fechas reales")

    # 11. Fecha en JSON-LD no debe ser placeholder
    if '"datePublished": "EDITAR' in html:
        E.append("JSON-LD datePublished sin rellenar")
    if '"datePublished": "2026-04-29"' in html and f not in date_map:
        W.append("JSON-LD datePublished es 2026-04-29 pero el artículo no aparece en noticias.html con esa fecha")

    # 12. Canonical no debe ser placeholder
    if 'EDITAR-slug' in html:
        E.append("Canonical URL contiene placeholder EDITAR-slug")

    # 13. slide-num correcto (01-04, no fechas) — excluir artículos especiales
    if f not in SPECIAL_ARTICLES:
        slide_nums = re.findall(r'<span class="slide-num">(\d+) — (\d+)</span>', html)
        for pos, total in slide_nums:
            if total != '04':
                W.append(f"slide-num '{pos} — {total}': el total no es 04")

# ── Checks globales ───────────────────────────────────────────────────────────
# Artículos en noticias.html que no existen como archivo (date_map ya tiene claves con .html)
for href in date_map:
    if not glob.glob(href):
        warnings['noticias.html'].append(f"Enlace a '{href}' pero el archivo no existe")

# Artículos que existen pero no están en noticias.html (excluir especiales)
for f in ARTICLES:
    if f not in date_map and f not in SPECIAL_ARTICLES:
        warnings[f].append("Artículo no aparece en noticias.html")

# Favicon en todas las páginas
for f in ALL_PAGES:
    html = open(f).read()
    if 'favicon' not in html:
        errors[f].append("Falta favicon")

# ── Informe ───────────────────────────────────────────────────────────────────
total_errors   = sum(len(v) for v in errors.values())
total_warnings = sum(len(v) for v in warnings.values())

print(f"\n{'='*60}")
print(f"  HdD — check.py · {len(ARTICLES)} artículos auditados")
print(f"{'='*60}")

if total_errors == 0 and total_warnings == 0:
    print("\n  ✅  Todo correcto. Puedes hacer git push.\n")
    sys.exit(0)

if total_errors > 0:
    print(f"\n  ❌  ERRORES ({total_errors}) — corrige antes de publicar:\n")
    for f, errs in sorted(errors.items()):
        if errs:
            print(f"  {f}")
            for e in errs:
                print(f"    ✗ {e}")

if total_warnings > 0:
    print(f"\n  ⚠️   AVISOS ({total_warnings}) — revisa si aplican:\n")
    for f, warns in sorted(warnings.items()):
        if warns:
            print(f"  {f}")
            for w in warns:
                print(f"    △ {w}")

print(f"\n{'='*60}\n")
sys.exit(1 if total_errors > 0 else 0)
