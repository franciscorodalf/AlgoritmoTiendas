import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  ArrowLeft,
  ArrowRight,
  CalendarCheck,
  Check,
  Clock3,
  Download,
  MapPin,
  Menu,
  MessageCircle,
  MousePointerClick,
  Phone,
  QrCode,
  ShieldCheck,
  Sparkles,
  Star,
} from "lucide-react";
import { motion, useMotionValue, useSpring, useTransform } from "framer-motion";
import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";
import "./styles.css";

const cn = (...classes: Array<string | false | null | undefined>) => twMerge(clsx(classes));

type ExampleKind = "restaurante" | "cafeteria" | "belleza" | "servicios";

const examples: Array<{
  id: ExampleKind;
  label: string;
  title: string;
  description: string;
  accent: string;
  tags: string[];
}> = [
  {
    id: "restaurante",
    label: "Restaurante",
    title: "Reservas, carta y menu QR",
    description: "Carta digital, platos destacados, reseñas, horario, mapa y reserva directa.",
    accent: "from-stone-950 via-[#97452a] to-[#e4a84e]",
    tags: ["Reservas", "QR menu", "Resenas"],
  },
  {
    id: "cafeteria",
    label: "Cafeteria / local",
    title: "Ambiente, desayunos y QR en mesa",
    description: "Menu PDF, producto destacado, visitas al local y contacto por WhatsApp.",
    accent: "from-[#fff0d4] via-[#bb7441] to-[#4b2b18]",
    tags: ["Menu PDF", "Horario", "WhatsApp"],
  },
  {
    id: "belleza",
    label: "Belleza",
    title: "Citas, tratamientos y confianza",
    description: "Servicios por categoria, equipo, protocolos, trabajos reales y formulario de cita.",
    accent: "from-[#fff6f8] via-[#d994aa] to-[#7f5267]",
    tags: ["Citas", "Equipo", "Protocolos"],
  },
  {
    id: "servicios",
    label: "Servicios",
    title: "Autoridad y solicitud guiada",
    description: "Servicios claros, garantias, preguntas frecuentes y contacto rapido.",
    accent: "from-[#071f24] via-brand-500 to-[#8bd2bf]",
    tags: ["Servicios", "FAQ", "Contacto"],
  },
];

