#!/usr/bin/env python3
"""
fix_tiempo.py — HdD
Elimina el tiempo de lectura de todos los archivos del sitio y mueve
la fecha de los index-items al lado derecho (donde estaba el tiempo).

Cambios:
  1. Artículos HTML        → elimina la línea "<strong>Lectura</strong> · X min"
  2. Listas index-item     → mueve <span class="date"> al final, borra "X min →"
  3. index.html portada    → elimina <span class="portada-card-read">
  4. assets/style.css      → quita .portada-card-read, ajusta grid a 1fr auto
  5. nuevo_articulo.py     → quita slide-meta-tiempo del template
  6. update_portada.py     → quita read_long / read_short del HTML generado
"""

import re
import os
import glob

BASE = "/Users/pablorufas/Documents/Claude/Scheduled"

# ─────────────────────────────────────────────────────────────
# 1. Artículos HTML: eliminar span con "Lectura · X min"
# ─────────────────────────────────────────────────────────────

# Patrón antiguo (todos los artículos actuales):
# <span><strong>Lectura</strong> · 11 min</span>
LECTURA_RE = re.compile(
    r'\s*<span><strong>Lectura</strong>\s*·\s*\d+\s*min</span>\n?',
    re.IGNORECASE
)

# Patrón nuevo (nuevo_articulo.py con clases):
# <span class="slide-meta-sep">·</span>\n…<span class="slide-meta-tiempo">…</span>
TIEMPO_CLASE_RE = re.compile(
    r'\s*<span class="slide-meta-sep">·</span>\n'
    r'\s*<span class="slide-meta-tiempo">[^<]*</span>\n?'
)

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

changed_articles = 0
for path in sorted(article_files):
    with open(path, "r", encoding="utf-8") as fh:
        original = fh.read()
    text = LECTURA_RE.sub("", original)
    text = TIEMPO_CLASE_RE.sub("", text)
    if text != original:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        changed_articles += 1
        print(f"  ✓ {os.path.basename(path)}")

print(f"\nArtículos modificados: {changed_articles} / {len(article_files)}")

# ─────────────────────────────────────────────────────────────
# 2. Listas index-item: mover fecha al final, borrar "X min →"
#    Aplica a: noticias.html, educacion.html, newsletter.html, index.html
# ─────────────────────────────────────────────────────────────

# Patrón de un index-item completo con estructura de 3 columnas:
#   <span class="date">DD·MM·AA</span>
#   <div>...</div>
#   <span style="color: var(--ink-mute)...">X min →</span>
#
# Estrategia: capturar la fecha de la primera columna y sustituir
# la tercera columna por esa fecha.

INDEX_ITEM_RE = re.compile(
    r'(<a [^>]*class="index-item"[^>]*>)\s*\n'
    r'(\s*)<span class="date">([^<]+)</span>\s*\n'   # grupo 3 = fecha
    r'(\s*<div>.*?</div>)\s*\n'                       # grupo 4 = bloque central
    r'\s*<span[^>]*>[\d]+ min[^<]*</span>\s*\n'       # tercera col (borrar)
    r'(\s*</a>)',                                       # grupo 5 = cierre
    re.DOTALL
)

def rewrite_index_items(html):
    def replace(m):
        a_open  = m.group(1)
        indent  = m.group(2)
        fecha   = m.group(3).strip()
        div     = m.group(4).strip()
        a_close = m.group(5).strip()
        return (
            f"{a_open}\n"
            f"{indent}  {div}\n"
            f'{indent}  <span class="date">{fecha}</span>\n'
            f"{indent}{a_close}"
        )
    return INDEX_ITEM_RE.sub(replace, html)

LIST_FILES = ["noticias.html", "educacion.html", "newsletter.html", "index.html"]
for fname in LIST_FILES:
    path = f"{BASE}/{fname}"
    if not os.path.exists(path):
        continue
    with open(path, "r", encoding="utf-8") as fh:
        original = fh.read()
    text = rewrite_index_items(original)
    if text != original:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        n = len(INDEX_ITEM_RE.findall(original))
        print(f"  ✓ {fname}: {n} index-items actualizados")
    else:
        print(f"  · {fname}: sin cambios en index-items")

