# Algoritmo de Prospección — Tenerife

Script que detecta negocios locales **sin página web** en Tenerife, extrae
sus datos de Google Maps, analiza sus reseñas con una IA local (Ollama) y
genera un **prompt listo para pegar en Bolt / v0 / Framer** que crea
automáticamente un prototipo visual personalizado de su web.

Todo el pipeline es **local y sin APIs de IA de pago**.

---

## Requisitos

| Herramienta | Para qué | Cómo obtenerla |
|---|---|---|
| Python 3.10+ | Ejecutar el script | https://python.org |
| Google Places API key | Buscar negocios + reseñas | [console.cloud.google.com](https://console.cloud.google.com/apis/credentials) |
| Ollama + modelo local | Analizar reseñas | https://ollama.com |

## Instalación rápida

```bash
# 1. Entra al directorio del proyecto
cd prospector

# 2. Crea un entorno virtual (recomendado)
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/Mac

# 3. Instala dependencias
pip install -r requirements.txt

# 4. Configura credenciales
copy .env.example .env          # Windows
# cp .env.example .env          # Linux/Mac
# edita .env y pon tu GOOGLE_PLACES_API_KEY

# 5. Arranca Ollama y descarga un modelo
ollama pull llama3.1:8b         # ~4.7 GB, mejor calidad
# ollama pull mistral:7b        # ~4 GB, más rápido
```

## Obtener una Google Places API key

1. Entra en https://console.cloud.google.com/
2. Crea un proyecto nuevo
3. En **APIs & Services → Library** activa:
   - **Places API (New)**
   - **Geocoding API**
4. En **APIs & Services → Credentials** crea una API key
5. Copia la key en `.env` como `GOOGLE_PLACES_API_KEY=...`
6. Google da **200 $/mes de crédito gratis** — suficiente para cientos de prospectos al mes.

## Uso

```bash
# Búsqueda por sector + zona
python main.py "peluquerías en La Laguna"

# Por nombre concreto
python main.py "Barbería El Rincón Santa Cruz"

# Solo sector (usa región por defecto de .env)
python main.py "cafeterías"

# Batch desde fichero
python main.py --queries queries.txt

# Limitar resultados
python main.py "restaurantes Adeje" --max 5

# Incluir los que ya tienen web (auditoría competencia)
python main.py "gimnasios" --include-with-website

# Modo rápido sin IA local (solo datos + paleta)
python main.py "talleres Santa Cruz" --skip-ollama
```

Los prompts generados se guardan en `prospector/output/<nombre_negocio>.txt`.

## Qué hace exactamente el pipeline

Para cada negocio:

1. **Google Places** — busca, filtra los que ya tienen web, extrae: nombre, categoría, dirección, teléfono, horario, puntuación, reseñas, fotos
2. **ColorThief + K-means** — descarga la foto de perfil y extrae una paleta de 6 colores clasificada en primario / secundario / acento / neutro
3. **Typography rules** — por el sector (`hair_care`, `restaurant`, etc.) elige la tipografía y vibe visual coherente
4. **Ollama + llama3.1:8b** — lee las reseñas y extrae keywords, tono, selling points, vibe y público objetivo en JSON
5. **Jinja2** — ensambla todo en un prompt con una plantilla específica del sector

Output final: un `.txt` con el prompt completo, listo para pegar en Bolt / v0 / Framer.

## Estructura

```
prospector/
├── main.py                      # orquestador + CLI
├── modules/
│   ├── google_extractor.py      # Google Places API
│   ├── image_analyzer.py        # paleta de colores
│   ├── typography_rules.py      # sector → tipografía
│   ├── review_analyzer.py       # Ollama local
│   └── prompt_builder.py        # ensamblaje Jinja2
├── templates/
│   ├── _base.j2                 # bloques comunes
│   ├── default.j2
│   ├── restaurante.j2
│   ├── cafeteria.j2
│   ├── barberia.j2
│   ├── peluqueria.j2
│   ├── clinica.j2
│   ├── taller.j2
│   ├── tienda_ropa.j2
│   └── gimnasio.j2
├── output/                      # prompts generados
├── requirements.txt
└── .env.example
```

## Probar un módulo aislado

Cada módulo es independiente. Ejemplos:

```python
# Sólo Google
from modules.google_extractor import GoogleExtractor
gx = GoogleExtractor()
for b in gx.search("peluquerías La Laguna", max_results=3):
    print(b.name, b.rating, b.website)

# Sólo paleta
from modules.image_analyzer import extract_palette
print(extract_palette("ruta/a/logo.jpg").to_dict())

# Sólo Ollama
from modules.review_analyzer import ReviewAnalyzer
ra = ReviewAnalyzer()
print(ra.analyze("Mi Negocio", "restaurante", reviews=[...]).to_dict())
```

## Troubleshooting

- **`GOOGLE_PLACES_API_KEY` no configurado** → copia `.env.example` a `.env` y pon tu key.
- **Ollama no responde** → arranca la app Ollama (en Windows corre como servicio en background); o usa `--skip-ollama`.
- **El modelo tarda mucho** → usa `mistral:7b` en vez de `llama3.1:8b` (actualiza `OLLAMA_MODEL` en `.env`).
- **No salen resultados** → Google devuelve como mucho 60 por query; usa queries más específicas por zona pequeña.
