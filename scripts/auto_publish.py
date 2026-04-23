#!/usr/bin/env python3
"""
HdD — Publicador automático
Busca noticias, selecciona las mejores, escribe artículos con Claude y publica.
Corre 4 veces al día via GitHub Actions.
"""

import os, re, json, subprocess, textwrap, time, sys
from datetime import date, datetime
from pathlib import Path
import requests
import feedparser
from bs4 import BeautifulSoup
import anthropic

# ─────────────────────────────────────────────
# CONFIGURACIÓN
# ─────────────────────────────────────────────
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
NEWSAPI_KEY   = os.environ.get("NEWSAPI_KEY", "")
REPO          = Path(os.environ.get("GITHUB_WORKSPACE", "."))
MAX_ARTICULOS = 6   # Artículos por ejecución (ajusta según presupuesto API)

FUENTES_RSS = [
    # Nacionales
    "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/portada",
    "https://www.europapress.es/rss/rss.aspx",
    "https://www.eldiario.es/rss/",
    "https://www.publico.es/rss/",
    "https://www.20minutos.es/rss/nacional/",
    "https://www.rtve.es/api/noticias.rss",
    # Economía
    "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/seccion/economia/portada",
    "https://www.expansion.com/rss/economia.xml",
    # Internacional desde España
    "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/seccion/internacional/portada",
    # Cataluña / territorios
    "https://www.lavanguardia.com/rss/home.xml",
]

MESES_ES = {
    1:"ENE",2:"FEB",3:"MAR",4:"ABR",5:"MAY",6:"JUN",
    7:"JUL",8:"AGO",9:"SEP",10:"OCT",11:"NOV",12:"DIC"
}

# ─────────────────────────────────────────────
# 1. RECOPILACIÓN DE NOTICIAS
# ─────────────────────────────────────────────

def obtener_noticias_rss() -> list[dict]:
    """Recoge titulares recientes de las fuentes RSS."""
    noticias = []
    for url in FUENTES_RSS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:6]:
                noticias.append({
                    "titulo":  entry.get("title","").strip(),
                    "resumen": BeautifulSoup(
                                   entry.get("summary",""), "lxml"
                               ).get_text()[:400].strip(),
                    "url":     entry.get("link",""),
                    "fuente":  feed.feed.get("title", url),
                    "fecha":   entry.get("published",""),
                })
        except Exception as e:
            print(f"[RSS] Error en {url}: {e}")
    return noticias


def obtener_noticias_api() -> list[dict]:
    """Busca noticias recientes con NewsAPI (complementa RSS)."""
    if not NEWSAPI_KEY:
        return []
    try:
        r = requests.get(
            "https://newsapi.org/v2/top-headlines",
            params={"country":"es","pageSize":30,"apiKey":NEWSAPI_KEY},
            timeout=10,
        )
        data = r.json()
        return [
            {
                "titulo":  a["title"] or "",
                "resumen": a.get("description","") or "",
                "url":     a.get("url",""),
                "fuente":  a.get("source",{}).get("name","NewsAPI"),
                "fecha":   a.get("publishedAt",""),
            }
            for a in data.get("articles",[])
            if a.get("title")
        ]
    except Exception as e:
        print(f"[NewsAPI] Error: {e}")
        return []


def scrape_articulo(url: str, max_chars=3000) -> str:
    """Extrae el texto principal de un artículo. Silencia errores."""
    try:
        r = requests.get(url, timeout=8, headers={"User-Agent":"HdD-Bot/1.0"})
        soup = BeautifulSoup(r.text, "lxml")
        for tag in soup(["script","style","nav","footer","aside","header"]):
            tag.decompose()
        # Buscar contenido principal
        for selector in ["article", "[role='main']", "main", ".article-body", ".story"]:
            bloque = soup.select_one(selector)
            if bloque:
                return bloque.get_text(" ", strip=True)[:max_chars]
        return soup.get_text(" ", strip=True)[:max_chars]
    except:
        return ""


