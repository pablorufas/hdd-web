# Hora de Despertar — sitio web

Sitio estático multipágina para **HdD — Hora de Despertar**, periódico digital de periodismo didáctico.

---

## Estructura del proyecto

```
/
├── index.html                  Portada: hero, pilares editoriales, estado de publicaciones
├── manifiesto.html             Manifiesto de marca y método editorial (público)
├── noticias.html               Índice de noticias (vacío hasta primera publicación)
├── educacion.html              Sección educativa (vacía hasta primera publicación)
├── newsletter.html             Semanal: descripción del formato y archivo de ediciones
├── aviso-legal.html            Aviso legal (placeholder hasta lanzamiento)
├── privacidad.html             Política de privacidad (placeholder hasta lanzamiento)
├── cookies.html                Política de cookies (placeholder hasta lanzamiento)
│
├── _plantilla-articulo.html    INTERNO — plantilla base para nuevos artículos
├── articulo-ejemplo.html       INTERNO — ejemplo de artículo completo con estructura real
│                               No está enlazado desde el sitio público.
│
└── assets/
    ├── style.css               Sistema visual completo
    └── script.js               Reloj en vivo, nav móvil
```

Los archivos con prefijo `_` o marcados como INTERNOS son de trabajo: no se enlazan desde la navegación pública y no deben subirse como páginas accesibles si quieres mantener el sitio limpio.

---

## Ver el sitio localmente

Abre `index.html` en cualquier navegador haciendo doble clic. No requiere servidor.

Para trabajar con rutas relativas sin fricciones (recomendado):

```bash
python3 -m http.server 8080
# luego abre http://localhost:8080
```

---

## Publicar el sitio en internet

El sitio es 100 % estático: no necesita base de datos ni servidor propio. Puedes publicarlo gratis en minutos.

### Opción A — Netlify (recomendado)

1. Crea una cuenta en [netlify.com](https://netlify.com)
2. Arrastra la carpeta del proyecto a la zona de deploy de Netlify
3. El sitio queda online al instante con URL tipo `hdd-abc123.netlify.app`
4. Para usar tu dominio propio (`horadedespertar.org`): en Netlify → Domain settings → Add custom domain

### Opción B — Vercel

1. Instala la CLI: `npm i -g vercel`
2. Desde la carpeta del proyecto: `vercel`
3. Sigue las instrucciones del asistente

### Opción C — Cloudflare Pages

1. Sube el proyecto a un repositorio de GitHub
2. En Cloudflare Pages → Create a project → conecta el repo
3. Sin configuración de build (es HTML estático): deja vacíos los campos de build command y output directory

### Dominio sugerido

`horadedespertar.org` o `.com` — unos 10–15 €/año en cualquier registrador (Namecheap, Porkbun, IONOS).

---

## Lógica de doble acceso: versión pública y versión de trabajo

El proyecto distingue dos modos de uso:

| Versión | Archivos | Para quién |
|---|---|---|
| **Pública** | Todos los `.html` sin prefijo `_` | Lectores del sitio |
| **De trabajo** | `_plantilla-articulo.html`, `articulo-ejemplo.html`, `LEEME.md` | Editor / desarrollador |

Los archivos de trabajo **no se enlazan desde el sitio** y pueden excluirse del deploy añadiendo un fichero `_redirects` o `.netlifyignore` si se quiere mayor limpieza. Por ahora, al no estar enlazados, son invisibles para el lector.

No hay CMS ni backend. La "edición" consiste en:
1. Copiar `_plantilla-articulo.html` con un nombre descriptivo
2. Editar el contenido marcado como `EDITAR`
3. Añadir la tarjeta correspondiente en `noticias.html`
4. Subir los archivos al hosting (re-deploy en Netlify/Vercel es automático si está conectado a un repo)

---

## Cómo añadir una noticia nueva

1. Copia `_plantilla-articulo.html` y renómbralo: `bce-tipos-mayo-2026.html`
2. Sustituye todo el contenido entre las etiquetas `EDITAR`
3. Respeta la estructura de cinco capas:
   - Hechos verificables
   - Contexto
   - Motivaciones plausibles (incentivos observables, no intenciones inventadas)
   - Cómo lo han contado otros medios
   - Lo que queda abierto
4. Añade la tarjeta en `noticias.html` dentro de `.index-list`:

```html
<a href="bce-tipos-mayo-2026.html" class="index-item">
  <span class="date">05·05·26</span>
  <div>
    <span class="cat">Economía</span>
    <h3>Titular del artículo</h3>
    <p class="summary">Resumen breve.</p>
  </div>
  <span style="color: var(--ink-mute); font-size: 0.78rem;">X min →</span>
</a>
```

5. Si quieres destacarla en portada, sustituye el `empty-state` de `index.html` por la tarjeta.

---

## Cómo añadir una edición semanal

Añade un bloque `<a class="index-item">` en `newsletter.html` dentro de `.index-list`, respetando el orden cronológico inverso (más reciente arriba). Sustituye el `empty-state` existente cuando haya al menos una edición publicada.

---

## Sistema visual

- **Logo**: `HdD` en fuente LED de siete segmentos DSEG7 Classic. Rojo `#e10600` con halo para imitar un despertador digital clásico.
- **Tipografía**: Fraunces (serif editorial) para titulares y cuerpo largo; Inter (sans) para UI, metadatos y navegación.
- **Paleta**: negro `#0a0a0a`, crema cálida `#f3ece2`, rojo `#e10600`, dorado `#f5c36b`.
- **Textura**: grano SVG sutil sobre toda la página.
- **Reloj en vivo**: se actualiza cada segundo en cabecera y hero.
- **Layer-nav**: componente de navegación pedagógica por capas (anclas internas) disponible en la plantilla de artículo. Acento dorado, distinto de las cajas didácticas (acento rojo).

---

## Continuar el desarrollo desde Claude Code

El proyecto está preparado para seguir evolucionando desde Claude Code sin fricción:

- Toda la lógica visual está en `assets/style.css` (tokens en `:root`)
- Todo el JS está en `assets/script.js` (sin dependencias externas)
- No hay build steps, bundlers ni dependencias npm
- Cada página es autocontenida: header, main, footer, `<script>`
- Para escalar a un CMS real (Ghost, Astro, Next.js), este sistema visual puede usarse directamente como capa de diseño

---

© 2026 Hora de Despertar · Hecho con rigor. Leído con criterio.
