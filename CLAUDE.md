# HdD — Hora de Despertar · Manual de operaciones para Claude

Este archivo le indica a Claude Code cómo gestionar el sitio web de HdD.
Léelo antes de hacer cualquier modificación.

---

## Estructura del proyecto

```
/
├── index.html              Portada
├── noticias.html           Índice de noticias (añadir tarjeta aquí al publicar)
├── educacion.html          Sección educativa
├── newsletter.html         Semanal
├── manifiesto.html         Manifiesto y método editorial
├── aviso-legal.html        Aviso legal
├── privacidad.html         Política de privacidad
├── cookies.html            Política de cookies
│
├── _plantilla-articulo.html  INTERNO — plantilla para nuevos artículos
├── articulo-ejemplo.html     INTERNO — ejemplo del BCE con 4 diapositivas
├── LEEME.md                  Documentación del proyecto (para el editor humano)
├── CLAUDE.md                 Este archivo — instrucciones para Claude
│
├── assets/
│   ├── style.css           Sistema visual completo (tokens en :root)
│   └── script.js           Reloj en vivo + nav + sistema de diapositivas
│
├── .gitignore
└── netlify.toml            Config de Netlify (headers de seguridad)
```

---

## Cómo publicar un artículo nuevo

### 1. Crear el archivo HTML

Copia `_plantilla-articulo.html` con un nombre descriptivo en slug:
```
nombre-del-tema-mes-año.html
Ejemplo: aranceles-trump-mayo-2026.html
```

Rellena las 4 diapositivas siguiendo la estructura obligatoria:
- **Slide 1 — Portada**: eyebrow (categoría), titular, lead/subtítulo, metadata
- **Slide 2 — Conceptos**: 1-3 cajas didácticas explicando términos clave
- **Slide 3 — Desarrollo**: hechos verificables + contexto + motivaciones por actor
- **Slide 4 — Análisis**: cómo lo contaron otros + preguntas abiertas + nota metodológica

**Regla crítica sobre motivaciones**: No atribuir intenciones ocultas como hechos.
Solo exponer incentivos observables, distinguidos claramente de los hechos confirmados.

### 2. Añadir la tarjeta en noticias.html

Busca el `<div class="index-list">` y añade al principio (más reciente primero):

```html
<a href="nombre-del-articulo.html" class="index-item">
  <span class="date">DD·MM·AA</span>
  <div>
    <span class="cat">Categoría</span>
    <h3>Titular del artículo</h3>
    <p class="summary">Resumen en 1-2 frases.</p>
  </div>
  <span style="color: var(--ink-mute); font-size: 0.78rem;">X min →</span>
</a>
```

Si es la primera noticia: elimina el bloque `<div class="empty-state">...</div>` y reemplázalo por el `<div class="index-list">` con la tarjeta.

### 3. Destacar en portada (opcional)

En `index.html`, busca el bloque `empty-state` dentro de la sección "Esta semana" y sustitúyelo por:

```html
<a href="nombre-del-articulo.html" class="index-item">
  <span class="date">DD·MM·AA</span>
  <div>
    <span class="cat">Categoría</span>
    <h3>Titular</h3>
    <p class="summary">Resumen breve.</p>
  </div>
  <span style="color: var(--ink-mute); font-size: 0.78rem;">X min →</span>
</a>
```

### 4. Deploy a producción

```bash
cd /Users/pablorufas/Documents/Claude/Scheduled
git add nombre-del-articulo.html noticias.html index.html
git commit -m "Publicar: Titular del artículo"
git push origin main
```

GitHub Pages despliega automáticamente en ~1-3 minutos.
La URL pública quedará en `https://horadedespertar.org/nombre-del-articulo.html`.

---

## Cómo modificar el sitio

### Cambiar algo de diseño (CSS)
Edita `assets/style.css`. Los tokens de diseño están en `:root` al inicio del archivo.
Commit + push para que se aplique en producción.

### Cambiar la lógica JS
Edita `assets/script.js`. Sin dependencias externas — solo vanilla JS.

### Cambiar el manifiesto o el método editorial
Edita `manifiesto.html`. Si cambias el número de capas de análisis, actualiza también
`_plantilla-articulo.html` y refleja el cambio en los artículos publicados si procede.

---

## Estructura de una diapositiva

Cada artículo tiene exactamente 4 slides. No añadir ni quitar slides sin motivo editorial claro.

```html
<section class="slide slide--cover|concepts|development|analysis" data-slide="0|1|2|3">
  <div class="slide-inner">
    <span class="slide-num">0X — 04</span>
    <span class="slide-label">Etiqueta de sección</span>
    <!-- contenido -->
  </div>
</section>
```

Clases de slide:
- `slide--cover`      → Portada (fondo oscuro)
- `slide--concepts`   → Conceptos (fondo normal, cajas doradas)
- `slide--development`→ Desarrollo (fondo normal)
- `slide--analysis`   → Análisis (fondo ligeramente elevado)

