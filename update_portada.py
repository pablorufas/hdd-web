#!/usr/bin/env python3
"""
update_portada.py — HdD
Actualiza la portada (index.html) con los artículos más recientes de noticias.html.
Añade separadores de fecha en noticias.html si faltan.
Hace git commit + push automáticamente.

Uso: python3 update_portada.py [--dry-run] [--no-git]
  --dry-run  Detecta cambios pero no escribe ni hace git
  --no-git   Escribe archivos pero no hace commit/push (para GitHub Actions)
"""

import re
import subprocess
import sys
import os

BASEDIR = "/Users/pablorufas/Documents/Claude/Scheduled"
NOTICIAS = f"{BASEDIR}/noticias.html"
INDEX    = f"{BASEDIR}/index.html"
DRY_RUN  = "--dry-run" in sys.argv
NO_GIT   = "--no-git" in sys.argv

MESES_ES = {
    1: "enero", 2: "febrero", 3: "marzo", 4: "abril",
    5: "mayo", 6: "junio", 7: "julio", 8: "agosto",
    9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre"
}

def fecha_larga(date_str):
    """'05·05·26' → '5 de mayo de 2026'"""
    parts = date_str.split("·")
    d, m, y = int(parts[0]), int(parts[1]), int(parts[2])
    return f"{d} de {MESES_ES[m]} de {2000 + y}"

def parse_items(html):
    """Extrae todos los index-items de noticias.html en orden.
    Formato actual: <a class="index-item"><div>cat+h3+summary</div><span class="date">DD·MM·AA</span></a>
    """
    pattern = re.compile(
        r'<a href="([^"]+)"\s+class="index-item">\s*'
        r'<div>\s*<span class="cat">([^<]+)</span>\s*'
        r'<h3>(.*?)</h3>\s*'
        r'<p class="summary">(.*?)</p>\s*'
        r'</div>\s*'
        r'<span class="date">([^<]+)</span>\s*'
        r'</a>',
        re.DOTALL
    )
    items = []
    for m in pattern.finditer(html):
        items.append({
            "href":    m.group(1).strip(),
            "cat":     m.group(2).strip(),
            "h3":      m.group(3).strip(),
            "summary": m.group(4).strip(),
            "date":    m.group(5).strip(),
        })
    return items

def ensure_date_dividers(html, items):
    """
    Garantiza que existe un <div class="date-divider">DD·MM·AA</div>
    antes del primer artículo de cada fecha (excepto la más reciente).
    También convierte los antiguos .day-sep en .date-divider con fecha.
    """
    # Recopilar fechas en orden de aparición
    dates_seen = []
    for item in items:
        if item["date"] not in dates_seen:
            dates_seen.append(item["date"])

    # Eliminar day-sep legacy (los reemplazamos por date-divider con fecha)
    # Primero detectar su posición: están entre dos grupos de fechas distintas
    # Estrategia: para cada fecha (a partir de la 2ª), insertar date-divider
    # si no existe ya uno para esa fecha.
    for date in dates_seen[1:]:
        divider_tag = f'<div class="date-divider">{date}</div>'
        if divider_tag in html:
            continue  # Ya existe, no hacer nada

        # Buscar el primer index-item con esta fecha e insertar el divider antes
        # La fecha está ahora al final del item: <span class="date">DD·MM·AA</span></a>
        first_item_re = re.compile(
            r'(?=<a href="[^"]+"\s+class="index-item">)'
        )
        # Hacemos lookup por fecha dentro del bloque completo del item
        first_item_re = re.compile(
            r'(?=<a href="[^"]+"\s+class="index-item">(?:(?!</a>).)*'
            r'<span class="date">' + re.escape(date) + r'</span>\s*</a>)',
            re.DOTALL
        )
        html, n = first_item_re.subn(divider_tag + "\n\n          ", html, count=1)
        if n:
            print(f"  + Separador añadido: {date}")

    # Limpiar day-sep legacy si quedan (los borramos porque ya tenemos date-divider)
    html = re.sub(
        r'\s*<div class="day-sep"[^>]*>.*?</div>\s*',
        "\n\n          ",
        html,
        flags=re.DOTALL
    )

    return html