# ─────────────────────────────────────────────
# 2. SELECCIÓN CON CLAUDE
# ─────────────────────────────────────────────

SELECCION_PROMPT = """\
Eres el editor de HdD (Hora de Despertar), un medio de periodismo didáctico español.
Hoy es {hoy}.

HdD publica análisis que:
- Van más allá del titular: buscan el fondo real, los intereses económicos ocultos, el contexto histórico
- Explican conceptos que el lector necesita para entender la noticia
- Analizan motivaciones de cada actor (incentivos observables, no intenciones)
- Cubren: política española e internacional, economía, asuntos sociales estructurales
- NO publican: deportes, farándula, sucesos menores, cotilleo, noticias sin análisis posible

Noticias disponibles:
{noticias}

Selecciona entre {min_art} y {max_art} historias con mayor potencial para HdD.
Para cada una dame:
- num: número de la historia
- razon: por qué merece un artículo HdD (1 frase)
- angulo: el ángulo específico que otros medios NO están contando
- categoria: categoría principal (Política, Economía, Social, Internacional, Historia)
- subcategoria: segunda categoría o tipo (Análisis, Energía, Social, etc.)
- minutos: tiempo estimado de lectura (7-12)

Responde SOLO con JSON válido, sin texto antes ni después:
{{"selected":[{{"num":1,"razon":"...","angulo":"...","categoria":"...","subcategoria":"...","minutos":9}}]}}
"""

def seleccionar_noticias(noticias: list[dict], cliente: anthropic.Anthropic) -> list[dict]:
    """Pide a Claude que seleccione las mejores historias para HdD."""
    texto_noticias = "\n\n".join(
        f"HISTORIA {i+1}:\nTítulo: {n['titulo']}\nFuente: {n['fuente']}\nResumen: {n['resumen']}"
        for i, n in enumerate(noticias[:50])
    )
    hoy = datetime.now().strftime("%A, %d de %B de %Y")

    prompt = SELECCION_PROMPT.format(
        hoy=hoy,
        noticias=texto_noticias,
        min_art=3,
        max_art=MAX_ARTICULOS,
    )

    try:
        respuesta = cliente.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=1200,
            messages=[{"role":"user","content":prompt}],
        )
    except anthropic.BadRequestError as e:
        if "credit balance is too low" in str(e):
            print("[Selección] Sin créditos en la cuenta Anthropic. Añade créditos en console.anthropic.com/settings/billing")
            sys.exit(0)
        raise
    except anthropic.AuthenticationError:
        print("[Selección] ANTHROPIC_API_KEY inválida o expirada.")
        sys.exit(1)
    except anthropic.APIStatusError as e:
        print(f"[Selección] Error de API Anthropic ({e.status_code}): {e.message}")
        sys.exit(1)

    try:
        data = json.loads(respuesta.content[0].text)
        seleccionadas = []
        for s in data.get("selected",[]):
            idx = s["num"] - 1
            if 0 <= idx < len(noticias):
                n = noticias[idx].copy()
                n["angulo"]      = s.get("angulo","")
                n["categoria"]   = s.get("categoria","Política")
                n["subcategoria"]= s.get("subcategoria","Análisis")
                n["minutos"]     = s.get("minutos", 9)
                seleccionadas.append(n)
        return seleccionadas
    except Exception as e:
        print(f"[Selección] Error parseando JSON: {e}\n{respuesta.content[0].text[:300]}")
        return noticias[:3]


# ─────────────────────────────────────────────
# 3. ESCRITURA DE ARTÍCULOS CON CLAUDE
# ─────────────────────────────────────────────

