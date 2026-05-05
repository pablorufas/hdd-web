# HdD — Manual de operaciones

## Estructura del proyecto

```
index.html          Portada (portada se actualiza con update_portada.py)
noticias.html       Índice de noticias
educacion.html      Sección educativa
newsletter.html     Semanal
manifiesto.html     Manifiesto
assets/style.css    Tokens de diseño en :root
assets/script.js    Reloj + nav + slides
_plantilla-articulo.html  INTERNO — no enlazar públicamente
```

## Publicar un artículo nuevo

**Método rápido (recomendado):**
```bash
python3 nuevo_articulo.py mi_articulo.json   # genera HTML + actualiza noticias + sitemap + push
python3 nuevo_articulo.py --schema           # muestra el formato JSON esperado
```

**Método manual (solo si el JSON no es suficiente):**
1. Copiar `_plantilla-articulo.html` con slug `tema-mes-2026.html`
2. Rellenar 4 slides (ver estructura más abajo)
3. Añadir tarjeta en `noticias.html` (más reciente primero)
4. `python3 check.py` → debe dar 0 errores
5. `git add ... && git commit -m "Publicar: ..." && GIT_SSH_COMMAND="ssh -p 443 -o Hostname=ssh.github.com" git push origin main`

## Estructura de 4 slides

| Slide | Clase | Contenido |
|---|---|---|
| 01 | `slide--cover` | eyebrow, h1, lead, metadata (fecha · tiempo · autor) |
| 02 | `slide--concepts` | 2-3 cajas `.didactic-box` (qué es, cómo funciona, por qué importa) |
| 03 | `slide--development` | Hechos + Contexto + Motivaciones posibles |
| 04 | `slide--analysis` | Cómo lo contaron medios + Preguntas abiertas + La pregunta + Lee también + Nota metodológica |

`slide-num` formato obligatorio: `01 — 04`, `02 — 04`, etc.

## Reglas críticas

- **Motivaciones**: incentivos observables, nunca intenciones atribuidas como hechos
- **Lee también**: exactamente 3 links, dentro del slide--analysis, ANTES de la nota metodológica
- **Nota metodológica**: fuentes específicas con fecha de consulta, siempre al final
- **back-link**: `<a href="noticias.html" class="back-link">← Todas las noticias</a>` al inicio de `<main>`
- `articulo-ejemplo.html` nunca se enlaza públicamente

## Automatización

```bash
python3 update_portada.py          # actualiza portada con artículos más recientes
python3 update_portada.py --no-git # solo modifica archivos (GitHub Actions lo usa)
python3 fix_lee_tambien.py         # añade lee-también a artículos que no lo tienen
```

GitHub Actions ejecuta `update_portada.py --no-git` automáticamente en cada push a `noticias.html`.

## Deploy

```
Repo: https://github.com/pablorufas/hdd-web
URL:  https://horadedespertar.org
Push normal:    git push origin main
Push restringido: GIT_SSH_COMMAND="ssh -p 443 -o Hostname=ssh.github.com" git push origin main
```

## Artículos especiales (> 4 slides)

`caso-kitchen-investigacion-completa-semanal-04-2026.html` (9 slides)
`corrupcion-entorno-sanchez-guia-04-2026.html` (8 slides)
`inflacion-explicada.html` (7 slides)
`oferta-y-demanda.html` (6 slides)

Están declarados en `SPECIAL_ARTICLES` dentro de `check.py`.

## Validación

```bash
python3 check.py   # 0 errores obligatorio antes de push
```

Detecta: og:image, canonical, meta description, favicon, GA, PWA, OneSignal, JSON-LD,
nota metodológica, back-link, lee-también ausente o mal colocado, artículo no en noticias.html.
