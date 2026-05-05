#!/usr/bin/env python3
"""
nuevo_articulo.py — HdD
Genera un artículo HTML completo a partir de un JSON de contenido.
Actualiza noticias.html y sitemap.xml automáticamente.

Uso:
  python3 nuevo_articulo.py articulo.json          # genera + git push
  python3 nuevo_articulo.py articulo.json --no-git # genera, no hace push
  python3 nuevo_articulo.py --schema               # muestra el esquema JSON

JSON esperado: ver --schema o SKILL-INFORMATIVO.md
"""

import json, re, sys, os, subprocess
from datetime import datetime

BASEDIR  = "/Users/pablorufas/Documents/Claude/Scheduled"
NO_GIT   = "--no-git" in sys.argv

MESES_ES = {1:"enero",2:"febrero",3:"marzo",4:"abril",5:"mayo",6:"junio",
            7:"julio",8:"agosto",9:"septiembre",10:"octubre",11:"noviembre",12:"diciembre"}

SCHEMA = {
  "slug": "nombre-slug-mes-2026",
  "fecha_display": "DD·MM·AA",
  "fecha_iso": "2026-MM-DD",
  "categoria": "Política · España",
  "tiempo": "12",
  "titular": "Titular del artículo (máx 15 palabras)",
  "lead": "Lead de 2-3 frases explicando qué pasó y qué aprenderá el lector.",
  "conceptos": [
    {"titulo": "Qué es X", "cuerpo": "Definición clara en 3-4 frases."},
    {"titulo": "Qué es Y", "cuerpo": "Definición clara en 3-4 frases."},
    {"titulo": "Qué es Z", "cuerpo": "Definición clara en 3-4 frases."}
  ],
  "hechos": "<p>Párrafo 1 con dato + fuente.</p><p>Párrafo 2.</p><p>Párrafo 3.</p>",
  "contexto": "<p>Contexto histórico/legal.</p><p>Por qué ocurre ahora.</p>",
  "motivaciones": [
    {"actor": "Actor 1", "incentivos": "Qué gana y qué pierde."},
    {"actor": "Actor 2", "incentivos": "Qué gana y qué pierde."},
    {"actor": "Actor 3", "incentivos": "Qué gana y qué pierde."}
  ],
  "medios": "<p>Cómo lo han contado los medios. Nombra medios concretos.</p>",
  "preguntas": [
    "¿Pregunta verificable 1?",
    "¿Pregunta verificable 2?",
    "¿Pregunta verificable 3?",
    "¿Pregunta verificable 4?"
  ],
  "pregunta_principal": "La pregunta más incómoda, sin respuesta fácil.",
  "nota_metodologica": "Fuentes consultadas el DD de mes de 2026: ...",
  "lee_tambien": [
    {"href": "articulo-1.html", "fecha": "DD·MM·AA", "titulo": "Título del artículo relacionado"},
    {"href": "articulo-2.html", "fecha": "DD·MM·AA", "titulo": "Título del artículo relacionado"},
    {"href": "articulo-3.html", "fecha": "DD·MM·AA", "titulo": "Título del artículo relacionado"}
  ],
  "card_titular": "Titular para noticias.html (puede ser igual o ligeramente diferente)",
  "card_summary": "Resumen de 1-2 frases para noticias.html."
}