ESCRITURA_PROMPT = """\
Eres el redactor de HdD (Hora de Despertar). Escribe un artículo completo en HTML siguiendo la metodología y voz editorial de HdD.

METODOLOGÍA HdD:
- Slide 1 (Portada): eyebrow con categoría, titular directo sin clickbait, lead de 2-3 frases que resumen el fondo real
- Slide 2 (Conceptos): 2-3 cajas didácticas explicando conceptos clave que el lector necesita. Cada caja: eyebrow + h4 + párrafo de 3-5 frases. Sin jerga innecesaria.
- Slide 3 (Desarrollo): Los hechos verificables, el contexto previo que importa, y las motivaciones por actor (incentivos observables, NO intenciones ocultas). Un bloque <p><span class="actor-name">Nombre</span> ... </p> por actor.
- Slide 4 (Análisis): Cómo lo han contado otros medios (con crítica honesta), qué nadie está preguntando, blockquote con la frase que resume el análisis, preguntas abiertas, nota metodológica con fuentes.

VOZ EDITORIAL:
- Tono directo, sin tecnicismos innecesarios
- Habla de tú al lector, hace preguntas directas
- Con política: más duro, igual con todos los partidos
- Con economía: más didáctico, con ejemplos concretos
- No atribuye intenciones: expone incentivos observables
- Va MÁS ALLÁ del titular: intereses económicos detrás, contexto histórico, quién gana y quién pierde
- Busca lo que otros medios no están contando

DATOS DEL ARTÍCULO:
Título de la noticia original: {titulo}
Fuente: {fuente}
Resumen disponible: {resumen}
Texto completo recuperado: {texto_completo}
Ángulo editorial HdD: {angulo}
Categoría: {categoria} · {subcategoria}
Fecha de hoy: {fecha_hoy}

INSTRUCCIONES HTML:
- Usa EXACTAMENTE esta estructura de slides. No añadas ni quites slides.
- Rellena TODO el contenido. No dejes placeholders.
- Las motivaciones deben incluir mínimo 3 actores relevantes.
- El análisis debe mencionar cómo lo cubren medios de distinto signo.
- La nota metodológica debe citar fuentes reales (las que conoces del tema).
- El slug del artículo debe ser descriptivo: palabras-clave-fecha.html
- slide-num: "01 — 04", "02 — 04", etc.

Devuelve SOLO el HTML completo del artículo (desde <!DOCTYPE html> hasta </html>).
No añadas explicaciones fuera del HTML.
El slide counter al final debe decir: 1/4

ESTRUCTURA DE REFERENCIA (rellena con contenido real):
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>TITULAR BREVE — HdD</title>
  <meta name="description" content="DESCRIPCIÓN 150 CHARS" />
  <link rel="canonical" href="https://horadedespertar.org/SLUG.html" />
  <meta property="og:type" content="article" />
  <meta property="og:site_name" content="Hora de Despertar" />
  <meta property="og:title" content="TITULAR — HdD" />
  <meta property="og:description" content="DESCRIPCIÓN CORTA" />
  <meta property="og:url" content="https://horadedespertar.org/SLUG.html" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:site" content="@hdedespertar" />
  <meta name="twitter:title" content="TITULAR — HdD" />
  <meta name="twitter:description" content="DESCRIPCIÓN CORTA" />
  <link rel="stylesheet" href="assets/style.css" />
</head>
<body>
  <header class="site-header">
    <div class="wrap bar">
      <div class="brand-unit">
        <a href="index.html" class="logo logo-sm" aria-label="Hora de Despertar — Inicio"><span class="logo-led">HdD</span></a>
        <span class="header-clock logo-led" data-live-clock aria-label="Hora actual">--:--</span>
      </div>
      <button class="nav-toggle" aria-label="Abrir menú" aria-expanded="false" aria-controls="main-nav">☰</button>
      <nav class="nav" id="main-nav">
        <a href="index.html">Inicio</a>
        <a href="manifiesto.html">Manifiesto</a>
        <a href="noticias.html" class="active">Noticias</a>
        <a href="educacion.html">Educación</a>
        <a href="newsletter.html">Semanal</a>
      </nav>
    </div>
  </header>
  <main>
    <div class="reading-mode-bar">
      <div class="wrap bar--reading">
        <span class="reading-mode-label">Modo de lectura</span>
        <div class="reading-mode-btns">
          <button class="mode-btn is-active" data-mode="slides">▣ Diapositivas</button>
          <button class="mode-btn" data-mode="flow">≡ Texto completo</button>
        </div>
      </div>
    </div>
    <div class="slides-view" id="slides-view">
      <div class="slide-progress-bar" aria-hidden="true"><div class="slide-progress-fill"></div></div>
      <section class="slide slide--cover" data-slide="0" aria-label="Portada">
        <div class="slide-inner">
          <span class="slide-num">01 — 04</span>
          <span class="slide-label">CATEGORIA · SUBCATEGORIA</span>
          <h1>TITULAR COMPLETO</h1>
          <p class="lead">LEAD DE 2-3 FRASES</p>
          <div class="slide-meta-row">
            <span><strong>Publicado</strong> · DD MMM AAAA</span>
            <span><strong>Lectura</strong> · X min</span>
            <span><strong>Autor</strong> · Redacción HdD</span>
          </div>
        </div>
      </section>
      <section class="slide slide--concepts" data-slide="1" aria-label="Conceptos básicos">
        <div class="slide-inner">
          <span class="slide-num">02 — 04</span>
          <span class="slide-label">Antes de leer</span>
          <h2>TÍTULO DE LA SECCIÓN DE CONCEPTOS</h2>
          <div class="didactic-box">
            <span class="eyebrow">Concepto</span>
            <h4>NOMBRE DEL CONCEPTO</h4>
            <p>EXPLICACIÓN EN 3-5 FRASES SIN JERGA</p>
          </div>
          <!-- repite didactic-box para cada concepto adicional -->
        </div>
      </section>
      <section class="slide slide--development" data-slide="2" aria-label="Desarrollo">
        <div class="slide-inner">
          <span class="slide-num">03 — 04</span>
          <span class="slide-label">La noticia</span>
          <h2>TÍTULO DESCRIPTIVO DEL DESARROLLO</h2>
          <div class="slide-section">
            <h3>Los hechos</h3>
            <p>HECHOS VERIFICABLES CON FECHAS Y CIFRAS</p>
          </div>
          <div class="slide-section">
            <h3>El contexto</h3>
            <p>QUÉ PASABA ANTES. POR QUÉ IMPORTA AHORA</p>
          </div>
          <div class="slide-section">
            <h3>Las motivaciones posibles</h3>
            <p><span class="actor-name">Actor 1</span> INCENTIVO OBSERVABLE</p>
            <p><span class="actor-name">Actor 2</span> INCENTIVO OBSERVABLE</p>
            <p><span class="actor-name">Actor 3</span> INCENTIVO OBSERVABLE</p>
          </div>
        </div>
      </section>
      <section class="slide slide--analysis" data-slide="3" aria-label="Análisis">
        <div class="slide-inner">
          <span class="slide-num">04 — 04</span>
          <span class="slide-label">Análisis</span>
          <h2>TÍTULO DEL ANÁLISIS</h2>
          <div class="slide-section">
            <h3>Cómo lo han contado otros medios</h3>
            <p>COMPARATIVA HONESTA DE COBERTURAS</p>
            <blockquote>FRASE QUE RESUME EL ANÁLISIS</blockquote>
          </div>
          <div class="slide-section">
            <h3>Lo que queda abierto</h3>
            <ul>
              <li>PREGUNTA VERIFICABLE 1</li>
              <li>PREGUNTA VERIFICABLE 2</li>
              <li>PREGUNTA VERIFICABLE 3</li>
            </ul>
          </div>
          <div class="didactic-box" style="border-left-color: var(--accent); margin-top: 48px;">
            <span class="eyebrow" style="color: var(--accent);">Nota metodológica</span>
            <h4>Cómo verificamos este artículo</h4>
            <p>Fuentes: LISTA DE FUENTES CON FECHA. Las motivaciones son incentivos observables, no intenciones confirmadas. Errores: <a href="mailto:redaccion@horadedespertar.org" style="color: var(--red);">redaccion@horadedespertar.org</a></p>
          </div>
          <a href="noticias.html" class="back-link">← Todas las noticias</a>
        </div>
      </section>
      <nav class="slide-nav" aria-label="Navegación de diapositivas">
        <button class="slide-nav__btn slide-nav__btn--prev" aria-label="Diapositiva anterior" disabled>←</button>
        <div class="slide-dots" role="tablist" aria-label="Diapositivas"></div>
        <button class="slide-nav__btn slide-nav__btn--next" aria-label="Siguiente diapositiva">→</button>
        <span class="slide-counter" aria-live="polite" aria-atomic="true">1/4</span>
      </nav>
    </div>
  </main>
  <footer class="site-footer">
    <div class="wrap">
      <div class="top">
        <div><a href="index.html" class="logo logo-sm" aria-label="Hora de Despertar — Inicio"><span class="logo-led">HdD</span></a><p class="tagline">Hora de Despertar. Periodismo didáctico para una sociedad que quiere pensar por sí misma.</p></div>
        <div><h5>Secciones</h5><ul><li><a href="noticias.html">Noticias</a></li><li><a href="educacion.html">Educación</a></li><li><a href="newsletter.html">Semanal</a></li><li><a href="manifiesto.html">Manifiesto</a></li></ul></div>
        <div><h5>Redacción</h5><ul><li><a href="manifiesto.html#metodo">Método</a></li><li><a href="manifiesto.html#correcciones">Correcciones</a></li><li><a href="manifiesto.html#contacto">Contacto</a></li><li><a href="https://instagram.com/hdedespertar" target="_blank" rel="noopener noreferrer">@hdedespertar</a></li></ul></div>
        <div><h5>Legal</h5><ul><li><a href="aviso-legal.html">Aviso legal</a></li><li><a href="privacidad.html">Privacidad</a></li><li><a href="cookies.html">Cookies</a></li></ul></div>
      </div>
      <div class="bottom"><span>© 2026 Hora de Despertar</span><span>Hecho con rigor. Leído con criterio.</span></div>
    </div>
  </footer>
  <script src="assets/script.js"></script>
</body>
</html>
"""

