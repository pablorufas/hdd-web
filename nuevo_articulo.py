#!/usr/bin/env python3
"""
nuevo_articulo.py — HdD
Genera un artículo HTML completo desde JSON. Actualiza noticias.html y sitemap.xml.

Uso:
  python3 nuevo_articulo.py articulo.json          # genera + git push
  python3 nuevo_articulo.py articulo.json --no-git # genera, sin push
  python3 nuevo_articulo.py --schema               # muestra esquema JSON completo
"""

import json, re, sys, os, subprocess

BASEDIR = "/Users/pablorufas/Documents/Claude/Scheduled"
NO_GIT  = "--no-git" in sys.argv

MESES_ES = {1:"enero",2:"febrero",3:"marzo",4:"abril",5:"mayo",6:"junio",
            7:"julio",8:"agosto",9:"septiembre",10:"octubre",11:"noviembre",12:"diciembre"}

# ── SCHEMA ────────────────────────────────────────────────────────────────────
SCHEMA = {
  "_razonamiento": {
    "tema": "Por qué este tema merece cobertura hoy (impacto, novedad, interés público).",
    "extension": "Por qué este artículo tiene esta longitud (8-15 min según complejidad).",
    "conceptos_nivel": "Qué sabe un lector de 20 años sobre este tema y qué necesita explicado."
  },
  "slug": "nombre-slug-mes-2026",
  "fecha_display": "DD·MM·AA",
  "fecha_iso": "2026-MM-DD",
  "categoria": "Política · España",
  "tiempo": "12",
  "titular": "Titular directo, sin clickbait, máx 15 palabras.",
  "lead": "2-3 frases: qué pasó y qué aprenderá el lector.",
  "conceptos": [
    {
      "titulo": "Qué es X",
      "cuerpo": "Definición para alguien de 20 años. (1) qué es, (2) cómo funciona, (3) por qué importa aquí. 3-5 frases según complejidad."
    }
  ],
  "hechos": "<p>Párrafo con dato exacto + fuente. Cifras, nombres, fechas precisas.</p>",
  "contexto": "<p>Línea de tiempo y marco que el lector necesita. Por qué ocurre AHORA.</p>",
  "motivaciones": [
    {
      "actor": "Nombre del actor",
      "incentivos": "Qué gana y qué pierde en cada escenario. 'Tiene incentivo para X', nunca 'quiere X'."
    }
  ],
  "_motivaciones_nota": "Poner null si el tema es científico, cultural o sin actores con intereses claros.",
  "medios": "<p>Cómo lo cubren medios concretos. Qué enfocan y qué omiten.</p>",
  "_medios_nota": "Poner null si no hay cobertura diferenciada reseñable.",
  "preguntas": [
    "¿Pregunta concreta y verificable que el lector puede investigar?",
    "¿Otra pregunta?",
    "¿Otra?",
    "¿Qué pasa si X? (al menos una sobre consecuencias futuras)"
  ],
  "pregunta_principal": "La pregunta más incómoda. Sin respuesta fácil. Sin moralismo.",
  "nota_metodologica": "Fuentes verificadas consultadas el DD de mes de 2026: [lista]. Motivaciones son incentivos observables, no intenciones confirmadas.",
  "lee_tambien": [
    {"href": "articulo-existente.html", "fecha": "DD·MM·AA", "titulo": "Título exacto del artículo"},
    {"href": "articulo-existente-2.html", "fecha": "DD·MM·AA", "titulo": "Título exacto"},
    {"href": "articulo-existente-3.html", "fecha": "DD·MM·AA", "titulo": "Título exacto"}
  ],
  "card_titular": "Titular para noticias.html.",
  "card_summary": "Resumen 1-2 frases para noticias.html."
}

# ── VALIDACIÓN ────────────────────────────────────────────────────────────────
REQUIRED = ["slug","fecha_display","fecha_iso","categoria","tiempo","titular",
            "lead","conceptos","hechos","contexto","preguntas","pregunta_principal",
            "nota_metodologica","lee_tambien","card_titular","card_summary"]

