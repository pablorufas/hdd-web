#!/usr/bin/env python3
"""
fix_lee_tambien.py — HdD
Agrega "Lee también" con 3 links relacionados a artículos que no lo tienen.

Estrategia:
  1. Indexa todas las categorías directamente de los archivos .html
  2. Para cada artículo sin lee-también:
     - Busca 3 artículos por palabra clave compartida
  3. Extrae fechas de noticias.html si está disponible
  4. Agrega bloque lee-también antes de nota metodológica
"""

import re
import os
import glob

BASE = "/Users/pablorufas/Documents/Claude/Scheduled"

# ─────────────────────────────────────────────────────────────
# 1. Indexar categorías y fechas de TODOS los artículos .html
# ─────────────────────────────────────────────────────────────

SKIP_FILES = {
    "_plantilla-articulo.html", "articulo-ejemplo.html",
    "index.html", "noticias.html", "educacion.html",
    "newsletter.html", "manifiesto.html", "aviso-legal.html",
    "privacidad.html", "cookies.html",
}

article_files = [
    f for f in glob.glob(f"{BASE}/*.html")
    if os.path.basename(f) not in SKIP_FILES
]

print(f"Procesando {len(article_files)} artículos...")

# Indexar categoría de cada artículo
articles_db = {}

for path in article_files:
    slug = os.path.basename(path).replace('.html', '')
    with open(path, "r", encoding="utf-8") as fh:
        content = fh.read()

    # Extraer categoría del artículo: <span class="cat">...</span>
    cat_match = re.search(r'<span class="cat">([^<]+)</span>', content)
    if cat_match:
        cat = cat_match.group(1).strip()
        keywords = [kw.strip().lower() for kw in cat.split('·')]
        articles_db[slug] = {
            'path': path,
            'cat': cat,
            'keywords': keywords,
        }

print(f"Indexed {len(articles_db)} artículos con categoría")

# Cargar fechas de noticias.html
noticias_dates = {}
if os.path.exists(f"{BASE}/noticias.html"):
    with open(f"{BASE}/noticias.html", "r", encoding="utf-8") as fh:
        noticias = fh.read()

    # Patrón: <a href="slug.html" class="index-item">...<span class="date">DD·MM·AA</span>
    FECHA_RE = re.compile(
        r'<a href="([^"]+\.html)"\s+class="index-item">'
        r'(?:(?!</a>).)*'
        r'<span class="date">([^<]+)</span>',
        re.DOTALL
    )
    for m in FECHA_RE.finditer(noticias):
        slug = m.group(1).replace('.html', '')
        fecha = m.group(2).strip()
        noticias_dates[slug] = fecha

print(f"Loaded {len(noticias_dates)} fechas from noticias.html")

# ─────────────────────────────────────────────────────────────
# 2. Función para buscar artículos relacionados
# ─────────────────────────────────────────────────────────────

def find_related(current_slug, db, n=3):
    """Busca n artículos relacionados por palabra clave."""
    if current_slug not in db:
        return []

    current = db[current_slug]
    candidates = []

    # Scoring: cada palabra clave compartida suma puntos
    for slug, info in db.items():
        if slug == current_slug:
            continue

        shared = set(current['keywords']) & set(info['keywords'])
        if shared:
            # Dar más peso si la categoría es igual
            weight = len(shared) * 2 if info['cat'] == current['cat'] else len(shared)
            candidates.append((slug, weight))

    # Ordenar por peso descendente y devolver top n
    candidates = sorted(set(candidates), key=lambda x: -x[1])
    return [slug for slug, _ in candidates[:n]]

# ─────────────────────────────────────────────────────────────
# 3. Detectar artículos sin lee-también
# ─────────────────────────────────────────────────────────────

needs_lee_tambien = []

for slug, info in articles_db.items():
    path = info['path']
    with open(path, "r", encoding="utf-8") as fh:
        content = fh.read()

    # Detectar si YA tiene lee-también
    if 'class="lee-tambien-link"' in content or '<!-- LEE TAMBIÉN' in content:
        continue

    needs_lee_tambien.append(slug)

print(f"Artículos sin lee-también: {len(needs_lee_tambien)}")

# ─────────────────────────────────────────────────────────────
# 4. Agregar lee-también a artículos sin él
# ─────────────────────────────────────────────────────────────

fixed_count = 0
skipped_count = 0

for slug in needs_lee_tambien:
    # Buscar 3 artículos relacionados
    related = find_related(slug, articles_db, n=3)

    if not related:
        print(f"  ⚠ {slug}: no hay artículos relacionados")
        skipped_count += 1
        continue

    # Generar HTML de lee-también con fechas de noticias.html si están disponibles
    lee_html = '          <!-- LEE TAMBIÉN — NO mover. Debe estar ANTES de la nota metodológica -->\n'
    lee_html += '          <div class="lee-tambien">\n'
    lee_html += '            <span class="lee-tambien-label">Lee también en HdD</span>\n'

    for related_slug in related:
        if related_slug not in articles_db:
            continue

        # Si está en noticias.html, usar fecha de allí; si no, usar placeholder
        fecha = noticias_dates.get(related_slug, "DD·MM·AA")

        # Extraer título del HTML del artículo relacionado
        related_path = articles_db[related_slug]['path']
        with open(related_path, "r", encoding="utf-8") as fh:
            related_content = fh.read()

        titulo_match = re.search(
            r'<h1>([^<]+)</h1>|'
            r'<span class="portada-card-titular">([^<]+)</span>|'
            r'<h3[^>]*>([^<]+)</h3>',
            related_content
        )
        if titulo_match:
            titulo = next(g for g in titulo_match.groups() if g)
            lee_html += (
                f'            <a href="{related_slug}.html" class="lee-tambien-link">\n'
                f'              <span class="lee-tambien-fecha">{fecha}</span>\n'
                f'              <span class="lee-tambien-titulo">{titulo}</span>\n'
                f'            </a>\n'
            )

    lee_html += '          </div>\n'

    # Leer artículo a arreglarse
    path = articles_db[slug]['path']
    with open(path, "r", encoding="utf-8") as fh:
        content = fh.read()

    # Insertarante de <!-- NOTA METODOLÓGICA --> o antes de </section>
    if 'Nota metodológica' in content or 'nota metodologica' in content.lower():
        # Buscar el div didactic-box de nota metodológica
        content = re.sub(
            r'(          <div class="didactic-box"[^>]*>\n            <span class="eyebrow"[^>]*>(?:Nota metodológica|nota metodologica))',
            lee_html + r'\1',
            content,
            count=1,
            flags=re.IGNORECASE
        )
    else:
        # Insertarante del último </section> (como fallback)
        content = re.sub(
            r'(        </div>\n      </section>\n\n    </div>)',
            lee_html + r'\1',
            content,
            count=1
        )

    # Guardar
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)

    fixed_count += 1
    print(f"  ✓ {slug}: {len(related)} links agregados")

print(f"\n✅ fix_lee_tambien.py completado: {fixed_count} reparados, {skipped_count} sin relacionados")