def build_html(d):
    slug       = d["slug"]
    fecha_d    = d["fecha_display"]
    fecha_iso  = d["fecha_iso"]
    cat        = d["categoria"]
    tiempo     = d["tiempo"]
    titular    = d["titular"]
    lead       = d["lead"]
    url        = f"https://horadedespertar.org/{slug}.html"

    # Slide 2 — conceptos
    conceptos_html = ""
    for c in d["conceptos"]:
        conceptos_html += f"""
          <div class="didactic-box">
            <h4>{c['titulo']}</h4>
            <p>{c['cuerpo']}</p>
          </div>"""

    # Slide 3 — motivaciones
    motiv_html = ""
    for m in d["motivaciones"]:
        motiv_html += f"""
          <div class="actor-block">
            <span class="actor-name">{m['actor']}</span>
            <p>{m['incentivos']}</p>
          </div>"""

    # Slide 4 — preguntas
    preguntas_html = "\n".join(f"          <li>{p}</li>" for p in d["preguntas"])

    # Lee también
    lee_html = ""
    for lt in d.get("lee_tambien", []):
        lee_html += f"""
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
  <meta name="description" content="{lead[:160]}" />
  <link rel="canonical" href="{url}" />
  <meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1" />

  <meta property="og:type" content="article" />
  <meta property="og:site_name" content="Hora de Despertar" />
  <meta property="og:title" content="{titular} — HdD" />
  <meta property="og:description" content="{lead[:200]}" />
  <meta property="og:url" content="{url}" />
  <meta property="og:image" content="https://horadedespertar.org/assets/icons/icon-512.png" />
  <meta property="og:image:width" content="512" />
  <meta property="og:image:height" content="512" />

  <meta name="twitter:card" content="summary" />
  <meta name="twitter:site" content="@hdedespertar" />
  <meta name="twitter:title" content="{titular} — HdD" />
  <meta name="twitter:description" content="{lead[:200]}" />
  <meta name="twitter:image" content="https://horadedespertar.org/assets/icons/icon-512.png" />

  <link rel="stylesheet" href="assets/style.css" />

  <script async src="https://www.googletagmanager.com/gtag/js?id=G-RTLZFW7HGF"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){{dataLayer.push(arguments);}}
    gtag("js", new Date());
    gtag("config", "G-RTLZFW7HGF");
  </script>

  <link rel="manifest" href="/manifest.json" />
  <meta name="theme-color" content="#0a0a0a" />
  <meta name="mobile-web-app-capable" content="yes" />
  <meta name="apple-mobile-web-app-capable" content="yes" />
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
  <meta name="apple-mobile-web-app-title" content="HdD" />
  <link rel="apple-touch-icon" href="/assets/icons/icon-192.png" />

  <script src="https://cdn.onesignal.com/sdks/web/v16/OneSignalSDK.page.js" defer></script>
  <script>
    window.OneSignalDeferred = window.OneSignalDeferred || [];
    OneSignalDeferred.push(async function(OneSignal) {{
      await OneSignal.init({{ appId: "26a69bec-30c7-4e90-a6b7-24ffab2e5e90" }});
    }});
  </script>

  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "NewsArticle",
    "headline": "{titular}",
    "description": "{lead[:200]}",
    "datePublished": "{fecha_iso}",
    "dateModified": "{fecha_iso}",
    "author": {{"@type": "Organization", "name": "Redacción HdD"}},
    "publisher": {{
      "@type": "Organization",
      "name": "Hora de Despertar",
      "logo": {{"@type": "ImageObject", "url": "https://horadedespertar.org/assets/icons/icon-512.png"}}
    }},
    "mainEntityOfPage": {{"@type": "WebPage", "@id": "{url}"}}
  }}
  </script>
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    "itemListElement": [
      {{"@type": "ListItem", "position": 1, "name": "Inicio", "item": "https://horadedespertar.org/"}},
      {{"@type": "ListItem", "position": 2, "name": "Noticias", "item": "https://horadedespertar.org/noticias.html"}},
      {{"@type": "ListItem", "position": 3, "name": "{titular}", "item": "{url}"}}
    ]
  }}
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

    <div class="slides-view" id="slides-view">

      <!-- SLIDE 1 — PORTADA -->
      <section class="slide slide--cover" data-slide="0">
        <div class="slide-inner">
          <span class="slide-num">01 — 04</span>
          <span class="slide-label">La noticia</span>
          <div class="slide-cover-content">
            <span class="eyebrow">{cat}</span>
            <h1>{titular}</h1>
            <p class="lead">{lead}</p>
            <div class="slide-meta-row">
              <span class="slide-meta-date">{fecha_d}</span>
              <span class="slide-meta-sep">·</span>
              <span class="slide-meta-tiempo">{tiempo} min de lectura</span>
              <span class="slide-meta-sep">·</span>
              <span class="slide-meta-autor">Redacción HdD</span>
            </div>
          </div>
        </div>
      </section>

      <!-- SLIDE 2 — CONCEPTOS -->
      <section class="slide slide--concepts" data-slide="1">
        <div class="slide-inner">
          <span class="slide-num">02 — 04</span>
          <span class="slide-label">Para entenderlo</span>
          <h2>Tres conceptos clave</h2>
          <div class="concepts-grid">{conceptos_html}
          </div>
        </div>
      </section>

      <!-- SLIDE 3 — DESARROLLO -->
      <section class="slide slide--development" data-slide="2">
        <div class="slide-inner">
          <span class="slide-num">03 — 04</span>
          <span class="slide-label">El análisis</span>

          <div class="dev-section">
            <h3>Los hechos</h3>
            {d['hechos']}
          </div>

          <div class="dev-section">
            <h3>El contexto</h3>
            {d['contexto']}
          </div>

          <div class="dev-section">
            <h3>Las motivaciones posibles</h3>
            <p class="motivaciones-disclaimer">Los incentivos que siguen son observables a partir de posiciones públicas documentadas. No son intenciones confirmadas.</p>
            {motiv_html}
          </div>
        </div>
      </section>

      <!-- SLIDE 4 — ANÁLISIS -->
      <section class="slide slide--analysis" data-slide="3">
        <div class="slide-inner">
          <span class="slide-num">04 — 04</span>
          <span class="slide-label">Perspectiva</span>

          <div class="dev-section">
            <h3>Cómo lo han contado otros medios</h3>
            {d['medios']}
          </div>

          <div class="dev-section">
            <h3>Lo que queda abierto</h3>
            <ul class="open-questions">
{preguntas_html}
            </ul>
          </div>

          <div class="open-question">
            <span class="eyebrow">La pregunta</span>
            <p>{d['pregunta_principal']}</p>
          </div>

          <!-- LEE TAMBIÉN — ANTES de la nota metodológica -->
          <div class="lee-tambien">
            <span class="lee-tambien-label">Lee también en HdD</span>{lee_html}
          </div>

          <!-- NOTA METODOLÓGICA -->
          <div class="didactic-box" style="border-left-color: var(--accent); margin-top: 48px;">
            <span class="eyebrow" style="color: var(--accent);">Nota metodológica</span>
            <h4>Cómo verificamos este artículo</h4>
            <p>{d['nota_metodologica']} Errores o información adicional: <a href="mailto:redaccion@horadedespertar.org" style="color: var(--red);">redaccion@horadedespertar.org</a></p>
          </div>

        </div>
      </section>

    </div><!-- /slides-view -->

    <div class="slides-nav" id="slides-nav" role="navigation" aria-label="Navegación entre diapositivas">
      <button class="snav-btn" id="btn-prev" aria-label="Diapositiva anterior" disabled>←</button>
      <div class="snav-dots" id="snav-dots">
        <button class="snav-dot active" data-target="0" aria-label="Ir a diapositiva 1"></button>
        <button class="snav-dot" data-target="1" aria-label="Ir a diapositiva 2"></button>
        <button class="snav-dot" data-target="2" aria-label="Ir a diapositiva 3"></button>
        <button class="snav-dot" data-target="3" aria-label="Ir a diapositiva 4"></button>
      </div>
      <button class="snav-btn" id="btn-next" aria-label="Siguiente diapositiva">→</button>
    </div>

  </main>

  <footer class="site-footer">
    <div class="wrap">
      <div class="top">
        <div>
          <a href="index.html" class="logo logo-sm" aria-label="Hora de Despertar — Inicio"><span class="logo-led">HdD</span></a>
          <p class="tagline">Hora de Despertar. Periodismo didáctico para una sociedad que quiere pensar por sí misma.</p>
        </div>
        <div>
          <h5>Secciones</h5>
          <ul>
            <li><a href="noticias.html">Noticias</a></li>
            <li><a href="educacion.html">Educación</a></li>
            <li><a href="newsletter.html">Semanal</a></li>
            <li><a href="manifiesto.html">Manifiesto</a></li>
          </ul>
        </div>
        <div>
          <h5>Redacción</h5>
          <ul>
            <li><a href="manifiesto.html#metodo">Método</a></li>
            <li><a href="manifiesto.html#correcciones">Correcciones</a></li>
            <li><a href="manifiesto.html#contacto">Contacto</a></li>
            <li><a href="https://instagram.com/hdedespertar" target="_blank" rel="noopener noreferrer">@hdedespertar</a></li>
          </ul>
        </div>
        <div>
          <h5>Legal</h5>
          <ul>
            <li><a href="aviso-legal.html">Aviso legal</a></li>
            <li><a href="privacidad.html">Privacidad</a></li>
            <li><a href="cookies.html">Cookies</a></li>
          </ul>
        </div>
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

def update_noticias(slug, fecha, cat, titular, summary, tiempo):
    path = os.path.join(BASEDIR, "noticias.html")
    with open(path) as f:
        html = f.read()
    if f'{slug}.html' in html:
        print(f"  · {slug} ya está en noticias.html")
        return
    card = f"""
          <a href="{slug}.html" class="index-item">
            <span class="date">{fecha}</span>
            <div>
              <span class="cat">{cat}</span>
              <h3>{titular}</h3>
              <p class="summary">{summary}</p>
            </div>
            <span style="color: var(--ink-mute); font-size: 0.78rem;">{tiempo} min →</span>
          </a>