def validate(d):
    errors = []

    # Campos obligatorios
    for f in REQUIRED:
        if f not in d or not d[f]:
            errors.append(f"Campo obligatorio vacío: {f}")

    # Slug limpio
    if d.get("slug") and re.search(r'[^a-z0-9\-]', d["slug"]):
        errors.append(f"slug con caracteres inválidos: {d['slug']}")

    # fecha_iso formato YYYY-MM-DD
    if d.get("fecha_iso") and not re.match(r'^\d{4}-\d{2}-\d{2}$', d["fecha_iso"]):
        errors.append(f"fecha_iso mal formateada: {d['fecha_iso']}")

    # Conceptos: mínimo 1, máximo 5
    c = d.get("conceptos", [])
    if not isinstance(c, list) or len(c) < 1:
        errors.append("conceptos: mínimo 1 elemento")
    for i, item in enumerate(c):
        if not item.get("titulo") or not item.get("cuerpo"):
            errors.append(f"concepto[{i}]: falta titulo o cuerpo")

    # Lee también: exactamente 3 links
    lt = d.get("lee_tambien", [])
    if len(lt) != 3:
        errors.append(f"lee_tambien: se requieren exactamente 3 (hay {len(lt)})")
    for i, item in enumerate(lt):
        if not item.get("href") or not item.get("fecha") or not item.get("titulo"):
            errors.append(f"lee_tambien[{i}]: falta href, fecha o titulo")
        # Verificar que el archivo existe
        href = item.get("href","")
        if href and not os.path.exists(os.path.join(BASEDIR, href)):
            errors.append(f"lee_tambien[{i}]: archivo no existe → {href}")

    # Motivaciones: si presente, mínimo 2 actores
    m = d.get("motivaciones")
    if m is not None and isinstance(m, list) and len(m) < 2:
        errors.append("motivaciones: si se incluye, mínimo 2 actores")

    # Preguntas: mínimo 3
    p = d.get("preguntas", [])
    if len(p) < 3:
        errors.append(f"preguntas: mínimo 3 (hay {len(p)})")

    # No tokens EDITAR sin reemplazar
    raw = json.dumps(d)
    if "EDITAR" in raw or "TODO" in raw or "XXXXX" in raw:
        errors.append("JSON contiene placeholders sin reemplazar (EDITAR/TODO/XXXXX)")

    # Slug no duplicado
    out = os.path.join(BASEDIR, f"{d.get('slug','')}.html")
    if os.path.exists(out):
        errors.append(f"Ya existe {d['slug']}.html — cambia el slug o elimina el archivo")

    return errors