def generar_slug(titulo: str, fecha: date) -> str:
    """Crea un slug limpio para el nombre de archivo."""
    slug = titulo.lower()
    slug = re.sub(r'[áàä]','a', slug)
    slug = re.sub(r'[éèë]','e', slug)
    slug = re.sub(r'[íìï]','i', slug)
    slug = re.sub(r'[óòö]','o', slug)
    slug = re.sub(r'[úùü]','u', slug)
    slug = re.sub(r'[ñ]','n', slug)
    slug = re.sub(r'[^a-z0-9\s-]','', slug)
    slug = re.sub(r'\s+','-', slug.strip())
    slug = re.sub(r'-+','-', slug)
    slug = slug[:60].rstrip('-')
    return f"{slug}-{fecha.strftime('%m-%Y')}"


def extraer_slug_del_html(html: str) -> str | None:
    """Extrae el slug del canonical link que Claude pone en el HTML."""
    match = re.search(r'horadedespertar\.org/([^"]+\.html)', html)
    return match.group(1) if match else None


def escribir_articulo(noticia: dict, cliente: anthropic.Anthropic) -> dict | None:
    """Llama a Claude para escribir el HTML completo de un artículo."""
    # Intentar obtener texto completo del artículo fuente
    texto_completo = ""
    if noticia.get("url"):
        texto_completo = scrape_articulo(noticia["url"])
        print(f"  → Texto obtenido: {len(texto_completo)} caracteres")

    hoy = datetime.now()
    fecha_str = f"{hoy.day} {MESES_ES[hoy.month]} {hoy.year}"

    prompt = ESCRITURA_PROMPT.format(
        titulo         = noticia["titulo"],
        fuente         = noticia["fuente"],
        resumen        = noticia["resumen"],
        texto_completo = texto_completo or "(no disponible — usa tu conocimiento del tema)",
        angulo         = noticia.get("angulo",""),
        categoria      = noticia.get("categoria","Política"),
        subcategoria   = noticia.get("subcategoria","Análisis"),
        fecha_hoy      = fecha_str,
    )

    try:
        respuesta = cliente.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=6000,
            messages=[{"role":"user","content":prompt}],
        )
        html = respuesta.content[0].text.strip()

        # Extraer o generar slug
        slug = extraer_slug_del_html(html)
        if not slug:
            slug = generar_slug(noticia["titulo"], hoy.date()) + ".html"

        # Extraer titular para la tarjeta
        titulo_match = re.search(r'<h1>(.*?)</h1>', html, re.DOTALL)
        titular = BeautifulSoup(titulo_match.group(1), "lxml").get_text().strip() if titulo_match else noticia["titulo"]

        lead_match = re.search(r'<p class="lead">(.*?)</p>', html, re.DOTALL)
        lead = BeautifulSoup(lead_match.group(1), "lxml").get_text().strip()[:200] if lead_match else ""

        return {
            "slug":      slug,
            "html":      html,
            "titular":   titular,
            "lead":      lead,
            "categoria": noticia.get("categoria","Política"),
            "minutos":   noticia.get("minutos", 9),
            "fecha_str": fecha_str,
            "fecha_obj": hoy.date(),
        }
    except Exception as e:
        print(f"  [Error escritura] {e}")
        return None