"""
    html = html.replace('<div class="index-list">', '<div class="index-list">' + card, 1)
    with open(path, "w") as f:
        f.write(html)
    print(f"  ✓ Tarjeta añadida en noticias.html")

def update_sitemap(slug, fecha_iso):
    path = os.path.join(BASEDIR, "sitemap.xml")
    with open(path) as f:
        xml = f.read()
    url = f"https://horadedespertar.org/{slug}.html"
    if url in xml:
        return
    entry = f"""  <url>
    <loc>{url}</loc>
    <lastmod>{fecha_iso}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>
"""
    xml = xml.replace("  <url>\n    <loc>https://horadedespertar.org/iran-trump", entry + "  <url>\n    <loc>https://horadedespertar.org/iran-trump", 1)
    with open(path, "w") as f:
        f.write(xml)
    print(f"  ✓ URL añadida en sitemap.xml")

def git_push(files, message):
    os.chdir(BASEDIR)
    subprocess.run(["git", "add"] + files, check=True)
    result = subprocess.run(["git", "diff", "--cached", "--name-only"], capture_output=True, text=True)
    if not result.stdout.strip():
        print("Sin cambios que publicar.")
        return
    subprocess.run(["git", "commit", "-m", message], check=True)
    ssh_env = {**os.environ, "GIT_SSH_COMMAND": "ssh -p 443 -o Hostname=ssh.github.com"}
    subprocess.run(["git", "push", "origin", "main"], env=ssh_env, check=True)
    print("✓ Publicado en producción.")

def main():
    if "--schema" in sys.argv:
        print(json.dumps(SCHEMA, ensure_ascii=False, indent=2))
        sys.exit(0)

    if len(sys.argv) < 2 or sys.argv[1].startswith("--"):
        print("Uso: python3 nuevo_articulo.py <archivo.json> [--no-git]")
        sys.exit(1)

    json_path = sys.argv[1]
    with open(json_path) as f:
        d = json.load(f)

    slug     = d["slug"]
    out_path = os.path.join(BASEDIR, f"{slug}.html")

    print(f"Generando: {slug}.html")
    html = build_html(d)

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  ✓ Archivo creado: {slug}.html")

    update_noticias(slug, d["fecha_display"], d["categoria"], d["card_titular"], d["card_summary"], d["tiempo"])
    update_sitemap(slug, d["fecha_iso"])

    # Validar
    result = subprocess.run(["python3", "check.py"], capture_output=True, text=True, cwd=BASEDIR)
    if "ERROR" in result.stdout:
        print("⚠ check.py encontró errores:")
        print(result.stdout)
    else:
        print("  ✓ check.py: 0 errores")

    if not NO_GIT:
        git_push([f"{slug}.html", "noticias.html", "sitemap.xml"],
                 f"Publicar: {d['card_titular'][:60]}")

if __name__ == "__main__":
    main()