# ─────────────────────────────────────────────────────────────
# 3. index.html portada: eliminar <span class="portada-card-read">
# ─────────────────────────────────────────────────────────────

idx_path = f"{BASE}/index.html"
with open(idx_path, "r", encoding="utf-8") as fh:
    idx = fh.read()

PORTADA_READ_RE = re.compile(
    r'\s*<span class="portada-card-read">[^<]*</span>\n?'
)
idx_new = PORTADA_READ_RE.sub("", idx)
if idx_new != idx:
    with open(idx_path, "w", encoding="utf-8") as fh:
        fh.write(idx_new)
    print("  ✓ index.html: portada-card-read eliminado")
else:
    print("  · index.html: portada-card-read no encontrado (ya limpio)")

# ─────────────────────────────────────────────────────────────
# 4. assets/style.css: quitar .portada-card-read, ajustar grid
# ─────────────────────────────────────────────────────────────

css_path = f"{BASE}/assets/style.css"
with open(css_path, "r", encoding="utf-8") as fh:
    css = fh.read()

# Eliminar bloque .portada-card-read { ... }
css = re.sub(
    r'\n\.portada-card-read \{[^}]*\}\n',
    "\n",
    css
)

# Cambiar grid-template-columns de .index-item: 80px 1fr auto → 1fr auto
css = re.sub(
    r'(\.index-item\s*\{[^}]*grid-template-columns:\s*)80px 1fr auto',
    r'\g<1>1fr auto',
    css
)

# Mobile: 60px 1fr → 1fr auto
css = re.sub(
    r'(\.index-item\s*\{[^}]*grid-template-columns:\s*)60px 1fr',
    r'\g<1>1fr auto',
    css
)

with open(css_path, "w", encoding="utf-8") as fh:
    fh.write(css)
print("  ✓ assets/style.css: grid e .portada-card-read actualizados")

# ─────────────────────────────────────────────────────────────
# 5. nuevo_articulo.py: quitar slide-meta-tiempo del template
# ─────────────────────────────────────────────────────────────

nap_path = f"{BASE}/nuevo_articulo.py"
with open(nap_path, "r", encoding="utf-8") as fh:
    nap = fh.read()

# Eliminar las dos líneas: sep + tiempo
nap = re.sub(
    r"\s*<span class=\"slide-meta-sep\">·</span>\n"
    r"\s*<span class=\"slide-meta-tiempo\">\{tiempo\} min de lectura</span>\n",
    "\n",
    nap
)

with open(nap_path, "w", encoding="utf-8") as fh:
    fh.write(nap)
print("  ✓ nuevo_articulo.py: slide-meta-tiempo eliminado del template")

# ─────────────────────────────────────────────────────────────
# 6. update_portada.py: quitar read_long / read_short del HTML
# ─────────────────────────────────────────────────────────────

up_path = f"{BASE}/update_portada.py"
with open(up_path, "r", encoding="utf-8") as fh:
    up = fh.read()

# Quitar <span class="portada-card-read">{portada['read_long']}</span>
up = re.sub(
    r"\s*<span class=\"portada-card-read\">\{portada\['read_long'\]}</span>\\n",
    "\\n",
    up
)
# Quitar <span style="...">{item['read_short']}</span>
up = re.sub(
    r"\s*<span style=\"color: var\(--ink-mute\); font-size: 0\.78rem;\">\{item\['read_short'\]}</span>\\n",
    "\\n",
    up
)

with open(up_path, "w", encoding="utf-8") as fh:
    fh.write(up)
print("  ✓ update_portada.py: read_long/read_short eliminados del HTML generado")

print("\n✅ fix_tiempo.py completado.")