function useHashRoute() {
  const [hash, setHash] = useState(window.location.hash || "#/");
  useEffect(() => {
    const onHash = () => setHash(window.location.hash || "#/");
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);
  return hash;
}

function App() {
  const hash = useHashRoute();
  const match = hash.match(/^#\/examples\/(.+)$/);
  const example = match ? examples.find((item) => item.id === match[1]) : undefined;
  useEffect(() => {
    if (example) {
      requestAnimationFrame(() => window.scrollTo({ top: 0, left: 0 }));
      return;
    }
    const id = hash.startsWith("#") ? hash.slice(1) : "";
    if (!id || id === "/") return;
    requestAnimationFrame(() => document.getElementById(id)?.scrollIntoView({ block: "start" }));
  }, [example, hash]);
  return example ? <ExamplePage example={example} /> : <Portfolio />;
}

function AmbientBackground() {
  const mouseX = useMotionValue(0);
  const mouseY = useMotionValue(0);
  const smoothX = useSpring(mouseX, { stiffness: 45, damping: 22, mass: 0.8 });
  const smoothY = useSpring(mouseY, { stiffness: 45, damping: 22, mass: 0.8 });
  const x1 = useTransform(smoothX, [-0.5, 0.5], ["-2.5%", "2.5%"]);
  const y1 = useTransform(smoothY, [-0.5, 0.5], ["-1.5%", "1.5%"]);
  const x2 = useTransform(smoothX, [-0.5, 0.5], ["2%", "-2%"]);

  useEffect(() => {
    const move = (event: PointerEvent) => {
      mouseX.set(event.clientX / window.innerWidth - 0.5);
      mouseY.set(event.clientY / window.innerHeight - 0.5);
    };
    window.addEventListener("pointermove", move, { passive: true });
    return () => window.removeEventListener("pointermove", move);
  }, [mouseX, mouseY]);

  return (
    <div className="pointer-events-none fixed inset-0 -z-10 overflow-hidden bg-[#f7f3ec]">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_18%_18%,rgba(255,255,255,.92),transparent_32%),radial-gradient(circle_at_85%_12%,rgba(213,234,225,.9),transparent_30%),radial-gradient(circle_at_68%_78%,rgba(244,210,166,.58),transparent_34%),linear-gradient(180deg,#fbfaf7_0%,#f5f0e8_48%,#eef6f1_100%)]" />
      <div className="absolute inset-0 opacity-[.28] [background-image:url('data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22140%22 height=%22140%22 viewBox=%220 0 140 140%22%3E%3Cfilter id=%22n%22%3E%3CfeTurbulence type=%22fractalNoise%22 baseFrequency=%22.9%22 numOctaves=%222%22 stitchTiles=%22stitch%22/%3E%3C/filter%3E%3Crect width=%22140%22 height=%22140%22 filter=%22url(%23n)%22 opacity=%22.28%22/%3E%3C/svg%3E')]" />
      <motion.div
        style={{ x: x1, y: y1 }}
        animate={{ scale: [1, 1.08, 1], borderRadius: ["42% 58% 52% 48%", "58% 42% 46% 54%", "42% 58% 52% 48%"] }}
        transition={{ duration: 16, repeat: Infinity, ease: "easeInOut" }}
        className="absolute -left-28 top-20 h-[440px] w-[440px] bg-brand-100/70 blur-3xl"
      />
      <motion.div
        style={{ x: x2 }}
        animate={{ scale: [1, 1.12, 1], borderRadius: ["55% 45% 35% 65%", "38% 62% 58% 42%", "55% 45% 35% 65%"] }}
        transition={{ duration: 20, repeat: Infinity, ease: "easeInOut" }}
        className="absolute -right-24 top-36 h-[520px] w-[520px] bg-[#f1cf9f]/55 blur-3xl"
      />
      <motion.div
        animate={{ opacity: [0.25, 0.5, 0.25], scale: [1, 1.05, 1] }}
        transition={{ duration: 10, repeat: Infinity, ease: "easeInOut" }}
        className="absolute bottom-[8%] left-[34%] h-72 w-72 rounded-full bg-white/70 blur-3xl"
      />
    </div>
  );
}

function Nav({ compact = false }: { compact?: boolean }) {
  return (
    <header className="sticky top-0 z-40 border-b border-ink/10 bg-[#fbfaf7]/82 backdrop-blur-2xl">
      <nav className="mx-auto flex h-16 w-[min(1120px,calc(100%-28px))] items-center justify-between gap-4">
        <a href="#/" className="flex items-center gap-3 font-extrabold tracking-tight">
          <span className="grid h-9 w-9 place-items-center rounded-[9px] bg-gradient-to-br from-brand-500 to-brand-700 text-white shadow-soft">W</span>
          <span className={cn("hidden text-[15px] sm:block", compact && "sm:hidden md:block")}>Webs para negocios locales</span>
        </a>
        <div className="flex items-center gap-5 text-sm text-muted">
          {!compact && (
            <div className="hidden items-center gap-5 md:flex">
              <a className="transition-colors hover:text-ink" href="#servicio">Servicio</a>
              <a className="transition-colors hover:text-ink" href="#templates">Ejemplos</a>
              <a className="transition-colors hover:text-ink" href="#proceso">Proceso</a>
              <a className="transition-colors hover:text-ink" href="#confianza">Confianza</a>
            </div>
          )}
          <Button href="#contacto" size="sm">Hablar del proyecto</Button>
        </div>
      </nav>
    </header>
  );
}

function Button({
  href,
  children,
  variant = "primary",
  size = "md",
  icon,
}: {
  href: string;
  children: React.ReactNode;
  variant?: "primary" | "secondary";
  size?: "sm" | "md";
  icon?: React.ReactNode;
}) {
  return (
    <motion.a
      href={href}
      whileTap={{ scale: 0.985 }}
      className={cn(
        "group relative inline-flex items-center justify-center overflow-hidden rounded-[10px] font-extrabold outline-none transition-[box-shadow,border-color,color] duration-500 ease-smooth focus-visible:ring-4 focus-visible:ring-brand-500/25",
        size === "sm" ? "min-h-11 px-4 text-sm" : "min-h-12 px-5 text-[15px]",
        variant === "primary"
          ? "border border-brand-900/20 bg-gradient-to-br from-brand-500 to-brand-700 text-white shadow-[0_14px_34px_rgba(35,99,90,.24)]"
          : "border border-ink/10 bg-white/72 text-ink shadow-[0_12px_30px_rgba(17,19,23,.07)] backdrop-blur-xl",
      )}
    >
      <span className="absolute inset-px rounded-[9px] bg-gradient-to-b from-white/24 to-transparent opacity-80" />
      <span className="absolute inset-0 -translate-x-[120%] bg-gradient-to-r from-transparent via-white/26 to-transparent transition-transform duration-700 ease-smooth group-hover:translate-x-[120%]" />
      <span className="relative flex items-center gap-2">
        {children}
        {icon}
      </span>
    </motion.a>
  );
}

function Portfolio() {
  return (
    <>
      <AmbientBackground />
      <Nav />
      <main>
        <Hero />
        <Service />
        <Templates />
        <Process />
        <Trust />
        <Contact />
      </main>
      <footer className="border-t border-ink/10 py-8 text-sm text-muted">
        <div className="mx-auto w-[min(1120px,calc(100%-28px))]">Webs profesionales para negocios locales. Diseno, contenido y publicacion.</div>
      </footer>
    </>
  );
}

function Hero() {
  return (
    <section className="relative overflow-hidden pb-14 pt-12 sm:pt-16 lg:min-h-[calc(100vh-64px)] lg:pb-12">
      <div className="mx-auto grid w-[min(1120px,calc(100%-28px))] items-center gap-10 lg:grid-cols-[1.04fr_.96fr] lg:gap-14">
        <motion.div initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}>
          <Eyebrow>Diseno web orientado a clientes</Eyebrow>
          <h1 className="max-w-[760px] font-display text-[clamp(2.4rem,11vw,4.7rem)] font-black leading-[1.02] tracking-tight text-ink">
            Tu negocio necesita una web que explique, convenza y haga facil contactar.
          </h1>
          <p className="mt-6 max-w-2xl text-[17px] leading-8 text-muted sm:text-[19px]">
            Creo paginas claras, rapidas y profesionales para negocios locales que quieren dejar de depender solo de redes sociales, directorios o recomendaciones de palabra.
          </p>
          <div className="mt-8 grid gap-3 sm:flex">
            <Button href="#contacto" icon={<ArrowRight className="h-4 w-4 transition-transform duration-500 group-hover:translate-x-1" />}>Pedir una propuesta</Button>
            <Button href="#templates" variant="secondary">Ver ejemplos</Button>
          </div>
          <div className="mt-10 grid gap-4 border-t border-ink/10 pt-5 sm:grid-cols-3">
            {[
              ["Sin plantillas genericas", "Estructura adaptada al negocio y a lo que busca su cliente."],
              ["Texto que vende", "Mensajes directos, beneficios claros y llamadas a la accion visibles."],
              ["Lista para publicar", "Base tecnica ligera, responsive y pensada para cargar rapido."],
            ].map(([title, text]) => (
              <div key={title} className="border-b border-ink/10 pb-4 sm:border-b-0">
                <strong className="block text-xl leading-tight text-ink">{title}</strong>
                <span className="mt-2 block text-sm leading-6 text-muted">{text}</span>
              </div>
            ))}
          </div>
        </motion.div>
        <HeroMockup />
      </div>
    </section>
  );
}

function HeroMockup() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 24, rotate: -1 }}
      animate={{ opacity: 1, y: 0, rotate: 0 }}
      transition={{ duration: 0.9, delay: 0.1, ease: [0.16, 1, 0.3, 1] }}
      className="relative hidden lg:block"
    >
      <motion.div
        animate={{ y: [0, -10, 0] }}
        transition={{ duration: 7, repeat: Infinity, ease: "easeInOut" }}
        className="relative overflow-hidden rounded-[28px] border border-ink/10 bg-white/78 p-4 shadow-premium backdrop-blur-xl"
      >
        <div className="absolute -right-10 -top-10 h-40 w-40 rounded-full bg-brand-100 blur-3xl" />
        <div className="overflow-hidden rounded-[20px] border border-ink/10 bg-[#f8f6f1]">
          <div className="flex h-10 items-center justify-between border-b border-ink/10 bg-white/70 px-4">
            <div className="flex gap-2">
              <span className="h-2.5 w-2.5 rounded-full bg-[#df6b60]" />
              <span className="h-2.5 w-2.5 rounded-full bg-[#e6bd55]" />
              <span className="h-2.5 w-2.5 rounded-full bg-[#5fbf89]" />
            </div>
            <div className="h-2 w-28 rounded-full bg-ink/10" />
          </div>
          <div className="grid min-h-[500px] grid-cols-[1fr_150px]">
            <div className="p-7">
              <div className="relative overflow-hidden rounded-[22px] bg-gradient-to-br from-brand-900 via-brand-500 to-copper p-7 text-white shadow-soft">
                <div className="absolute inset-0 bg-[linear-gradient(90deg,rgba(255,255,255,.14)_1px,transparent_1px)] bg-[size:58px_100%]" />
                <div className="relative max-w-[310px]">
                  <span className="rounded-full bg-white/16 px-3 py-1 text-xs font-black uppercase tracking-[.12em]">Web local</span>
                  <h2 className="mt-8 text-4xl font-black leading-[1.02] tracking-tight">Reserva, llama o escribe en segundos.</h2>
                  <p className="mt-4 text-white/78">Una estructura hecha para convertir visitas en contactos.</p>
                  <div className="mt-7 flex gap-3">
                    <div className="h-11 w-32 rounded-xl bg-white text-brand-700" />
                    <div className="h-11 w-24 rounded-xl border border-white/35" />
                  </div>
                </div>
              </div>
              <div className="mt-5 grid grid-cols-3 gap-4">
                {[
                  ["4.8", "Resenas"],
                  ["24h", "Respuesta"],
                  ["90+", "Lighthouse"],
                ].map(([value, label]) => (
                  <div key={label} className="rounded-2xl border border-ink/10 bg-white p-4 shadow-soft">
                    <strong className="block text-2xl font-black">{value}</strong>
                    <span className="text-xs font-bold uppercase tracking-[.08em] text-muted">{label}</span>
                  </div>
                ))}
              </div>
              <div className="mt-5 rounded-2xl border border-ink/10 bg-white p-4 shadow-soft">
                <div className="mb-3 flex items-center justify-between">
                  <span className="text-sm font-black">Flujo de contacto</span>
                  <span className="rounded-full bg-brand-50 px-2.5 py-1 text-xs font-black text-brand-700">Activo</span>
                </div>
                <div className="grid grid-cols-4 gap-2">
                  {[MessageCircle, Phone, MapPin, Star].map((Icon, index) => (
                    <div key={index} className="grid h-14 place-items-center rounded-xl bg-brand-50 text-brand-700">
                      <Icon className="h-5 w-5" />
                    </div>
                  ))}
                </div>
              </div>
            </div>
            <aside className="border-l border-ink/10 bg-white/70 p-5">
              <div className="h-3 w-20 rounded-full bg-ink/10" />
              <div className="mt-6 grid gap-3">
                {["Hero", "Servicios", "Resenas", "Contacto"].map((item, index) => (
                  <div key={item} className={cn("rounded-xl px-3 py-3 text-sm font-black", index === 0 ? "bg-brand-500 text-white" : "bg-ink/5 text-muted")}>{item}</div>
                ))}
              </div>
              <div className="mt-8 rounded-2xl bg-gradient-to-br from-brand-50 to-white p-4">
                <QrCode className="h-7 w-7 text-brand-700" />
                <p className="mt-3 text-sm font-bold leading-5 text-ink">Menu QR y descargas integradas</p>
              </div>
            </aside>
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
}