# ─────────────────────────────────────────────
# 4. ACTUALIZACIÓN DE noticias.html
# ─────────────────────────────────────────────

def tarjeta_html(art: dict) -> str:
    """Genera el HTML de una tarjeta para noticias.html."""
    d = art["fecha_obj"]
    fecha_corta = f"{d.day:02d}·{d.month:02d}·{str(d.year)[2:]}"
    resumen = art["lead"][:180] + ("…" if len(art["lead"]) > 180 else "")
    return textwrap.dedent(f"""\
          <a href="{art['slug']}" class="index-item">
            <span class="date">{fecha_corta}</span>
            <div>
              <span class="cat">{art['categoria']}</span>
              <h3>{art['titular']}</h3>
              <p class="summary">{resumen}</p>
            </div>
            <span style="color: var(--ink-mute); font-size: 0.78rem;">{art['minutos']} min →</span>
          </a>""")


def actualizar_noticias_html(articulos: list[dict]):
    """Inserta las nuevas tarjetas al principio de noticias.html."""
    ruta = REPO / "noticias.html"
    contenido = ruta.read_text(encoding="utf-8")

    nuevas_tarjetas = "\n\n".join(tarjeta_html(a) for a in articulos)

    if 'class="index-list"' in contenido:
        # Ya existe el listado — insertar al principio
        contenido = contenido.replace(
            '<div class="index-list">',
            '<div class="index-list">\n\n' + nuevas_tarjetas,
            1,
        )
    else:
        # Reemplazar empty-state
        bloque_nuevo = (
            '        <div class="index-list">\n\n'
            + nuevas_tarjetas
            + '\n\n        </div>'
        )
        contenido = re.sub(
            r'\s*<div class="empty-state">.*?</div>',
            "\n" + bloque_nuevo,
            contenido,
            flags=re.DOTALL,
        )

    ruta.write_text(contenido, encoding="utf-8")
    print(f"[noticias.html] Actualizado con {len(articulos)} tarjetas nuevas")