# ── BUILD HTML ────────────────────────────────────────────────────────────────
def build_html(d):
    slug      = d["slug"]
    fecha_d   = d["fecha_display"]
    fecha_iso = d["fecha_iso"]
    cat       = d["categoria"]
    tiempo    = d["tiempo"]
    titular   = d["titular"]
    lead      = d["lead"]
    url       = f"https://horadedespertar.org/{slug}.html"
    lead_meta = re.sub(r'<[^>]+>', '', lead)[:200]

    # Conceptos
    conceptos_html = ""
    for c in d["conceptos"]:
        conceptos_html += f"""
          <div class="didactic-box">
            <h4>{c['titulo']}</h4>
            <p>{c['cuerpo']}</p>
          </div>"""

    # Motivaciones (opcional)
    motiv_html = ""
    motivaciones = d.get("motivaciones")
    if motivaciones:
        actores_html = ""
        for m in motivaciones:
            actores_html += f'\n              <p>\n                <span class="actor-name">{m["actor"]}</span>\n                {m["incentivos"]}\n              </p>'
        motiv_html = f"""

          <div class="slide-section">
            <h3>Las motivaciones posibles</h3>
            <p>Los incentivos que siguen son observables a partir de posiciones públicas. No son intenciones confirmadas.</p>{actores_html}
          </div>"""

    # Medios (opcional)
    medios_html = ""
    medios = d.get("medios")
    if medios:
        medios_html = f"""
          <div class="slide-section">
            <h3>Cómo lo han contado otros medios</h3>
            {medios}
          </div>
"""

    # Preguntas
    preguntas_html = "\n".join(f"          <li>{p}</li>" for p in d["preguntas"])

    # Lee también
    lee_links = ""
    for lt in d["lee_tambien"]:
        lee_links += f"""
            <a href="{lt['href']}" class="lee-tambien-link">
              <span class="lee-tambien-fecha">{lt['fecha']}</span>
              <span class="lee-tambien-titulo">{lt['titulo']}</span>
            </a>"""

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8" />
  <link rel="icon" type="image/png" sizes="32x32" href="/assets/icons/favicon-32.png" />
  <link rel="icon" type="image/png" sizes="16x16" href="/assets/icons/favicon-16.png" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{titular} — HdD</title>
  <meta name="description" content="{lead_meta}" />
  <link rel="canonical" href="{url}" />
  <meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1" />
  <meta property="og:type" content="article" />
  <meta property="og:site_name" content="Hora de Despertar" />
  <meta property="og:title" content="{titular} — HdD" />
  <meta property="og:description" content="{lead_meta}" />
  <meta property="og:url" content="{url}" />
  <meta property="og:image" content="https://horadedespertar.org/assets/icons/icon-512.png" />
  <meta property="og:image:width" content="512" />
  <meta property="og:image:height" content="512" />
  <meta name="twitter:card" content="summary" />
  <meta name="twitter:site" content="@hdedespertar" />
  <meta name="twitter:title" content="{titular} — HdD" />
  <meta name="twitter:description" content="{lead_meta}" />
  <meta name="twitter:image" content="https://horadedespertar.org/assets/icons/icon-512.png" />
  <link rel="stylesheet" href="assets/style.css" />
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-RTLZFW7HGF"></script>
  <script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag("js",new Date());gtag("config","G-RTLZFW7HGF");</script>
  <link rel="manifest" href="/manifest.json" />
  <meta name="theme-color" content="#0a0a0a" />
  <meta name="mobile-web-app-capable" content="yes" />
  <meta name="apple-mobile-web-app-capable" content="yes" />
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
  <meta name="apple-mobile-web-app-title" content="HdD" />
  <link rel="apple-touch-icon" href="/assets/icons/icon-192.png" />
  <script src="https://cdn.onesignal.com/sdks/web/v16/OneSignalSDK.page.js" defer></script>
  <script>window.OneSignalDeferred=window.OneSignalDeferred||[];OneSignalDeferred.push(async function(O){{await O.init({{appId:"26a69bec-30c7-4e90-a6b7-24ffab2e5e90"}});}});</script>
  <script type="application/ld+json">
  {{"@context":"https://schema.org","@type":"NewsArticle","headline":"{titular}","description":"{lead_meta}","datePublished":"{fecha_iso}","dateModified":"{fecha_iso}","author":{{"@type":"Organization","name":"Redacción HdD"}},"publisher":{{"@type":"Organization","name":"Hora de Despertar","logo":{{"@type":"ImageObject","url":"https://horadedespertar.org/assets/icons/icon-512.png"}}}},"mainEntityOfPage":{{"@type":"WebPage","@id":"{url}"}}}}
  </script>
  <script type="application/ld+json">
  {{"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[{{"@type":"ListItem","position":1,"name":"Inicio","item":"https://horadedespertar.org/"}},{{"@type":"ListItem","position":2,"name":"Noticias","item":"https://horadedespertar.org/noticias.html"}},{{"@type":"ListItem","position":3,"name":"{titular}","item":"{url}"}}]}}
  </script>
</head>
<body>
  <header class="site-header">
    <div class="wrap bar">
      <div class="brand-unit">
        <a href="index.html" class="logo logo-sm" aria-label="Hora de Despertar — Inicio"><span class="logo-led">HdD</span></a>
        <span class="header-clock logo-led" data-live-clock aria-label="Hora actual">--:--</span>
        <span class="header-site-name">Hora de Despertar</span>
      </div>
      <button class="nav-toggle" aria-label="Abrir menú" aria-expanded="false" aria-controls="main-nav">☰</button>
      <nav class="nav" id="main-nav">
        <a href="index.html">Inicio</a>
        <a href="noticias.html">Noticias</a>
        <a href="educacion.html">Educación</a>
        <a href="newsletter.html">Semanal</a>
        <a href="manifiesto.html">Manifiesto</a>
      </nav>
    </div>
  </header>

  <main>
    <a href="noticias.html" class="back-link">← Todas las noticias</a>

    <!-- Barra de modo de lectura -->
    <div class="reading-mode-bar">
      <div class="wrap bar--reading">
        <span class="reading-mode-label">Modo de lectura</span>
        <div class="reading-mode-btns">
          <button class="mode-btn is-active" data-mode="slides">▣ Diapositivas</button>
          <button class="mode-btn" data-mode="flow">≡ Texto completo</button>
        </div>
      </div>
    </div>

    <!-- Vista de diapositivas -->
    <div class="slides-view" id="slides-view">

      <!-- Barra de progreso -->
      <div class="slide-progress-bar" aria-hidden="true">
        <div class="slide-progress-fill"></div>
      </div>

      <section class="slide slide--cover" data-slide="0" aria-label="Portada">
        <div class="slide-inner">
          <span class="slide-num">01 — 04</span>
          <span class="slide-label">{cat}</span>
          <div class="slide-cover-content">
            <span class="eyebrow">{cat}</span>
            <h1>{titular}</h1>
            <p class="lead">{lead}</p>
            <div class="slide-meta-row">
              <span><strong>Noticias HdD</strong> · {fecha_d}</span>
              <span><strong>Autor</strong> · Redacción HdD</span>
            </div>
          </div>
        </div>
      </section>

      <section class="slide slide--concepts" data-slide="1" aria-label="Conceptos básicos">
        <div class="slide-inner">
          <span class="slide-num">02 — 04</span>
          <span class="slide-label">Antes de leer</span>
          <h2>Lo que necesitas saber primero</h2>
          <div class="concepts-grid">{conceptos_html}
          </div>
        </div>
      </section>

      <section class="slide slide--development" data-slide="2" aria-label="Desarrollo">
        <div class="slide-inner">
          <span class="slide-num">03 — 04</span>
          <span class="slide-label">La noticia</span>
          <h2>{d['titular']}</h2>

          <div class="slide-section">
            <h3>Los hechos</h3>
            {d['hechos']}
          </div>

          <div class="slide-section">
            <h3>El contexto</h3>
            {d['contexto']}
          </div>{motiv_html}

        </div>
      </section>

      <section class="slide slide--analysis" data-slide="3" aria-label="Análisis">
        <div class="slide-inner">
          <span class="slide-num">04 — 04</span>
          <span class="slide-label">Análisis</span>
          <h2>Lo que los datos no dicen solos</h2>
{medios_html}
          <div class="slide-section">
            <h3>Lo que queda abierto</h3>
            <ul>
{preguntas_html}
            </ul>
          </div>

          <div class="open-question">
            <span class="eyebrow">La pregunta</span>
            <p>{d['pregunta_principal']}</p>
          </div>

          <!-- LEE TAMBIÉN — NO mover. Debe estar ANTES de la nota metodológica -->
          <div class="lee-tambien">
            <span class="lee-tambien-label">Lee también en HdD</span>{lee_links}
          </div>

          <!-- NOTA METODOLÓGICA — obligatoria, siempre al final -->
          <div class="didactic-box" style="border-left-color: var(--accent); margin-top: 48px;">
            <span class="eyebrow" style="color: var(--accent);">Nota metodológica</span>
            <h4>Cómo verificamos este artículo</h4>
            <p>{d['nota_metodologica']} Errores o información adicional: <a href="mailto:redaccion@horadedespertar.org" style="color:var(--red);">redaccion@horadedespertar.org</a></p>
          </div>

          <a href="noticias.html" class="back-link">← Todas las noticias</a>

        </div>
      </section>

      <!-- Nav de diapositivas -->
      <nav class="slide-nav" aria-label="Navegación de diapositivas">
        <button class="slide-nav__btn slide-nav__btn--prev" aria-label="Diapositiva anterior" disabled>←</button>
        <div class="slide-dots" role="tablist" aria-label="Diapositivas"></div>
        <button class="slide-nav__btn slide-nav__btn--next" aria-label="Siguiente diapositiva">→</button>
        <span class="slide-counter" aria-live="polite" aria-atomic="true">1/4</span>
      </nav>

    </div><!-- /slides-view -->

  </main>

  <footer class="site-footer">
    <div class="wrap">
      <div class="top">
        <div>
          <a href="index.html" class="logo logo-sm" aria-label="Hora de Despertar — Inicio"><span class="logo-led">HdD</span></a>
          <p class="tagline">Hora de Despertar. Periodismo didáctico para una sociedad que quiere pensar por sí misma.</p>
        </div>
        <div><h5>Secciones</h5><ul><li><a href="noticias.html">Noticias</a></li><li><a href="educacion.html">Educación</a></li><li><a href="newsletter.html">Semanal</a></li><li><a href="manifiesto.html">Manifiesto</a></li></ul></div>
        <div><h5>Redacción</h5><ul><li><a href="manifiesto.html#metodo">Método</a></li><li><a href="manifiesto.html#correcciones">Correcciones</a></li><li><a href="manifiesto.html#contacto">Contacto</a></li><li><a href="https://instagram.com/hdedespertar" target="_blank" rel="noopener noreferrer">@hdedespertar</a></li></ul></div>
        <div><h5>Legal</h5><ul><li><a href="aviso-legal.html">Aviso legal</a></li><li><a href="privacidad.html">Privacidad</a></li><li><a href="cookies.html">Cookies</a></li></ul></div>
      </div>
      <div class="bottom">
        <span>© 2026 Hora de Despertar</span>
        <span>Hecho con rigor. Leído con criterio.</span>
      </div>
    </div>
  </footer>

  <script src="assets/script.js?v=2"></script>
</body>
</html>"""

# ── HELPERS ───────────────────────────────────────────────────────────────────
def update_noticias(slug, fecha, cat, titular, summary, tiempo):
    path = os.path.join(BASEDIR, "noticias.html")
    with open(path) as f: html = f.read()
    if f'{slug}.html' in html:
        print(f"  · {slug} ya está en noticias.html"); return
    card = f'\n          <a href="{slug}.html" class="index-item">\n            <span class="date">{fecha}</span>\n            <div>\n              <span class="cat">{cat}</span>\n              <h3>{titular}</h3>\n              <p class="summary">{summary}</p>\n            </div>\n            <span style="color: var(--ink-mute); font-size: 0.78rem;">{tiempo} min →</span>\n          </a>\n'
    html = html.replace('<div class="index-list">', '<div class="index-list">' + card, 1)
    with open(path, "w") as f: f.write(html)
    print("  ✓ Tarjeta añadida en noticias.html")

def update_sitemap(slug, fecha_iso):
    path = os.path.join(BASEDIR, "sitemap.xml")
    with open(path) as f: xml = f.read()
    url = f"https://horadedespertar.org/{slug}.html"
    if url in xml: return
    entry = f"  <url>\n    <loc>{url}</loc>\n    <lastmod>{fecha_iso}</lastmod>\n    <changefreq>monthly</changefreq>\n    <priority>0.8</priority>\n  </url>\n"
    # Insertar después de la primera URL (homepage)
    xml = re.sub(r'(</url>\n)', r'\1' + entry, xml, count=1)
    with open(path, "w") as f: f.write(xml)
    print("  ✓ URL añadida en sitemap.xml")

def git_push(files, message):
    os.chdir(BASEDIR)
    subprocess.run(["git", "add"] + files, check=True)
    r = subprocess.run(["git", "diff", "--cached", "--name-only"], capture_output=True, text=True)
    if not r.stdout.strip(): print("Sin cambios que publicar."); return
    subprocess.run(["git", "commit", "-m", message], check=True)
    env = {**os.environ, "GIT_SSH_COMMAND": "ssh -p 443 -o Hostname=ssh.github.com"}
    subprocess.run(["git", "push", "origin", "main"], env=env, check=True)
    print("✓ Publicado en producción.")

# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    if "--schema" in sys.argv:
        print(json.dumps(SCHEMA, ensure_ascii=False, indent=2)); sys.exit(0)

    if len(sys.argv) < 2 or sys.argv[1].startswith("--"):
        print("Uso: python3 nuevo_articulo.py <archivo.json> [--no-git]"); sys.exit(1)

    with open(sys.argv[1]) as f:
        d = json.load(f)

    # Validación pre-vuelo
    errors = validate(d)
    if errors:
        print("✗ JSON inválido. Corrige antes de continuar:")
        for e in errors: print(f"  · {e}")
        sys.exit(1)

    slug = d["slug"]
    print(f"Generando: {slug}.html")

    html = build_html(d)
    out  = os.path.join(BASEDIR, f"{slug}.html")
    with open(out, "w", encoding="utf-8") as f: f.write(html)
    print(f"  ✓ Archivo creado")

    update_noticias(slug, d["fecha_display"], d["categoria"], d["card_titular"], d["card_summary"], d["tiempo"])
    update_sitemap(slug, d["fecha_iso"])

    # Validar con check.py
    r = subprocess.run(["python3", "check.py"], capture_output=True, text=True, cwd=BASEDIR)
    lines = [l for l in r.stdout.splitlines() if slug in l or "ERROR" in l]
    if any("ERROR" in l for l in lines):
        print("⚠ check.py encontró errores en este artículo:")
        for l in lines: print(f"  {l}")
        sys.exit(1)
    else:
        print("  ✓ check.py: sin errores")

    if not NO_GIT:
        git_push([f"{slug}.html", "noticias.html", "sitemap.xml"],
                 f"Publicar: {d['card_titular'][:70]}")

if __name__ == "__main__":
    main()