function Eyebrow({ children }: { children: React.ReactNode }) {
  return (
    <div className="mb-4 flex items-center gap-3 text-xs font-black uppercase tracking-[.14em] text-brand-500">
      <span className="h-px w-7 bg-copper" />
      {children}
    </div>
  );
}

function SectionHeading({ eyebrow, title, text }: { eyebrow?: string; title: string; text: string }) {
  return (
    <motion.div
      initial={{ y: 14 }}
      whileInView={{ y: 0 }}
      viewport={{ once: true, margin: "-80px" }}
      transition={{ duration: 0.65, ease: [0.16, 1, 0.3, 1] }}
      className="mb-9 max-w-3xl"
    >
      {eyebrow && <Eyebrow>{eyebrow}</Eyebrow>}
      <h2 className="text-[clamp(2rem,5.4vw,3.25rem)] font-black leading-[1.06] tracking-tight text-ink">{title}</h2>
      <p className="mt-4 text-[17px] leading-8 text-muted">{text}</p>
    </motion.div>
  );
}

function Service() {
  return (
    <section id="servicio" className="border-t border-ink/10 bg-white/36 py-16 sm:py-24">
      <div className="mx-auto w-[min(1120px,calc(100%-28px))]">
        <SectionHeading
          title="Una web pensada para convertir visitas en conversaciones."
          text="No se trata solo de verse bien. La pagina tiene que responder dudas, transmitir seriedad y llevar al cliente al siguiente paso."
        />
        <div className="grid gap-4 md:grid-cols-3">
          {[
            [MessageCircle, "Mensaje comercial claro", "Ordeno servicios, beneficios y razones para elegirte en una estructura facil de leer."],
            [ShieldCheck, "Confianza desde el primer vistazo", "Experiencia, proceso, preguntas frecuentes, ubicacion y contacto visible."],
            [MousePointerClick, "Diseno util en movil", "La mayoria de clientes llega desde el telefono. Contactar debe ser inmediato."],
          ].map(([Icon, title, text]) => (
            <MotionCard key={String(title)}>
              <Icon className="mb-5 h-6 w-6 text-brand-500" />
              <h3 className="text-xl font-black">{String(title)}</h3>
              <p className="mt-3 leading-7 text-muted">{String(text)}</p>
            </MotionCard>
          ))}
        </div>
      </div>
    </section>
  );
}