# ─────────────────────────────────────────────
# 5. GIT COMMIT + PUSH
# ─────────────────────────────────────────────

def git_push(archivos: list[str]):
    """Hace commit y push de los nuevos archivos."""
    if not archivos:
        return
    try:
        # Añadir archivos específicos
        subprocess.run(["git","add"] + archivos + ["noticias.html"],
                       cwd=REPO, check=True)
        # Verificar que hay cambios staged
        result = subprocess.run(["git","diff","--cached","--name-only"],
                                cwd=REPO, capture_output=True, text=True)
        if not result.stdout.strip():
            print("[Git] Nada nuevo que commitear")
            return

        ahora = datetime.now().strftime("%d/%m/%Y %H:%M")
        n = len(archivos)
        msg = f"Auto: {n} artículo{'s' if n>1 else ''} publicado{'s' if n>1 else ''} — {ahora}"
        subprocess.run(["git","commit","-m", msg], cwd=REPO, check=True)
        subprocess.run(["git","push","origin","main"], cwd=REPO, check=True)
        print(f"[Git] Push completado: {msg}")
    except subprocess.CalledProcessError as e:
        print(f"[Git] Error: {e}")


# ─────────────────────────────────────────────
# 6. MAIN
# ─────────────────────────────────────────────

def main():
    if not ANTHROPIC_KEY:
        print("ERROR: ANTHROPIC_API_KEY no configurada")
        return

    cliente = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
    ahora = datetime.now().strftime("%H:%M")
    print(f"\n{'='*50}")
    print(f"HdD Auto-Publisher — {datetime.now().strftime('%d/%m/%Y')} {ahora}")
    print(f"{'='*50}\n")

    # 1. Recopilar noticias
    print("1. Buscando noticias...")
    noticias = obtener_noticias_rss()
    noticias += obtener_noticias_api()
    # Deduplicar por título similar
    titulos_vistos = set()
    noticias_unicas = []
    for n in noticias:
        clave = re.sub(r'\W','', n["titulo"].lower())[:50]
        if clave not in titulos_vistos:
            titulos_vistos.add(clave)
            noticias_unicas.append(n)
    print(f"   {len(noticias_unicas)} noticias únicas encontradas")

    if not noticias_unicas:
        print("   Sin noticias disponibles. Saliendo.")
        return

    # 2. Seleccionar con Claude
    print("2. Seleccionando historias para HdD...")
    seleccionadas = seleccionar_noticias(noticias_unicas, cliente)
    print(f"   {len(seleccionadas)} historias seleccionadas")

    # 3. Escribir artículos
    print("3. Escribiendo artículos...")
    articulos_ok = []
    archivos_nuevos = []

    for i, noticia in enumerate(seleccionadas):
        print(f"\n   [{i+1}/{len(seleccionadas)}] {noticia['titulo'][:70]}...")
        art = escribir_articulo(noticia, cliente)

        if art:
            # Guardar HTML
            ruta = REPO / art["slug"]
            ruta.write_text(art["html"], encoding="utf-8")
            articulos_ok.append(art)
            archivos_nuevos.append(art["slug"])
            print(f"   ✓ Guardado: {art['slug']}")
        else:
            print(f"   ✗ Error generando artículo")

        # Pausa entre llamadas para no saturar la API
        if i < len(seleccionadas) - 1:
            time.sleep(2)

    if not articulos_ok:
        print("\nNingún artículo generado correctamente.")
        return

    # 4. Actualizar noticias.html
    print(f"\n4. Actualizando noticias.html ({len(articulos_ok)} tarjetas)...")
    actualizar_noticias_html(articulos_ok)

    # 5. Commit y push
    print("5. Publicando en GitHub...")
    git_push(archivos_nuevos)

    print(f"\n{'='*50}")
    print(f"✓ Publicados {len(articulos_ok)} artículos en horadedespertar.org")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    main()
