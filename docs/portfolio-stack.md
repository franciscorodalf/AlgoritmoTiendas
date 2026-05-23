# Portfolio: arquitectura recomendada

## Estado actual

El portfolio publico vive en `prospector/static/portfolio/` y se sirve desde Flask con estas rutas:

- `/portfolio/` -> `index.html`
- `/portfolio/demo-*.html` -> demos navegables
- `/portfolio/assets/...` -> imagenes y recursos

Es una web estatica: HTML, CSS y JavaScript sin framework frontend activo. Eso es positivo para velocidad, pero ahora mismo dificulta mantener una identidad consistente porque cada demo contiene su propio CSS y estructura.

## Astro vs Eleventy

Astro y Eleventy son generadores de sitios estaticos. En lugar de editar un HTML grande a mano, se trabaja con layouts, componentes y datos; despues el build genera HTML final para publicar.

### Astro

Astro encaja mejor para este portfolio porque:

- Genera HTML estatico rapido.
- Permite componentes reutilizables para demos, estadisticas, CTAs y layouts.
- Carga JavaScript solo en las partes interactivas que lo necesitan mediante su modelo de "islas".
- Deja migrar poco a poco una web existente sin reescribir todo de golpe.

Fuente oficial: https://docs.astro.build/en/concepts/islands/

### Eleventy

Eleventy encaja muy bien para contenido simple, blogs, documentacion o landings muy ligeras. Es flexible y directo, pero para este caso Astro tiene mejor recorrido si el portfolio va a tener visores, filtros, demos interactivas y componentes visuales reutilizables.

Fuente oficial: https://www.11ty.dev/docs/

## Plan de migracion recomendado

1. Mantener Flask para el CRM y API de Prospector.
2. Separar el portfolio comercial en una app estatica Astro.
3. Convertir las demos en componentes y datos:
   - `demos/barberia`
   - `demos/restaurante`
   - `demos/clinica`
   - `demos/taller`
4. Sustituir previews con iframe por capturas optimizadas y abrir la demo completa bajo demanda.
5. Usar WebP/AVIF responsive para imagenes.
6. Publicar el portfolio en Vercel, Netlify, Cloudflare Pages o GitHub Pages, y enlazarlo desde el CRM.

## Mejora aplicada ya

Mientras el entorno no tenga `npm`, `pnpm` o `yarn`, no se puede instalar Astro de forma normal en esta maquina. Por eso se han aplicado mejoras compatibles con la version actual:

- Assets convertidos a WebP.
- HTML apuntando a las versiones WebP.
- Cache headers para imagenes servidas desde `/portfolio/assets/`.
- HTML sin cache agresiva para poder ver cambios rapido durante desarrollo.