function MotionCard({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <motion.article
      initial={{ y: 14 }}
      whileInView={{ y: 0 }}
      viewport={{ once: true, margin: "-80px" }}
      whileHover={{ y: -6 }}
      transition={{ duration: 0.45, ease: [0.16, 1, 0.3, 1] }}
      className={cn("rounded-xl border border-ink/10 bg-white/78 p-6 shadow-soft backdrop-blur-xl", className)}
    >
      {children}
    </motion.article>
  );
}

function Templates() {
  return (
    <section id="templates" className="relative overflow-hidden border-t border-ink/10 py-16 sm:py-24">
      <div className="mx-auto w-[min(1120px,calc(100%-28px))]">
        <SectionHeading
          eyebrow="Demos navegables"
          title="Ejemplos para que el cliente vea posibilidades reales."
          text="Demos de estilos y estructuras que puedo adaptar a cada negocio: restaurante, local de barrio, belleza o servicios."
        />
        <Marquee />
        <div className="mt-9 grid gap-5 md:grid-cols-2 lg:grid-cols-3">
          {examples.map((example) => (
            <ExampleCard key={example.id} example={example} />
          ))}
        </div>
      </div>
    </section>
  );
}

function Marquee() {
  const words = ["Reservas", "Menu QR", "WhatsApp", "Resenas", "SEO local", "Galeria", "Formulario", "Mapa"];
  return (
    <div className="overflow-hidden rounded-full border border-ink/10 bg-white/60 py-3 [mask-image:linear-gradient(90deg,transparent,#000_12%,#000_88%,transparent)]">
      <motion.div
        animate={{ x: ["0%", "-50%"] }}
        transition={{ duration: 22, repeat: Infinity, ease: "linear" }}
        className="flex w-max gap-8 px-5 text-xs font-black uppercase tracking-[.12em] text-muted"
      >
        {[...words, ...words, ...words].map((word, index) => <span key={`${word}-${index}`}>{word}</span>)}
      </motion.div>
    </div>
  );
}

function ExampleCard({ example }: { example: (typeof examples)[number] }) {
  const goToExample = () => {
    window.location.hash = `/examples/${example.id}`;
  };

  return (
    <motion.article
      initial={{ y: 14 }}
      whileInView={{ y: 0 }}
      viewport={{ once: true, margin: "-80px" }}
      whileHover={{ y: -8 }}
      onClick={goToExample}
      onKeyDown={(event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          goToExample();
        }
      }}
      role="link"
      tabIndex={0}
      transition={{ duration: 0.48, ease: [0.16, 1, 0.3, 1] }}
      className="group cursor-pointer overflow-hidden rounded-xl border border-ink/10 bg-white shadow-soft outline-none transition-[box-shadow,border-color] focus-visible:border-brand-500 focus-visible:ring-4 focus-visible:ring-brand-500/20"
    >
      <div className={cn("relative min-h-[245px] overflow-hidden bg-gradient-to-br p-4 text-white", example.accent)}>
        <div className="absolute inset-0 bg-black/28" />
        <div className="absolute inset-0 bg-[linear-gradient(90deg,rgba(255,255,255,.18)_1px,transparent_1px)] bg-[size:54px_100%]" />
        <span className="relative z-10 inline-flex min-h-8 items-center rounded-full bg-white px-3 text-xs font-black text-ink shadow-soft ring-1 ring-white/70">{example.label}</span>
        <div className="absolute right-5 top-14 h-32 w-24 rounded-2xl border border-white/45 bg-white/18 shadow-premium backdrop-blur-xl">
          <div className="mx-auto mt-5 h-10 w-16 rounded-lg bg-white/28" />
          <div className="mx-auto mt-7 h-2 w-14 rounded-full bg-white/28" />
          <div className="mx-auto mt-3 h-2 w-12 rounded-full bg-white/22" />
        </div>
        <div className="absolute bottom-5 left-4 right-14 rounded-2xl border border-white/45 bg-black/38 p-5 text-white shadow-premium backdrop-blur-xl transition-transform duration-500 ease-smooth group-hover:-translate-y-1">
          <div className="mb-3 flex gap-1.5">
            <span className="h-2 w-2 rounded-full bg-white/72" />
            <span className="h-2 w-2 rounded-full bg-white/72" />
            <span className="h-2 w-2 rounded-full bg-white/72" />
          </div>
          <h3 className="max-w-[220px] text-xl font-black leading-tight text-white drop-shadow-sm">{example.title}</h3>
          <div className="mt-4 flex flex-wrap gap-2">
            {example.tags.map((tag) => (
              <span
                key={tag}
                className="rounded-full bg-white px-3 py-1.5 text-[11px] font-black text-ink shadow-[0_8px_20px_rgba(0,0,0,.18)] ring-1 ring-white/70"
              >
                {tag}
              </span>
            ))}
          </div>
        </div>
      </div>
      <div className="p-5">
        <h3 className="text-xl font-black">{example.title.split(",")[0]}</h3>
        <p className="mt-3 leading-7 text-muted">{example.description}</p>
        <Button href={`#/examples/${example.id}`} variant="secondary" size="sm" icon={<ArrowRight className="h-4 w-4" />}>Ver ejemplo</Button>
      </div>
    </motion.article>
  );
}

function Process() {
  const steps = [
    ["Diagnostico", "Reviso como se presenta el negocio hoy: ficha de Google, redes, competencia y puntos fuertes."],
    ["Propuesta visual y contenido", "Defino estructura, tono, secciones clave y llamadas a la accion antes de construir."],
    ["Web lista para publicar", "Entrego una pagina responsive, clara y preparada para WhatsApp, telefono, email o reservas."],
  ];
  return (
    <section id="proceso" className="border-t border-ink/10 bg-white/36 py-16 sm:py-24">
      <div className="mx-auto grid w-[min(1120px,calc(100%-28px))] gap-8 lg:grid-cols-[.85fr_1.15fr]">
        <SectionHeading title="Proceso simple, sin marearte." text="Trabajo con informacion real del negocio para que la web no suene vacia ni parezca una plantilla cambiada de color." />
        <div className="grid gap-4">
          {steps.map(([title, text], index) => (
            <MotionCard key={title} className="grid grid-cols-[44px_1fr] gap-4">
              <span className="grid h-11 w-11 place-items-center rounded-xl bg-brand-50 font-black text-brand-700">{index + 1}</span>
              <div>
                <h3 className="text-lg font-black">{title}</h3>
                <p className="mt-2 leading-7 text-muted">{text}</p>
              </div>
            </MotionCard>
          ))}
        </div>
      </div>
    </section>
  );
}

