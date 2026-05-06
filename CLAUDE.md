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

## Estándares de calidad editorial — NO NEGOCIABLES

### Verificación de hechos
- **Cada dato numérico necesita fuente**. Si no se puede citar fuente verificada con fecha, no se publica el dato. Nunca inventar cifras, aproximar sin avisar ni usar "datos aproximados" sin decirlo.
- **Primaria > secundaria**: citar el documento original (informe del BCE, comunicado oficial, resolución judicial), no la noticia que lo menciona. Si solo se accede a la secundaria, indicarlo: "según X que cita a Y".
- **Fecha de consulta obligatoria** en nota metodológica para cada fuente. Si la fuente ha cambiado o desaparecido desde la consulta, indicarlo.
- **Distinguir entre confirmado, declarado y especulado**. "El gobierno anunció X" ≠ "el gobierno hará X". Usar el modo correcto siempre.
- **Nunca dar por publicada una fuente sin haberla verificado en ese momento**. No asumir que algo sigue siendo verdad porque lo era hace semanas.

### Rigor en los datos
- Las cifras deben ser **las más recientes disponibles** en el momento de escribir. Si hay datos de Q1 2026 y se cita Q4 2025, justificarlo.
- Indicar **siempre el denominador** cuando se usan porcentajes: "el 12% de los hogares" ≠ "el 12%".
- Citar el **tamaño muestral** cuando se mencionan encuestas o estudios.
- Las **proyecciones y estimaciones** se etiquetan como tales: "McKinsey estima que...", no "desaparecerá el 60% del empleo".
- No redondear a conveniencia del relato. Si el dato exacto es 11,8%, no escribir "casi el 12%".

### Estándares de redacción
- **Titular**: descripción precisa del hecho principal, sin adjetivos valorativos, sin clickbait. Máximo 15 palabras.
- **Lead**: qué pasó (hecho), quién, cuándo, y qué aprenderá el lector. Sin hipérbole.
- **Hechos y contexto separados**: los hechos van en "Los hechos" (lo que ocurrió), el análisis va en "Análisis". No mezclar.
- **Motivaciones**: SOLO incentivos observables a partir de posiciones públicas documentadas. Si no hay fuente para el incentivo, no se escribe. Nunca "X quiere", siempre "X tiene incentivo para X porque...".
- **Artículos de educación**: requieren analogías cotidianas, ejemplos concretos con números reales, progresión pedagógica (de lo simple a lo complejo), y al menos una tabla o comparativa visual.

### Control de calidad antes de publicar
1. ¿Cada dato tiene fuente citada en nota metodológica? → Si no: añadir o eliminar el dato.
2. ¿El titular describe el hecho exactamente como ocurrió? → Si no: reescribir.
3. ¿Las motivaciones usan el modo "tiene incentivo para" sin atribuir intenciones? → Si no: reescribir.
4. ¿La nota metodológica lista fuentes específicas (no genéricas) con fecha? → Si no: completar.
5. ¿Los datos son los más recientes disponibles? → Si no: actualizar o justificar.
6. `python3 check.py` → 0 errores antes de cualquier push.

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