---

## Sistema de deploy (GitHub Pages + dominio propio)

El flujo de trabajo es:
1. Claude edita archivos localmente
2. `git add + git commit + git push origin main`
3. GitHub Pages despliega automáticamente en ~1-3 minutos

**Repositorio GitHub**: `https://github.com/pablorufas/hdd-web`
**URL de producción**: `https://horadedespertar.org` (dominio propio conectado a GitHub Pages)

**SSH push (puerto 443, para redes restringidas)**:
```bash
GIT_SSH_COMMAND="ssh -p 443 -o Hostname=ssh.github.com" git push origin main
```

---

## Dominio

Dominio: `horadedespertar.org`
Conectado en: GitHub → Settings → Pages → Custom domain

---

## Reglas de estilo editorial

1. Nunca publicar antes de tener al menos 2 fuentes verificables
2. Las motivaciones siempre se presentan como incentivos observables, no como hechos
3. Toda caja didáctica explica un solo concepto en 2-4 frases
4. El slide de análisis siempre termina con nota metodológica
5. `articulo-ejemplo.html` nunca se enlaza desde el sitio público — es archivo de referencia
6. Noticias en `noticias.html` en orden cronológico inverso (más reciente primero)

---

## Longitud y profundidad de los artículos

Los artículos de HdD son **largos y explicativos por diseño**. El objetivo es que el lector salga sabiendo más de lo que entró — no solo informado, sino con criterio formado.

### Slide 1 — Portada
- Titular: directo, sin clickbait, máximo 15 palabras
- Lead: 2-3 frases que cuenten QUÉ pasó y QUÉ aprenderá el lector

### Slide 2 — Conceptos
- Mínimo **2 cajas didácticas, ideal 3**
- Cada caja: define un término técnico como si el lector tiene 16 años y ganas de aprender
- Estructura de cada caja: (1) qué es, (2) cómo funciona, (3) por qué importa para esta noticia
- No uses el término que defines para definirlo

### Slide 3 — Desarrollo
**Los hechos** (mínimo 3 párrafos):
- Dato + fuente en cada párrafo
- Cifras exactas, nombres completos, fechas precisas
- Sin adjetivos vacíos ("importante", "significativo") — los datos hablan solos

**El contexto** (2-4 párrafos):
- La línea de tiempo que el lector necesita
- Marco legal, económico o político relevante
- Por qué ocurre AHORA y no antes

**Las motivaciones posibles** (mínimo 3 actores):
- Para cada actor: qué gana y qué pierde en cada escenario, 2-3 frases
- Siempre hay un tercer actor (ciudadanos, mercados, otro Estado, la oposición...)
- Distingue "tiene incentivo para X" de "quiere X" — nunca atribuyas intenciones

### Slide 4 — Análisis
**Cómo lo han contado otros medios** (2-3 párrafos):
- Nombra medios concretos
- Identifica qué marco narrativo usan y qué omiten
- Diferencia entre cobertura nacional e internacional si la hay

**Lo que queda abierto** (mínimo 4 puntos):
- Preguntas concretas y verificables, no retóricas
- El lector debe poder buscar la respuesta él mismo
- Al menos uno debe marcar el hilo para un artículo futuro de HdD

**La pregunta**: la más incómoda, sin respuesta fácil, sin moralismo

---

## Validación antes de publicar

**Siempre correr antes de `git push`:**
```bash
python3 check.py
```

`check.py` detecta automáticamente:
- og:image, twitter:image, canonical, meta description ausentes
- favicon faltante en cualquier página
- Google Analytics, PWA manifest, OneSignal ausentes
- JSON-LD NewsArticle o BreadcrumbList ausentes
- Tokens EDITAR sin reemplazar
- Nota metodológica ausente
- `back-link` ausente
- "Lee también" ausente o colocado DESPUÉS de la nota metodológica (bug conocido)
- "Lee también" fuera del slides-view (otro bug conocido)
- Artículo no añadido a noticias.html

Artículos especiales (semanal, guías) con más de 4 slides están en `SPECIAL_ARTICLES` dentro de `check.py`.

---

## Reglas críticas de estructura

- `slide-num` (ej. `01 — 04`) indica posición de slide, **NO es una fecha**
- La fecha real del artículo está en `slide-meta-row` y en `noticias.html`
- "Lee también" va DENTRO del slide--analysis, ANTES de la nota metodológica
- La sección "Lee también" nunca debe quedar fuera de `</div><!-- /slides-view -->`
- Fechas en "Lee también" se extraen de `noticias.html`, no del HTML del artículo enlazado

---

## Comandos frecuentes

```bash
# Ver el sitio en local
cd /Users/pablorufas/Documents/Claude/Scheduled
python3 -m http.server 8080
# → http://localhost:8080

# Estado del repositorio
git status
git log --oneline -10

# Publicar cambios
git add -A
git commit -m "Descripción del cambio"
git push origin main
```