function Trust() {
  return (
    <section id="confianza" className="bg-gradient-to-br from-brand-700 to-brand-900 py-16 text-white sm:py-24">
      <div className="mx-auto grid w-[min(1120px,calc(100%-28px))] gap-9 lg:grid-cols-2 lg:items-center">
        <div>
          <h2 className="text-[clamp(2rem,5vw,3.3rem)] font-black leading-[1.06] tracking-tight">Tu cliente tiene que entender en segundos por que deberia elegirte.</h2>
          <p className="mt-5 text-lg leading-8 text-white/74">Una web profesional reduce dudas: quien eres, que haces, donde estas, como trabajas y como puede contactar contigo.</p>
        </div>
        <div className="grid gap-4">
          {["Textos escritos para personas, no para rellenar espacio.", "Estructura preparada para servicios, comercios, salud, belleza, restauracion y profesionales locales.", "Propuesta a medida: primero se entiende el proyecto y despues se prepara un alcance adecuado.", "Diseno sobrio, rapido y facil de mantener."].map((item) => (
            <div key={item} className="grid grid-cols-[32px_1fr] gap-3 text-white/88">
              <span className="grid h-8 w-8 place-items-center rounded-full bg-white/14"><Check className="h-4 w-4" /></span>
              <span>{item}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function Contact() {
  return (
    <section id="contacto" className="border-t border-ink/10 py-16 sm:py-24">
      <div className="mx-auto grid w-[min(1120px,calc(100%-28px))] gap-8 lg:grid-cols-[1fr_.8fr] lg:items-center">
        <SectionHeading title="Hablemos de la web que necesita tu negocio." text="Cuentame que vendes, donde atiendes y que quieres conseguir. Te respondo con una propuesta clara y sin compromiso." />
        <MotionCard>
          <p className="mb-5 leading-7 text-muted">Cambia estos enlaces por tu WhatsApp y email reales cuando quieras publicar.</p>
          <div className="grid gap-3 sm:flex">
            <Button href="https://wa.me/34000000000" icon={<MessageCircle className="h-4 w-4" />}>WhatsApp</Button>
            <Button href="mailto:contacto@tudominio.com" variant="secondary">Email</Button>
          </div>
        </MotionCard>
      </div>
    </section>
  );
}

function ExamplePage({ example }: { example: (typeof examples)[number] }) {
  if (example.id === "restaurante") return <RestaurantWebsite />;
  if (example.id === "cafeteria") return <CafeWebsite />;
  if (example.id === "belleza") return <BeautyWebsite />;
  return <ServicesWebsite />;
}

function DemoShell({ children, tone = "warm" }: { children: React.ReactNode; tone?: "warm" | "rose" | "green" }) {
  const bg = tone === "rose" ? "from-[#fff6f8] via-white to-[#f3faf6]" : tone === "green" ? "from-[#eef8f4] via-white to-[#fff8ed]" : "from-[#fff7ed] via-white to-[#eef8f4]";
  return (
    <div className={cn("min-h-screen bg-gradient-to-br", bg)}>
      <AmbientBackground />
      <Nav compact />
      {children}
    </div>
  );
}

function DemoBack() {
  return <a href="#/" className="inline-flex items-center gap-2 text-sm font-black text-ink/80"><ArrowLeft className="h-4 w-4" /> Volver a ejemplos</a>;
}

function RestaurantWebsite() {
  const menu = [
    ["Para compartir", "Pulpo braseado con mojo verde", "Papa negra, aceite de cilantro, sal marina y lima."],
    ["Para compartir", "Croquetas de jamon iberico", "Bechamel cremosa, panko fino y alioli tostado."],
    ["Brasa", "Cherne a la brasa", "Verduras de temporada, jugo de limon y hierbas frescas."],
    ["Brasa", "Arroz meloso de costilla", "Fondo tostado, setas, azafran y alioli suave."],
    ["Postres", "Tarta cremosa de queso", "Mermelada de higos y crumble de almendra."],
    ["Postres", "Chocolate, aceite y sal", "Bizcocho humedo, crema ligera y escamas de sal."],
  ];
  const reviews = [
    ["Laura M.", "La carta se entiende rapido y reservar por WhatsApp fue comodisimo."],
    ["Carlos R.", "Buena presencia, fotos cuidadas y menu QR claro en mesa."],
    ["Nerea S.", "Llegamos por Google y en dos clics teniamos mesa."],
  ];
  return (
    <DemoShell>
      <main>
        <section className="mx-auto grid w-[min(1180px,calc(100%-28px))] gap-10 pb-16 pt-10 lg:min-h-[calc(100vh-64px)] lg:grid-cols-[1fr_.9fr] lg:items-center">
          <div>
            <DemoBack />
            <p className="mt-10 text-sm font-black uppercase tracking-[.18em] text-[#9a4f2f]">Brasa Atlantica</p>
            <h1 className="mt-4 text-[clamp(3rem,11vw,6.3rem)] font-black leading-[.94] tracking-tight">Cocina de brasa, producto local y reservas sin friccion.</h1>
            <p className="mt-6 max-w-2xl text-lg leading-8 text-muted">Una web completa para restaurante: carta digital, menu QR, reservas, platos destacados, opiniones, ubicacion, horario y experiencia visual.</p>
            <div className="mt-8 grid gap-3 sm:flex">
              <Button href="#reserva">Reservar mesa</Button>
              <Button href="#carta" variant="secondary" icon={<QrCode className="h-4 w-4" />}>Ver carta QR</Button>
            </div>
          </div>
          <div className="relative min-h-[520px] overflow-hidden rounded-[34px] bg-gradient-to-br from-[#1b1512] via-[#93462b] to-[#efb34f] p-8 text-white shadow-premium">
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_25%_20%,rgba(255,255,255,.22),transparent_24%),linear-gradient(90deg,rgba(255,255,255,.12)_1px,transparent_1px)] bg-[size:auto,70px_100%]" />
            <div className="relative flex h-full flex-col justify-between">
              <div className="max-w-sm">
                <span className="rounded-full bg-white/18 px-3 py-1 text-xs font-black uppercase tracking-[.14em]">Abierto hoy 13:00 - 23:30</span>
                <h2 className="mt-8 text-5xl font-black leading-none">Reserva para esta noche.</h2>
              </div>
              <div className="grid gap-3 sm:grid-cols-3">
                {["4.8 opiniones", "Carta QR", "Centro ciudad"].map((item) => <div key={item} className="rounded-2xl bg-white/18 p-4 font-black backdrop-blur-xl">{item}</div>)}
              </div>
            </div>
          </div>
        </section>

        <section className="border-y border-ink/10 bg-white/58 py-14">
          <div className="mx-auto grid w-[min(1180px,calc(100%-28px))] gap-4 md:grid-cols-4">
            {["Reserva por WhatsApp", "Menu PDF con QR", "Alergenos visibles", "Mapa y parking"].map((item) => <MotionCard key={item}><Check className="mb-3 h-5 w-5 text-[#9a4f2f]" /><strong>{item}</strong></MotionCard>)}
          </div>
        </section>

        <section id="carta" className="mx-auto grid w-[min(1180px,calc(100%-28px))] gap-10 py-20 lg:grid-cols-[1fr_360px] lg:items-start">
          <div>
            <Eyebrow>Carta destacada</Eyebrow>
            <h2 className="text-[clamp(2.4rem,6vw,4rem)] font-black leading-none">Una carta completa que se entiende antes de pedir.</h2>
            <div className="mt-8 grid gap-4 md:grid-cols-2">
              {menu.map(([section, name, desc]) => (
                <MotionCard key={name}>
                  <span className="text-xs font-black uppercase tracking-[.14em] text-[#9a4f2f]">{section}</span>
                  <h3 className="text-xl font-black">{name}</h3>
                  <p className="mt-3 leading-7 text-muted">{desc}</p>
                </MotionCard>
              ))}
            </div>
          </div>
          <MenuQrSection />
        </section>

        <section className="bg-[#171210] py-20 text-white">
          <div className="mx-auto w-[min(1180px,calc(100%-28px))]">
            <Eyebrow>Ambiente</Eyebrow>
            <h2 className="max-w-3xl text-[clamp(2.2rem,6vw,4.4rem)] font-black leading-none">Una experiencia visual para vender la visita.</h2>
            <div className="mt-9 grid gap-4 md:grid-cols-3">
              {["Barra abierta", "Mesa para grupos", "Producto de temporada"].map((item, index) => (
                <motion.div
                  key={item}
                  whileHover={{ y: -8, scale: 1.01 }}
                  transition={{ type: "spring", stiffness: 180, damping: 22 }}
                  className={cn(
                    "min-h-72 overflow-hidden rounded-[28px] border border-white/10 p-6 shadow-premium",
                    index === 0 && "bg-[radial-gradient(circle_at_25%_20%,rgba(239,179,79,.45),transparent_34%),linear-gradient(145deg,rgba(255,255,255,.16),rgba(255,255,255,.04))]",
                    index === 1 && "bg-[radial-gradient(circle_at_70%_30%,rgba(155,83,48,.55),transparent_35%),linear-gradient(145deg,rgba(255,255,255,.18),rgba(255,255,255,.04))]",
                    index === 2 && "bg-[radial-gradient(circle_at_40%_25%,rgba(139,210,191,.32),transparent_34%),linear-gradient(145deg,rgba(255,255,255,.14),rgba(255,255,255,.04))]"
                  )}
                >
                  <strong className="text-2xl">{item}</strong>
                  <p className="mt-4 max-w-xs leading-7 text-white/70">Bloque preparado para fotos reales del local, platos o equipo cuando el cliente las tenga.</p>
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        <section className="mx-auto grid w-[min(1180px,calc(100%-28px))] gap-4 py-20 lg:grid-cols-[.9fr_1.1fr]">
          <MotionCard>
            <Eyebrow>Opiniones</Eyebrow>
            <h2 className="text-4xl font-black leading-tight">Confianza antes de reservar.</h2>
            <div className="mt-7 grid gap-4">
              {reviews.map(([name, text]) => (
                <div key={name} className="rounded-2xl border border-ink/10 bg-white/70 p-5">
                  <div className="flex gap-1 text-[#d68b35]">{Array.from({ length: 5 }).map((_, index) => <Star key={index} className="h-4 w-4 fill-current" />)}</div>
                  <p className="mt-3 leading-7 text-muted">{text}</p>
                  <strong className="mt-3 block">{name}</strong>
                </div>
              ))}
            </div>
          </MotionCard>
          <MotionCard id="reserva" className="bg-[#102f2b] text-white">
            <Eyebrow>Reserva</Eyebrow>
            <h2 className="text-4xl font-black leading-tight">Formulario preparado para recibir mesas reales.</h2>
            <div className="mt-7 grid gap-3 sm:grid-cols-2">
              {["Fecha preferida", "Hora", "Personas", "Telefono"].map((item) => <div key={item} className="rounded-2xl bg-white/10 p-4 font-black text-white/90">{item}</div>)}
            </div>
            <Button href="#" className="mt-7 bg-white text-brand-800 hover:bg-white">Enviar solicitud</Button>
          </MotionCard>
        </section>

        <DemoFinalCta title="Reserva una mesa en Brasa Atlantica" text="Formulario corto con fecha, hora, personas y contacto. La web tambien puede enlazar a WhatsApp Business o a un motor de reservas." cta="Reservar por WhatsApp" />
      </main>
    </DemoShell>
  );
}

function MenuQrSection() {
  return (
    <MotionCard className="grid justify-items-center text-center">
      <QrVisual />
      <strong className="mt-5 text-xl">Carta PDF con QR</strong>
      <p className="mt-2 leading-7 text-muted">Lista para imprimir en mesa, escaparate o compartir por WhatsApp.</p>
      <div className="mt-5">
        <Button href="./assets/carta-brasa-atlantica.pdf" icon={<Download className="h-4 w-4" />}>Descargar carta PDF</Button>
      </div>
    </MotionCard>
  );
}

function CafeWebsite() {
  const products = [
    ["Flat white Colombia", "Cafe dulce, leche texturizada y notas de panela."],
    ["Tostada Atlantica", "Aguacate, huevo, tomate asado y aceite de albahaca."],
    ["Croissant de almendra", "Horneado diario, crema suave y almendra laminada."],
    ["Bowl de temporada", "Yogur, fruta fresca, granola y miel local."],
  ];
  return (
    <DemoShell>
      <main>
        <DemoHero label="Cafeteria Nube" title="Cafe de especialidad, desayunos y un menu que cambia cada semana." text="Demo completa para cafeteria: carta QR, productos de temporada, galeria, horario, mapa y pedidos por WhatsApp." accent="from-[#fff0d4] via-[#b97944] to-[#4b2b18]" primary="Pedir por WhatsApp" secondary="Ver menu" />
        <DemoFeatureGrid items={[["Cafe de especialidad", "Origenes rotativos, metodos filtrados y recomendaciones."], ["Desayunos", "Tostadas, dulces, bowls y opciones vegetales."], ["Menu QR", "Carta digital para mesa, barra y escaparate."], ["Eventos", "Brunch privado, talleres y degustaciones."]]} />
        <section id="carta" className="mx-auto grid w-[min(1180px,calc(100%-28px))] gap-8 py-20 lg:grid-cols-[1fr_360px]">
          <div>
            <Eyebrow>Producto de temporada</Eyebrow>
            <h2 className="text-[clamp(2.3rem,6vw,4rem)] font-black leading-none">Una carta viva, facil de actualizar.</h2>
            <div className="mt-8 grid gap-4 md:grid-cols-2">{products.map(([name, desc]) => <MotionCard key={name}><h3 className="text-xl font-black">{name}</h3><p className="mt-3 leading-7 text-muted">{desc}</p><span className="mt-5 inline-flex rounded-full bg-brand-50 px-3 py-1 text-xs font-black text-brand-700">Disponible hoy</span></MotionCard>)}</div>
          </div>
          <MenuQrSection />
        </section>
        <DemoShowcase title="Ambiente de local" items={["Mesa de trabajo con enchufes", "Mostrador de producto fresco", "Zona de terraza y pedidos para llevar"]} />
        <DemoFinalCta title="Haz que el cliente sepa que esta abierto y quiera entrar." text="Horario, ubicacion, terraza, carta QR y WhatsApp siempre visibles." cta="Como llegar" />
      </main>
    </DemoShell>
  );
}

function BeautyWebsite() {
  return (
    <DemoShell tone="rose">
      <main>
        <DemoHero label="Aura Studio" title="Tratamientos, citas y confianza desde el primer vistazo." text="Demo completa para estetica o peluqueria: servicios, protocolos, equipo, reseñas, galeria y formulario de cita." accent="from-[#fff6f8] via-[#d994aa] to-[#7f5267]" primary="Pedir cita" secondary="Ver tratamientos" />
        <DemoFeatureGrid items={[["Tratamientos faciales", "Higiene, hidratacion, luminosidad y antiedad."], ["Equipo profesional", "Especialidades, formacion y trato cercano."], ["Protocolos", "Higiene, tiempos, preparacion y cuidados posteriores."], ["Citas", "Formulario con servicio, fecha preferida y contacto."]]} />
        <section className="mx-auto w-[min(1180px,calc(100%-28px))] py-20">
          <Eyebrow>Tratamientos</Eyebrow>
          <h2 className="max-w-4xl text-[clamp(2.3rem,6vw,4rem)] font-black leading-none">Una web que transmite calma sin perder conversion.</h2>
          <div className="mt-9 grid gap-4 md:grid-cols-3">{["Faciales", "Corporales", "Manicura premium"].map((item) => <MotionCard key={item}><h3 className="text-xl font-black">{item}</h3><p className="mt-3 leading-7 text-muted">Beneficios, duracion orientativa, para quien es y CTA de cita.</p></MotionCard>)}</div>
        </section>
        <DemoShowcase title="Prueba visual y confianza" items={["Galeria de trabajos reales", "Equipo y cabinas", "Cuidados antes y despues de la cita"]} tone="rose" />
        <DemoFinalCta title="Convierte interes en citas reales." text="La pagina guia al cliente hacia WhatsApp o formulario sin parecer agresiva." cta="Solicitar cita" />
      </main>
    </DemoShell>
  );
}

function ServicesWebsite() {
  return (
    <DemoShell tone="green">
      <main>
        <DemoHero label="Nexo Servicios" title="Servicios claros, autoridad local y solicitud guiada." text="Demo completa para talleres, clinicas, reformas, academias o profesionales: servicios, proceso, garantias, FAQs y presupuesto." accent="from-[#071f24] via-brand-500 to-[#8bd2bf]" primary="Solicitar presupuesto" secondary="Ver servicios" />
        <DemoFeatureGrid items={[["Servicios", "Cada servicio explica problema, solucion y siguiente paso."], ["Proceso", "Diagnostico, presupuesto, ejecucion y seguimiento."], ["Confianza", "Reseñas, garantias, experiencia y preguntas frecuentes."], ["Formulario", "Campos utiles para recibir solicitudes de calidad."]]} />
        <section className="mx-auto w-[min(1180px,calc(100%-28px))] py-20">
          <Eyebrow>Flujo comercial</Eyebrow>
          <h2 className="max-w-4xl text-[clamp(2.3rem,6vw,4rem)] font-black leading-none">No solo informa: filtra y prepara el contacto.</h2>
          <div className="mt-9 grid gap-4 md:grid-cols-4">{["Problema", "Revision", "Presupuesto", "Servicio"].map((item, index) => <MotionCard key={item}><span className="text-sm font-black text-brand-500">0{index + 1}</span><h3 className="mt-2 text-xl font-black">{item}</h3></MotionCard>)}</div>
        </section>
        <DemoShowcase title="Autoridad local" items={["Garantias y cobertura", "Casos resueltos", "Preguntas frecuentes antes de llamar"]} tone="green" />
        <DemoFinalCta title="Contacto rapido sin perder informacion importante." text="Formulario, llamada, WhatsApp y mapa segun el flujo real del negocio." cta="Solicitar presupuesto" />
      </main>
    </DemoShell>
  );
}

function DemoHero({ label, title, text, accent, primary, secondary }: { label: string; title: string; text: string; accent: string; primary: string; secondary: string }) {
  return (
    <section className="mx-auto grid w-[min(1180px,calc(100%-28px))] gap-10 pb-16 pt-10 lg:min-h-[calc(100vh-64px)] lg:grid-cols-[1fr_.9fr] lg:items-center">
      <div>
        <DemoBack />
        <p className="mt-10 text-sm font-black uppercase tracking-[.18em] text-brand-500">{label}</p>
        <h1 className="mt-4 text-[clamp(3rem,11vw,6rem)] font-black leading-[.95] tracking-tight">{title}</h1>
        <p className="mt-6 max-w-2xl text-lg leading-8 text-muted">{text}</p>
        <div className="mt-8 grid gap-3 sm:flex"><Button href="#accion">{primary}</Button><Button href="#accion" variant="secondary">{secondary}</Button></div>
      </div>
      <div className={cn("relative min-h-[500px] overflow-hidden rounded-[34px] bg-gradient-to-br p-8 text-white shadow-premium", accent)}>
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_30%_20%,rgba(255,255,255,.24),transparent_25%),linear-gradient(90deg,rgba(255,255,255,.14)_1px,transparent_1px)] bg-[size:auto,72px_100%]" />
        <div className="relative flex h-full flex-col justify-between">
          <span className="w-fit rounded-full bg-white/18 px-3 py-1 text-xs font-black uppercase tracking-[.14em]">Demo navegable</span>
          <div className="rounded-[28px] bg-white/88 p-6 text-ink shadow-premium backdrop-blur-xl"><h2 className="text-3xl font-black leading-tight">{title}</h2><div className="mt-5 flex flex-wrap gap-2"><span className="rounded-full bg-brand-50 px-3 py-1 text-xs font-black text-brand-700">Mobile-first</span><span className="rounded-full bg-brand-50 px-3 py-1 text-xs font-black text-brand-700">CTAs</span><span className="rounded-full bg-brand-50 px-3 py-1 text-xs font-black text-brand-700">Confianza</span></div></div>
        </div>
      </div>
    </section>
  );
}

function DemoFeatureGrid({ items }: { items: string[][] }) {
  return <section className="border-y border-ink/10 bg-white/55 py-14"><div className="mx-auto grid w-[min(1180px,calc(100%-28px))] gap-4 md:grid-cols-4">{items.map(([title, text]) => <MotionCard key={title}><Sparkles className="mb-4 h-5 w-5 text-brand-500" /><h3 className="text-lg font-black">{title}</h3><p className="mt-3 text-sm leading-6 text-muted">{text}</p></MotionCard>)}</div></section>;
}

function DemoFinalCta({ title, text, cta }: { title: string; text: string; cta: string }) {
  return <section id="accion" className="py-20"><div className="mx-auto w-[min(980px,calc(100%-28px))]"><MotionCard className="text-center"><h2 className="text-[clamp(2rem,6vw,3.8rem)] font-black leading-none">{title}</h2><p className="mx-auto mt-5 max-w-2xl text-lg leading-8 text-muted">{text}</p><div className="mt-7 flex justify-center"><Button href="#">{cta}</Button></div></MotionCard></div></section>;
}

function DemoShowcase({ title, items, tone = "warm" }: { title: string; items: string[]; tone?: "warm" | "rose" | "green" }) {
  const colors = tone === "rose"
    ? ["from-[#fff4f7] to-[#c27c95]", "from-[#f4d3dc] to-[#7f5267]", "from-white to-[#e7aabb]"]
    : tone === "green"
      ? ["from-[#ecfaf5] to-[#2c7469]", "from-[#0d3330] to-[#8bd2bf]", "from-white to-[#d5efe8]"]
      : ["from-[#fff3dd] to-[#c07838]", "from-[#3b2218] to-[#efb34f]", "from-white to-[#ead0aa]"];
  return (
    <section className="bg-white/55 py-20">
      <div className="mx-auto w-[min(1180px,calc(100%-28px))]">
        <Eyebrow>Contenido real</Eyebrow>
        <h2 className="max-w-4xl text-[clamp(2.2rem,6vw,4rem)] font-black leading-none">{title}</h2>
        <div className="mt-9 grid gap-4 md:grid-cols-3">
          {items.map((item, index) => (
            <motion.div
              key={item}
              whileHover={{ y: -8, scale: 1.01 }}
              transition={{ type: "spring", stiffness: 180, damping: 22 }}
              className={cn("min-h-72 overflow-hidden rounded-[28px] bg-gradient-to-br p-6 shadow-premium", colors[index])}
            >
              <div className="flex h-full flex-col justify-between">
                <span className="h-14 w-14 rounded-2xl bg-white/70 shadow-soft" />
                <strong className="max-w-xs text-2xl leading-tight text-white drop-shadow-[0_1px_12px_rgba(0,0,0,.25)]">{item}</strong>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

function QrVisual() {
  const cells = ["111010111", "101000101", "111011111", "000110010", "101111101", "011001000", "111010111", "101011101", "111100111"];
  return (
    <div className="grid aspect-square w-52 grid-cols-9 gap-1.5 rounded-2xl border border-ink/10 bg-white p-5 shadow-soft">
      {cells.join("").split("").map((cell, index) => <span key={index} className={cn("rounded-[3px]", cell === "1" ? "bg-ink" : "bg-transparent")} />)}
    </div>
  );
}

createRoot(document.getElementById("root")!).render(<App />);
