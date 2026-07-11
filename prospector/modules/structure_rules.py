"""
structure_rules.py
------------------
Variación estructural de la página: en vez de que cada sector tenga siempre
las mismas secciones en el mismo orden, cada negocio recibe:

  - un patrón de hero elegido de un pool global
  - las secciones obligatorias de su sector (el esqueleto que vende)
  - 2-3 secciones opcionales elegidas del pool del sector

Todo determinista: la elección se hace con random.Random sembrado con el
place_id, así el mismo negocio genera siempre la misma estructura pero dos
negocios del mismo sector casi nunca coinciden.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, asdict, field


@dataclass
class PageStructure:
    hero: str                       # patrón de hero (descripción para el prompt)
    sections: list[str] = field(default_factory=list)  # secciones ordenadas (sin el hero)

    def to_dict(self) -> dict:
        return asdict(self)


# --- Pool global de patrones de hero ----------------------------------------

HERO_PATTERNS: list[str] = [
    "Hero a sangre completa: una sola fotografía del local o del servicio ocupando "
    "toda la pantalla, titular superpuesto con contraste garantizado y CTA visible sin hacer scroll.",
    "Hero dividido 50/50: mitad imagen potente, mitad bloque tipográfico con claim, "
    "subtítulo específico y doble CTA.",
    "Hero tipográfico: el nombre del negocio en tipografía gigante como elemento gráfico "
    "principal, fondo con color o textura de marca, foto secundaria pequeña y CTA directo.",
    "Hero collage: mosaico asimétrico de 3-4 fotos reales del negocio con el claim cruzando "
    "la composición y CTA anclado.",
    "Hero editorial con banda: imagen alta con claim sobrio y una banda inferior pegada con "
    "horario de hoy, valoración de Google y botón de llamada/WhatsApp.",
    "Hero asimétrico: imagen desplazada hacia un lado sangrando por el borde, titular que "
    "cruza sobre ella, un bloque de color de marca detrás y CTA con el acento de la paleta.",
    "Hero de ambiente en movimiento: carrusel o vídeo sutil en bucle del local funcionando, "
    "claim fijo encima y CTA que no se mueve.",
]


# --- Secciones por sector -----------------------------------------------------
#
# required: el esqueleto comercial — siempre presentes, en este orden relativo.
#           La ÚLTIMA required es siempre el cierre (ubicación/contacto).
# optional: el pool del que se eligen 2-3 según el negocio.

_SECTIONS: dict[str, dict[str, list[str]]] = {
    "restaurante": {
        "required": [
            "Banda de confianza inmediata: horario de hoy, valoración, ubicación y botón de llamada.",
            "Carta destacada sin importes visibles: platos estrella con descripción breve, alérgenos si procede y CTA 'Consultar carta'.",
            "Reseñas de Google seleccionadas con formato elegante y prueba social.",
            "Reserva simple: WhatsApp, teléfono y formulario corto de fecha, hora y personas.",
            "Cómo llegar: mapa, dirección, aparcamiento/transporte si aplica y horario visible.",
        ],
        "optional": [
            "Experiencia del restaurante: cocina, ambiente, especialidad y para qué ocasiones encaja.",
            "Módulo de menú digital con QR: tarjeta escaneable para abrir la carta, botón 'Ver menú' y texto de actualización.",
            "Galería editorial del local, platos y equipo con transiciones suaves al hacer scroll.",
            "Sugerencias del chef o plato de temporada con su historia breve.",
            "El equipo de sala y cocina: quiénes son y qué defienden.",
            "FAQ: reservas, grupos, intolerancias, comida para llevar y métodos de contacto.",
        ],
    },
    "cafeteria": {
        "required": [
            "Banda de confianza: horario de hoy, valoración, ubicación y contacto rápido.",
            "Especialidades: cafés, desayunos, brunch, dulces o producto artesanal con descripciones apetecibles.",
            "Reseñas de clientes con foco en trato, calidad y ambiente.",
            "Contacto y cómo llegar: mapa, horario, teléfono y WhatsApp.",
        ],
        "optional": [
            "Ambiente del local: galería generosa y bloque 'ideal para...' (trabajar, quedar, familia).",
            "Menú digital con QR para mesa o escaparate, con botón alternativo visible.",
            "Producto de temporada o novedades sin importes visibles.",
            "Módulo de Instagram/galería social presentado con cuidado.",
            "La historia detrás del café: origen del producto o del local en primera persona.",
            "FAQ: reservas, pedidos para llevar, opciones sin gluten/veganas y horarios especiales.",
        ],
    },
    "barberia": {
        "required": [
            "Barra de confianza: valoración, reseñas, ubicación y disponibilidad por WhatsApp.",
            "Servicios principales sin importes visibles: corte, barba, afeitado y packs con beneficios.",
            "Reseñas destacadas con frases reales que refuercen puntualidad, trato y resultado.",
            "Reserva: WhatsApp directo, teléfono, horario y sistema de cita simple.",
            "Ubicación con mapa, referencias para llegar y CTA final.",
        ],
        "optional": [
            "Galería de trabajos tipo portfolio con filtros simples y hover elegante.",
            "El equipo: cada barbero con foto, especialidad y tono cercano.",
            "Método de trabajo: bienvenida, asesoramiento, servicio y acabado final.",
            "El local: sillones, ambiente y detalles que lo hacen reconocible.",
            "Muro de barrio: menciones, colaboraciones o comunidad alrededor de la barbería.",
        ],
    },
    "peluqueria": {
        "required": [
            "Indicadores de confianza: valoración, reseñas, especialistas y ubicación.",
            "Servicios por categoría sin importes: corte, color, tratamientos y asesoramiento.",
            "Reseñas destacadas con foco en trato, resultado y confianza.",
            "Reserva online/WhatsApp con selección de servicio y horario preferido.",
            "Ubicación, horario, mapa y datos de contacto.",
        ],
        "optional": [
            "Galería de trabajos tipo lookbook con transiciones suaves y captions.",
            "Equipo: estilistas, especialidad y enfoque personal.",
            "Productos y marcas usadas si hay información real, sin inventar.",
            "Transformaciones: antes/después tratado con elegancia y consentimiento.",
            "FAQ de citas: cambios, duración y cuidados posteriores.",
            "El look del mes o tendencia de temporada comentada por el salón.",
        ],
    },
    "clinica": {
        "required": [
            "Banda de confianza: valoración, experiencia, ubicación y respuesta rápida.",
            "Especialidades/tratamientos en tarjetas claras con explicación breve y beneficios.",
            "Opiniones verificadas de pacientes con diseño discreto.",
            "Pedir cita: formulario accesible, teléfono, WhatsApp, horario y mapa.",
        ],
        "optional": [
            "Equipo profesional: foto, rol y titulación/certificaciones si se conocen.",
            "Instalaciones y tecnología con módulo visual limpio, sin exagerar claims médicos.",
            "Proceso de atención: primera consulta, diagnóstico, tratamiento y seguimiento.",
            "FAQ: cita, preparación, documentación, urgencias y métodos de contacto.",
            "Compromiso con el paciente: tiempos de espera, trato y seguimiento explicados en claro.",
        ],
    },
    "taller": {
        "required": [
            "Barra de contacto rápido: teléfono, WhatsApp, horario, ubicación y valoración.",
            "Servicios principales: mecánica, ITV, neumáticos, diagnosis, electricidad, etc.",
            "Reseñas reales con foco en confianza, rapidez y transparencia.",
            "Solicitud de presupuesto: formulario con matrícula opcional, modelo, problema y contacto.",
            "Ubicación, mapa, horario y CTA final.",
        ],
        "optional": [
            "Por qué elegirnos: garantía, experiencia, diagnosis clara, trato honesto y plazos.",
            "Proceso: cuenta el problema, revisión, presupuesto, reparación y entrega.",
            "Marcas/vehículos con los que trabajan como módulo visual discreto.",
            "El taller por dentro: fotos reales de los boxes y el equipo trabajando.",
            "Consejos de mantenimiento del taller: 3-4 tips que demuestran oficio.",
        ],
    },
    "tienda_ropa": {
        "required": [
            "Banda de confianza: ubicación, horario, valoración y atención personalizada.",
            "Colecciones destacadas: categorías relevantes del negocio real.",
            "Reseñas o prueba social sobre trato, asesoramiento y calidad.",
            "Información práctica: probadores, cambios si procede, horario, mapa y contacto.",
        ],
        "optional": [
            "Lookbook del mes con composiciones visuales y sugerencias de uso.",
            "Marcas que trabajan si hay información real, sin inventar.",
            "Compra/contacto: catálogo, Instagram, WhatsApp o visita a tienda según corresponda.",
            "Newsletter o avisos de novedades como módulo opcional.",
            "La persona detrás de la tienda: criterio de selección de prendas en primera persona.",
        ],
    },
    "gimnasio": {
        "required": [
            "Barra de confianza: valoración, horario, ubicación y contacto rápido.",
            "Actividades/clases con beneficios, nivel recomendado y CTA por actividad.",
            "Historias/testimonios de alumnos, cuidando privacidad y realismo.",
            "Formulario de prueba: objetivo, disponibilidad, teléfono y WhatsApp.",
            "Ubicación, horario, FAQ y CTA final.",
        ],
        "optional": [
            "Parrilla semanal visual sin saturar la vista móvil.",
            "Instalaciones: galería de salas, material, vestuarios y ambiente.",
            "Entrenadores: foto, especialidad y enfoque de acompañamiento.",
            "Primer día sin miedo: qué pasa exactamente cuando entras por la puerta.",
            "La comunidad: eventos, retos y logros de los miembros.",
        ],
    },
    "floristeria": {
        "required": [
            "Banda práctica: envíos/recogida si procede, horario, ubicación y valoración.",
            "Ramos y arreglos por ocasión: cumpleaños, bodas, condolencias, eventos y detalle.",
            "Reseñas de clientes con foco en cuidado, puntualidad y belleza del resultado.",
            "Formulario de encargo: ocasión, fecha, preferencias, entrega/recogida y contacto.",
            "Ubicación, horario, mapa y FAQ de encargos urgentes.",
        ],
        "optional": [
            "Flor de temporada con historia breve y recomendación de uso.",
            "Servicios especiales: eventos, bodas, decoración, suscripciones o encargos a medida.",
            "Galería de trabajos reales con rejilla elegante y transiciones suaves.",
            "Cómo cuidar tu ramo: consejos breves que demuestran oficio.",
            "El proceso de un encargo: de la llamada a la entrega.",
        ],
    },
    "estetica": {
        "required": [
            "Banda de confianza: valoración, reseñas, ubicación, higiene y atención personalizada.",
            "Tratamientos por categoría: faciales, corporales, depilación, aparatología según el negocio real.",
            "Reseñas de clientas/clientes con foco en cuidado, profesionalidad y confianza.",
            "Reserva: formulario con tratamiento, fecha preferida, teléfono y WhatsApp.",
            "Ubicación, horario, mapa y FAQ de preparación/cuidados.",
        ],
        "optional": [
            "Beneficios y para quién es cada tratamiento, sin promesas exageradas.",
            "Equipo profesional: foto, especialidad, formación y trato.",
            "Instalaciones: cabinas, limpieza, confort y marcas usadas si se conocen.",
            "Resultados esperados tratados con prudencia (antes/después solo con consentimiento).",
            "El ritual de una sesión: qué se siente desde que entras hasta que sales.",
        ],
    },
    "default": {
        "required": [
            "Banda de confianza con valoración, reseñas, ubicación y respuesta rápida.",
            "Servicios o productos principales en tarjetas completas con beneficios, no solo nombres.",
            "Testimonios de clientes con formato cuidado y extractos creíbles.",
            "Contacto completo: dirección, teléfono, horario, mapa, formulario y WhatsApp.",
        ],
        "optional": [
            "Proceso de trabajo en 3 pasos para reducir dudas del cliente.",
            "Galería o bloque visual con imágenes reales y captions útiles.",
            "Preguntas frecuentes orientadas a objeciones habituales.",
            "Quiénes somos: la historia del negocio contada en corto.",
        ],
    },
}


def build_structure(sector: str, seed: str, n_optional: int | None = None) -> PageStructure:
    """
    Construye la estructura de página para un negocio concreto.

    Determinista: mismo (sector, seed) → misma estructura.
    """
    pools = _SECTIONS.get(sector, _SECTIONS["default"])
    rng = random.Random(f"{seed}::{sector}")

    hero = rng.choice(HERO_PATTERNS)

    required = list(pools["required"])
    optional_pool = list(pools["optional"])
    if n_optional is None:
        n_optional = rng.choice([2, 3])
    n_optional = min(n_optional, len(optional_pool))
    chosen_optional = rng.sample(optional_pool, n_optional)

    # Las opcionales se insertan entre las obligatorias, nunca al final:
    # el cierre (contacto/ubicación) siempre es la última sección.
    sections = list(required)
    for extra in chosen_optional:
        pos = rng.randint(1, len(sections) - 1)  # nunca antes de la banda de confianza ni al final
        sections.insert(pos, extra)

    return PageStructure(hero=hero, sections=sections)


__all__ = ["PageStructure", "build_structure", "HERO_PATTERNS"]
