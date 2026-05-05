# HdD — Criterios editoriales para selección y escritura de artículos

Este archivo guía el razonamiento editorial. Se lee antes de elegir temas y antes de escribir.

---

## 1. Selección de temas

### Qué cubre HdD

Un tema merece cobertura si cumple al menos 2 de estos 4 criterios:
- **Impacto directo**: afecta al bolsillo, la salud, los derechos o la seguridad de gente real
- **Requiere contexto**: sin explicación previa, el dato suelto no se entiende
- **Infracobertura**: los medios generalistas lo ignoran, minimizan o cubren mal
- **Enseña algo durable**: explica un mecanismo que sirve para entender el mundo más allá de hoy

### Qué NO cubre HdD

- Declaraciones sin acción concreta ("el ministro dijo que estudiarán...")
- Noticias de protocolo o agenda oficial sin consecuencias reales
- Deportes, salvo que la historia sea sobre economía, corrupción o política
- Sucesos sin dimensión sistémica (accidentes aislados, crímenes individuales sin patrón)
- Contenido que es esencialmente una nota de prensa

### Variedad temática obligatoria en un informativo de 5 artículos

Nunca 2 artículos del mismo tema principal. Buscar equilibrio entre:
- España (política, economía, sociedad)
- Internacional (geopolítica, Europa, mundo)
- Economía de impacto cotidiano (precios, empleo, vivienda)
- Institucional / judicial
- Ciencia, tecnología o medio ambiente (al menos 1 por semana)

---

## 2. Razonamiento sobre extensión

Antes de escribir, decide conscientemente:

### Tiempo de lectura según tipo de artículo

| Tipo | Rango | Cuándo |
|---|---|---|
| Noticia con buen contexto previo | 8-10 min | Tema conocido, hecho concreto y claro |
| Análisis estándar | 11-13 min | Contexto necesario, varios actores |
| Investigación o tema complejo | 14-16 min | Muchos conceptos nuevos, historia larga, múltiples capas |

### Longitud de cada sección

Decide ANTES de escribir cuánto merece cada parte. Escríbelo en `_razonamiento.extension`.

**Conceptos (slide 2)**:
- 1 concepto → tema muy conocido para adultos, solo falta un matiz técnico
- 2 conceptos → estándar
- 3 conceptos → tema técnico o con varios sistemas que explicar
- 4-5 conceptos → solo si el tema es genuinamente complejo (economía, ciencia, derecho)

**Hechos (slide 3)**:
- 2 párrafos → noticia reciente con poco historial
- 3-4 párrafos → estándar
- 5+ párrafos → caso judicial largo, proceso con fases múltiples, datos estadísticos complejos

**Contexto (slide 3)**:
- 1 párrafo → contexto muy conocido o irrelevante
- 2-3 párrafos → estándar
- 4+ párrafos → solo si el "por qué ahora" requiere explicar cambios históricos o legales profundos

**Motivaciones (slide 3)**:
- `null` si: descubrimiento científico, estadística sin actores, evento cultural, desastre natural
- `null` si: los actores son tan obvios que añadir la sección no aporta información
- 2 actores → mínimo cuando sí aplica
- 3-4 actores → estándar en política, economía, geopolítica
- Nunca más de 5 actores en el mismo artículo

**Medios (slide 4)**:
- `null` si: cobertura mediática es homogénea y no hay nada que contrastar
- `null` si: tema tan técnico que no hay "enfoque editorial" diferenciado
- Presente si: hay diferencia clara entre cómo lo cuenta la derecha vs. izquierda, o entre medios nacionales vs. internacionales

---

## 3. Test del lector de 20 años

Antes de usar cualquier término técnico, nombre de institución, sigla o concepto, pregúntate:

> *¿Sabría esto un estudiante universitario de 20 años que lee noticias pero no es experto en política o economía?*

**Si la respuesta es NO → explícalo**, ya sea en el slide de conceptos o con una frase aclaratoria inline en el texto.

Ejemplos de cosas que un lector de 20 años probablemente NO sabe:
- Qué es el BCE, el FMI, la AIEA, el TJUE, el CGPJ, la AN
- Qué es el euríbor, el PIB, el déficit estructural, el déficit de cuenta corriente
- Qué es la Ertzaintza, la Guardia Civil, la AN, el TC, el TS
- Qué es un ERE, un ERTE, un convenio colectivo
- Qué es el Estrecho de Ormuz y por qué importa
- Diferencia entre mayoría absoluta y simple
- Qué es el artículo 155, la LOMLOE, el ELA, la amnistía

Ejemplos de cosas que SÍ sabe:
- Que hay un presidente del gobierno y un rey
- Que existe el Congreso y el Senado
- Que Trump es el presidente de EEUU
- Precios, alquiler, trabajo

**Regla práctica**: si pones un acrónimo, la primera vez siempre escríbelo completo + acrónimo. Después puedes usar solo el acrónimo.

---

## 4. Calidad de hechos

- Cada párrafo de hechos lleva al menos 1 dato concreto: cifra, nombre, fecha, porcentaje o fuente
- Sin adjetivos vacíos: "histórico", "importante", "significativo", "relevante", "clave" — los datos hablan solos
- Las fuentes se nombran en el texto ("según el INE", "de acuerdo con The Guardian", "datos del Ministerio de Hacienda")
- Si un hecho no tiene fuente, no se incluye

---

## 5. Motivaciones

**Nunca**: "el gobierno quiere X", "PP busca Y", "Irán pretende Z"
**Siempre**: "el gobierno tiene incentivo para X porque...", "al PP le conviene Y si...", "Irán gana si Z porque..."

La diferencia es epistémica: lo segundo es verificable, lo primero es atribución de intenciones.

---

## 6. Lee también — cómo elegirlo

```bash
grep -n 'class="index-item"' noticias.html | head -50
```

Criterios de selección (en orden de prioridad):
1. Mismo tema o actor principal
2. Mismo contexto geográfico o institucional  
3. Artículo que explica un concepto usado en este
4. Artículo reciente (últimos 7 días preferiblemente)

Nunca poner un artículo que no existe en el repo — el script `nuevo_articulo.py` lo validará y fallará.