def build_portada_block(items):
    """Genera el bloque HTML completo entre los marcadores PORTADA."""
    if not items:
        return None

    latest_date = items[0]["date"]
    today = [i for i in items if i["date"] == latest_date]

    portada = today[0]
    rest    = today[1:4]

    date_long = fecha_larga(latest_date)

    lines = []
    lines.append(f"""
        <div class="briefing-head">
          <div class="briefing-head-label">
            <span class="briefing-tag">Informativo</span>
            <span class="briefing-date">{date_long}</span>
          </div>
        </div>

        <a href="{portada['href']}" class="portada-card">
          <div class="portada-card-meta">
            <span class="cat portada-cat">{portada['cat']}</span>
            <span class="portada-card-date">{portada['date']}</span>
          </div>
          <h2 class="portada-card-titular">{portada['h3']}</h2>
          <p class="portada-card-lead">{portada['summary']}</p>
        </a>""")

    if rest:
        lines.append('\n\n        <div class="index-list" style="margin-top: 0;">\n')
        for item in rest:
            lines.append(f"""
          <a href="{item['href']}" class="index-item">
            <div>
              <span class="cat">{item['cat']}</span>
              <h3>{item['h3']}</h3>
              <p class="summary">{item['summary']}</p>
            </div>
            <span class="date">{item['date']}</span>
          </a>
""")
        lines.append("        </div>")

    return "".join(lines)

def update_index(index_html, portada_html):
    """Reemplaza el contenido entre <!-- PORTADA-START --> y <!-- PORTADA-END -->."""
    pattern = re.compile(
        r'(<!-- PORTADA-START -->).*?(<!-- PORTADA-END -->)',
        re.DOTALL
    )
    if not pattern.search(index_html):
        print("ERROR: Marcadores <!-- PORTADA-START/END --> no encontrados en index.html")
        sys.exit(1)
    return pattern.sub(r'\1' + portada_html + '\n\n        ' + r'\2', index_html)

def git_push(files, message):
    os.chdir(BASEDIR)
    subprocess.run(["git", "add"] + files, check=True)
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        capture_output=True, text=True
    )
    if not result.stdout.strip():
        print("Sin cambios que publicar.")
        return
    subprocess.run(["git", "commit", "-m", message], check=True)
    ssh_env = {**os.environ, "GIT_SSH_COMMAND": "ssh -p 443 -o Hostname=ssh.github.com"}
    subprocess.run(["git", "push", "origin", "main"], env=ssh_env, check=True)
    print("✓ Publicado en producción.")

def main():
    with open(NOTICIAS, "r", encoding="utf-8") as f:
        noticias_html = f.read()
    with open(INDEX, "r", encoding="utf-8") as f:
        index_html = f.read()

    items = parse_items(noticias_html)
    if not items:
        print("No se encontraron artículos en noticias.html")
        sys.exit(0)

    latest_date = items[0]["date"]
    today_count = len([i for i in items if i["date"] == latest_date])
    print(f"Fecha más reciente: {latest_date} ({today_count} artículos)")

    # --- Separadores en noticias.html ---
    noticias_fixed = ensure_date_dividers(noticias_html, items)
    noticias_changed = (noticias_fixed != noticias_html)

    # --- Portada en index.html ---
    portada_html = build_portada_block(items)
    index_new = update_index(index_html, portada_html)
    index_changed = (index_new != index_html)

    if not noticias_changed and not index_changed:
        print("Todo ya está actualizado.")
        sys.exit(0)

    if DRY_RUN:
        print("[dry-run] Cambios detectados pero no aplicados.")
        if index_changed:   print("  · index.html se actualizaría")
        if noticias_changed: print("  · noticias.html se actualizaría")
        sys.exit(0)

    changed_files = []
    if noticias_changed:
        with open(NOTICIAS, "w", encoding="utf-8") as f:
            f.write(noticias_fixed)
        print("✓ noticias.html: separadores actualizados")
        changed_files.append("noticias.html")

    if index_changed:
        with open(INDEX, "w", encoding="utf-8") as f:
            f.write(index_new)
        print(f"✓ index.html: portada actualizada a {latest_date}")
        changed_files.append("index.html")

    if not NO_GIT:
        git_push(changed_files, f"Portada actualizada: {latest_date}")

if __name__ == "__main__":
    main()
