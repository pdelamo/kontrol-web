#!/usr/bin/env python3
"""Monta las páginas de contenido de kontrolapp.es (SEO) a partir de los textos de seo/textos/*.md.

Uso, desde la raíz del repo:   python3 seo/construir.py

Qué hace:
  · web/<slug>/index.html por cada seo/textos/<slug>.md (URL limpia: /escandallos/).
  · web/paginas.css y web/paginas.js: la hoja de estilos y los guiones de la PORTADA (web/index.html) copiados
    tal cual, más lo propio de estas páginas. Se SACAN de index.html cada vez que se ejecuta: si Luis o Pablo
    cambian la cabecera, el menú, los colores, los botones, las imágenes o el «Pide tu demo» de la portada, basta
    volver a ejecutar esto y las páginas los siguen (no hay que tocar nada a mano).
  · web/sitemap.xml con todas las direcciones y su lastmod.

Pablo, 18-nov-2026: SIN precios («nadie de la competencia los pone») y CORTAS como la portada: «solo lo necesario
y justo para que nos llamen o nos contacten; ahí ya se lo vendemos mejor». Cada página: titular, entradilla,
3-4 puntos de una frase, una imagen real, 3 preguntas y «Pide tu demo» (el de la portada).

Formato de cada .md (lo escribe el director de arte; aquí no se reescribe nada, Markdown → HTML y poco más):
  ---
  slug, title, description, etiqueta, h1, imagen (una de IMAGENES o «ninguna»), enlaces (3 páginas), [revisar]
  ---
  La entradilla (un párrafo).
  ## Titular de los puntos.
  ### Punto           (3 o 4)
  Una frase.
  ## Preguntas frecuentes
  ### ¿Pregunta?      (3)
  Respuesta.
Los «[PENDIENTE DE PABLO: …]» pasan a comentario HTML. Solo usa la biblioteca estándar.
"""
import html, json, re, subprocess, sys
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
WEB = RAIZ / "web"
TEXTOS = RAIZ / "seo" / "textos"
DOMINIO = "https://kontrolapp.es"
HOY = date.today().isoformat()
OG_IMAGEN = DOMINIO + "/img/foto-albaran-1100.webp"

# Nombre corto de cada página (migas de pan y «Más de Kontrol»), en el orden del sitemap.
NOMBRES = {
    "escandallos": "Escandallos",
    "facturas-y-albaranes": "Facturas y albaranes",
    "almacen-y-merma": "Almacén y merma",
    "personal-y-nominas": "Personal y nóminas",
    "ventas-y-cierres-de-caja": "Ventas y cierres de caja",
    "restaurantes-y-bares": "Restaurantes y bares",
    "tiendas": "Tiendas",
    "menorca-y-baleares": "Menorca y Baleares",
    "verifactu": "Verifactu",
}

# Las imágenes que se pueden poner en la cabecera: las mismas de la portada (texto alternativo y tamaños salen de ahí).
IMAGENES = {
    "tarjeta-platos": "app", "tarjeta-avisos": "app", "tarjeta-margen": "app",
    "hoy-m-claro": "movil",
    "foto-albaran": "foto", "foto-pedido": "foto", "foto-noche2": "foto",
}
PIE_APP = "Pantalla real de la app, con un restaurante de ejemplo."

LARGO_MAX = 260          # palabras visibles por página (el encargo dice 230; esto solo avisa)


# ───────────────────────────── Markdown → HTML (lo justo) ─────────────────────────────
def esc(t):
    return html.escape(t, quote=False)


def enlace_interno(u):
    """/escandallos → /escandallos/ (las direcciones de las páginas acaban en barra)."""
    if u.startswith("/") and not u.startswith("//") and "." not in u.rsplit("/", 1)[-1] and not u.endswith("/"):
        return u + "/"
    return u


def inline(t):
    t = t.replace("VERI*FACTU", "VERI\x00FACTU")            # el asterisco de la palabra, que no es cursiva
    t = esc(t)
    t = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", lambda m: '<a href="%s">%s</a>' % (enlace_interno(m.group(2)), m.group(1)), t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<![\*\w])\*(?!\s)([^*]+?)(?<!\s)\*(?![\*\w])", r"<em>\1</em>", t)
    return t.replace("\x00", "*")


def plano(t):
    """El mismo texto sin marcas, para el JSON-LD y para contar palabras."""
    t = t.replace("VERI*FACTU", "VERI\x00FACTU")
    t = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", t)
    t = re.sub(r"\*\*(.+?)\*\*", r"\1", t)
    t = re.sub(r"(?<![\*\w])\*(?!\s)([^*]+?)(?<!\s)\*(?![\*\w])", r"\1", t)
    return t.replace("`", "").replace("\x00", "*")


def leer_md(ruta):
    texto = ruta.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", texto, re.S)
    if not m:
        sys.exit("%s: falta la cabecera --- ... ---" % ruta.name)
    meta, clave = {}, None
    for linea in m.group(1).split("\n"):
        if re.match(r"^\s+-\s", linea) and clave:
            meta.setdefault(clave, []).append(linea.split("-", 1)[1].strip())
        else:
            k, _, v = linea.partition(":")
            clave = k.strip()
            meta[clave] = v.strip() if v.strip() else []
    return meta, m.group(2)


def bloques(cuerpo, nombre):
    """Trocea el cuerpo en bloques (tipo, texto): solo párrafos, ## y ###."""
    out = []
    for trozo in re.split(r"\n\s*\n", cuerpo.strip()):
        lineas = [l.strip() for l in trozo.strip().split("\n") if l.strip()]
        while lineas:
            l = lineas.pop(0)
            if l.startswith("### "):
                out.append(("h3", l[4:].strip()))
            elif l.startswith("## "):
                out.append(("h2", l[3:].strip()))
            elif re.match(r"^(# |\||- |\* |\d+\. |---)", l):
                sys.exit("%s: «%s…» no va en el formato corto (solo párrafos, ## y ###)" % (nombre, l[:30]))
            else:
                par = [l]
                while lineas and not lineas[0].startswith("#"):
                    par.append(lineas.pop(0))
                out.append(("p", " ".join(par)))
    return out


def pendiente(p):
    m = re.match(r"^\[PENDIENTE DE PABLO:\s*(.*)\]$", p, re.S)
    if not m:
        return None
    txt = m.group(1).strip()
    assert "--" not in txt, "«--» dentro de un PENDIENTE"
    return "<!-- PENDIENTE DE PABLO: %s -->" % txt, txt


# ───────────────────────────── Piezas sacadas de la portada ─────────────────────────────
def pieza(origen, ini, fin, incluir_ini=True):
    a = origen.index(ini)
    b = origen.index(fin, a)
    return origen[a:b + len(fin)] if incluir_ini else origen[a + len(ini):b]


def sin_entra(t):
    """Sin la animación de entrada de la portada: estas piezas se ven quietas desde el primer momento."""
    return t.replace(" entra\"", "\"").replace("class=\"entra\"", "")


def imagenes_de_portada(idx):
    out = {}
    for tag in re.findall(r"<img [^>]*>", idx):
        m = re.search(r'src="img/([^"]+)\.webp"', tag)
        if not m:
            continue
        clave = re.sub(r"-\d+$", "", m.group(1))

        def at(n):
            r = re.search(r'\s%s="([^"]*)"' % n, tag)
            return r.group(1) if r else None
        if clave in out or not at("alt"):
            continue
        out[clave] = {"src": "/img/%s.webp" % m.group(1), "srcset": (at("srcset") or "").replace("img/", "/img/"),
                      "alt": at("alt"), "w": at("width"), "h": at("height")}
    return out


def sacar_de_portada():
    idx = (WEB / "index.html").read_text(encoding="utf-8")
    p = {}
    # El bloque de MARCA (teléfono, WhatsApp, correo, plazas…) y el arranque del tema oscuro: los mismos que la portada.
    p["marca"] = pieza(idx, "<script>\n/* ── LO QUE SE PUEDE CAMBIAR", "</script>")
    p["sprite"] = pieza(idx, '<svg xmlns="http://www.w3.org/2000/svg" style="display:none"', "</svg>\n")
    css = pieza(idx, "<style>", "</style>", incluir_ini=False)
    css = css.replace("url(fuentes/", "url(/fuentes/")
    p["css"] = css
    cab = pieza(idx, '<header class="cabecera">', "</header>\n<div class=\"menu-velo\" hidden></div>")
    cab = cab.replace('<a class="marca" href="#inicio"', '<a class="marca" href="/"')
    cab = re.sub(r'(<a\b[^>]*?\shref=")#(?=[a-z])', r"\1/#", cab)   # los enlaces del menú llevan a las secciones de la portada (los iconos <use href="#i-…"> no se tocan)
    cab = cab.replace('src="img/', 'src="/img/')
    p["cabecera"] = cab
    p["pie"] = pieza(idx, '<footer class="pie">', "</footer>").replace('src="img/', 'src="/img/')
    p["barra"] = pieza(idx, '<nav class="barra-movil"', "</nav>")
    p["agenda"] = pieza(idx, "<!-- AGENDAR UNA LLAMADA", "</dialog>")
    # La cabecera de la portada: los dos botones, «Mándanos 3 o 4 facturas…» y las tres garantías.
    p["acciones"] = sin_entra(pieza(idx, '<div class="acciones entra">', "</div>"))
    p["como_demo"] = sin_entra(pieza(idx, '<p class="como-demo entra">', "</p>"))
    p["confianza"] = sin_entra(pieza(idx, '<ul class="confianza entra">', "</ul>"))
    # «Pide tu demo con tus propias facturas»: el titular, los 3 pasos, las 3 formas de contacto y la nota, como en la portada.
    marca_nota = '<p class="nota-facturas aparece">'
    contacto = pieza(idx, '<section class="contacto bloque" id="contacto"', marca_nota)[:-len(marca_nota)]
    p["contacto"] = contacto + pieza(idx, marca_nota, "</p>") + "\n  </div>\n</section>"
    p["imagenes"] = imagenes_de_portada(idx)
    # Los guiones del final de la portada (menú, tema, agenda, WhatsApp, barra de abajo, lo que aparece al bajar)
    cola = idx[idx.index("</footer>"):]
    p["js"] = "\n".join(re.findall(r"<script>(.*?)</script>", cola, re.S))
    return p


def trocear_css(css):
    """Las reglas de primer nivel de una hoja: [(lo de antes de «{», lo de dentro)], con las llaves anidadas bien emparejadas."""
    out, i, n = [], 0, len(css)
    while i < n:
        j = css.find("{", i)
        if j < 0:
            break
        d, k = 1, j + 1
        while d and k < n:
            d += {"{": 1, "}": -1}.get(css[k], 0)
            k += 1
        out.append((css[i:j].strip(), css[j + 1:k - 1]))
        i = k
    return out


def copiar_reglas(css, de, a):
    """Copia las reglas de la portada que llevan el selector «de» (también dentro de sus @media) cambiándolo por «a».
    Así la cabecera de estas páginas se porta en el móvil como la de la portada (los dos botones en una fila…) y sigue sus cambios."""
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    salida = []
    for pre, cuerpo in trocear_css(css):
        if pre.startswith("@media"):
            dentro = [(x, c) for x, c in trocear_css(cuerpo) if de in x]
            if dentro:
                salida.append("%s{%s}" % (pre, "".join("%s{%s}" % (x.replace(de, a), c) for x, c in dentro)))
        elif not pre.startswith("@") and de in pre:
            salida.append("%s{%s}" % (pre.replace(de, a), cuerpo))
    return "\n".join(salida)


# ───────────────────────────── Estilos propios de estas páginas ─────────────────────────────
CSS_PROPIO = r"""
/* ══════════════════════════════════════════════════════════════════════════════════════════
   PÁGINAS DE CONTENIDO (SEO, nov-2026; cortas desde el 18-nov). Todo lo de arriba es la hoja de
   la portada, copiada tal cual por seo/construir.py; esto de aquí abajo es lo único propio de
   estas páginas. Mismos colores y mismas variables: claro y oscuro salen solos.
   ══════════════════════════════════════════════════════════════════════════════════════════ */
.migas{padding-top:18px}
.migas ol{list-style:none;margin:0;padding:0;display:flex;flex-wrap:wrap;align-items:center;gap:0 8px;font-size:14.5px;color:var(--texto-2)}
.migas li{display:inline-flex;align-items:center;min-height:32px}
.migas li+li::before{content:"/";margin-right:8px;color:var(--borde-fuerte)}
.migas a{color:inherit;text-decoration:underline;text-decoration-color:var(--borde-fuerte);text-underline-offset:4px}
.migas a:hover{color:var(--texto);text-decoration-color:currentColor}
.migas [aria-current]{color:var(--texto)}

/* Cabecera: el texto y, al lado (o debajo en el móvil), una imagen real */
.pagina-cab{display:grid;gap:40px;padding-block:20px 64px;align-items:center}
.pagina-cab h1{font-size:clamp(34px,8.6vw,60px);line-height:1.02;letter-spacing:-.034em;max-width:17ch;text-wrap:balance}
.pagina-cab .entradilla{max-width:42ch}
.pagina-cab .antetitulo{margin-bottom:14px}
.pagina-figura{margin:0;justify-self:center;width:100%}
.pagina-figura figcaption{margin-top:14px;font-size:14.5px;line-height:1.4;color:var(--texto-2);text-align:center}
.figura-app{max-width:540px}
.figura-app img{display:block;width:100%;height:auto;border-radius:22px;background:var(--crudo);box-shadow:0 0 0 1px var(--borde),0 30px 60px -30px color-mix(in srgb,var(--pino-claro) 55%,transparent)}
.figura-movil{position:relative;isolation:isolate;max-width:270px}
.figura-movil .movil{margin-inline:auto}
.figura-movil figcaption{margin-top:44px}
.figura-foto{max-width:600px}
.figura-foto img{display:block;width:100%;height:auto;aspect-ratio:4/3.2;object-fit:cover;border-radius:28px;background:var(--pino-profundo);box-shadow:var(--sombra-3)}
.pagina-cab.sin-figura h1{max-width:21ch}
.pagina-cab.sin-figura .entradilla{max-width:52ch}
@media (min-width:900px){
  .pagina-cab{grid-template-columns:minmax(0,1.06fr) minmax(0,.94fr);gap:64px;padding-block:32px 104px}
  .pagina-cab.sin-figura{grid-template-columns:minmax(0,1fr);padding-bottom:72px}
  .pagina-cab-texto{padding-block:12px}
}

/* Los 3-4 puntos: como las cajas de «Cuatro cosas que dejas de hacer a mano», solo con texto */
.puntos-bloque{padding-top:8px}
.puntos{display:grid;gap:14px;margin-top:32px}
.punto{margin:0;padding:26px 24px 28px;border-radius:26px;background:color-mix(in srgb,var(--niebla) 42%,var(--fondo));box-shadow:inset 0 0 0 1px color-mix(in srgb,var(--borde) 70%,transparent)}
:root[data-tema="oscuro"] .punto{background:var(--superficie)}
.punto h3{font-size:clamp(21px,5vw,25px);line-height:1.12;letter-spacing:-.022em;max-width:20ch;text-wrap:balance}
.punto p{margin-top:10px;color:var(--texto-2);font-size:16.5px;line-height:1.55;max-width:46ch}
@media (min-width:700px){.puntos-4{grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}}
@media (min-width:900px){.puntos-3{grid-template-columns:repeat(3,minmax(0,1fr));gap:18px}.punto{padding:32px 30px 34px}}

/* Las 3 preguntas: las de la portada, en una sola columna */
.preguntas-bloque{padding-top:0;padding-bottom:16px}
.preguntas-bloque .faq{grid-template-columns:1fr;max-width:820px}
.preguntas-bloque .faq details:nth-last-child(2){border-bottom:0}
.preguntas-bloque .faq details:last-child{border-bottom:1px solid var(--borde)}

/* Más de Kontrol: tres enlaces a otras páginas */
.sigue{padding-block:8px 80px}
.sigue h2{font-size:clamp(24px,5.2vw,32px)}
.sigue ul{list-style:none;margin:22px 0 0;padding:0;display:grid;gap:12px}
.sigue a{display:flex;align-items:center;justify-content:space-between;gap:16px;min-height:64px;padding:16px 20px;border-radius:20px;background:var(--superficie);background-image:linear-gradient(to bottom,color-mix(in srgb,var(--luz) 40%,transparent),transparent 40%);box-shadow:var(--filo),0 0 0 1px var(--borde),var(--sombra-1);color:var(--texto);font-weight:700;font-size:18px;line-height:1.25;text-decoration:none;transition:transform .25s var(--curva),box-shadow .25s var(--curva)}
:root[data-tema="oscuro"] .sigue a{background-image:none}
.sigue a:hover{transform:translateY(-3px);box-shadow:var(--filo),0 0 0 1px var(--borde-fuerte),var(--sombra-2)}
.sigue a .icono{color:var(--acento);transition:transform .25s var(--curva)}
.sigue a:hover .icono{transform:translateX(3px)}
@media (min-width:900px){.sigue ul{grid-template-columns:repeat(3,minmax(0,1fr))}}
@media (prefers-reduced-motion:reduce){.sigue a,.sigue a .icono{transition:none}.sigue a:hover,.sigue a:hover .icono{transform:none}}
"""

PALABRAS_PROHIBIDAS = [r"€", r"\bIA\b", r"inteligencia artificial", r"\bDAB\b", r"/precios", r"el mejor\b", r"\bel primero\b", r"\blíder"]


# ───────────────────────────── Una página ─────────────────────────────
def figura(clave, piezas, nombre):
    if clave in ("ninguna", "", None) or clave == []:
        return ""
    assert clave in IMAGENES, "%s: imagen desconocida «%s» (valen: %s)" % (nombre, clave, ", ".join(IMAGENES))
    im = piezas["imagenes"].get(clave)
    assert im, "%s: la portada ya no tiene la imagen «%s»" % (nombre, clave)
    tipo = IMAGENES[clave]
    attrs = 'src="%s" alt="%s" width="%s" height="%s" decoding="async" fetchpriority="high"' % (im["src"], im["alt"], im["w"], im["h"])
    if im["srcset"]:
        attrs += ' srcset="%s" sizes="(min-width:900px) 600px, 100vw"' % im["srcset"]
    if tipo == "movil":
        return ('<figure class="pagina-figura figura-movil"><div class="movil"><div class="pantalla"><img %s></div></div>'
                '<figcaption>%s</figcaption></figure>' % (attrs, PIE_APP))
    pie = "<figcaption>%s</figcaption>" % PIE_APP if tipo == "app" else ""
    return '<figure class="pagina-figura figura-%s"><img %s>%s</figure>' % (tipo, attrs, pie)


def construir_pagina(ruta, piezas):
    meta, cuerpo = leer_md(ruta)
    n = ruta.name
    for k in ("slug", "title", "description", "etiqueta", "h1", "imagen", "enlaces"):
        assert meta.get(k), "%s: falta «%s» en la cabecera" % (n, k)
    slug = meta["slug"]
    assert slug == ruta.stem, "%s: el slug no coincide con el nombre del fichero" % n
    assert slug in NOMBRES, "%s: página que no está en NOMBRES" % n
    url = "%s/%s/" % (DOMINIO, slug)
    nombre = NOMBRES[slug]
    avisos, pendientes = [], []

    bl = bloques(cuerpo, n)
    # Entradilla: el primer párrafo antes del primer ##. Los PENDIENTES, a comentario.
    entradilla, previo, i = None, [], 0
    while i < len(bl) and bl[i][0] != "h2":
        t, d = bl[i]
        pe = pendiente(d) if t == "p" else None
        if pe:
            previo.append(pe[0]); pendientes.append(pe[1])
        elif t == "p" and entradilla is None:
            entradilla = d
        else:
            sys.exit("%s: antes del primer ## solo va la entradilla" % n)
        i += 1
    assert entradilla, "%s: falta la entradilla" % n

    secciones = []
    while i < len(bl):
        assert bl[i][0] == "h2", "%s: se esperaba un ##" % n
        titulo, sec = bl[i][1], []
        i += 1
        while i < len(bl) and bl[i][0] != "h2":
            sec.append(bl[i]); i += 1
        secciones.append((titulo, sec))
    assert len(secciones) == 2 and secciones[1][0] == "Preguntas frecuentes", \
        "%s: tiene que haber dos ##: el de los puntos y «Preguntas frecuentes»" % n

    def pares(sec, que):
        out, actual = [], None
        for t, d in sec:
            pe = pendiente(d) if t == "p" else None
            if pe:
                previo.append(pe[0]); pendientes.append(pe[1])
            elif t == "h3":
                actual = [d, []]; out.append(actual)
            elif actual is not None:
                actual[1].append(d)
            else:
                sys.exit("%s: algo antes del primer ### en %s" % (n, que))
        for q, a in out:
            assert a, "%s: «%s» no tiene texto" % (n, q)
        return out

    titulo_puntos, puntos = secciones[0][0], pares(secciones[0][1], "los puntos")
    faq = pares(secciones[1][1], "las preguntas")
    if not 3 <= len(puntos) <= 4:
        avisos.append("%d puntos (se esperaban 3 o 4)" % len(puntos))
    if len(faq) != 3:
        avisos.append("%d preguntas (se esperaban 3)" % len(faq))

    enlaces = [enlace_interno(u) for u in meta["enlaces"]]
    for u in enlaces:
        assert u.strip("/") in NOMBRES and u.strip("/") != slug, "%s: enlaza a una página que no vale: %s" % (n, u)

    # Comprobaciones del encargo: largo y palabras que no pueden salir
    visible = [entradilla, titulo_puntos] + [x for q, a in puntos + faq for x in [q] + a]
    palabras = len(" ".join(plano(x) for x in visible).split())
    if palabras > LARGO_MAX:
        avisos.append("%d palabras (máximo %d)" % (palabras, LARGO_MAX))
    if len(meta["title"]) > 60:
        avisos.append("title de %d caracteres" % len(meta["title"]))
    if len(meta["description"]) > 160:
        avisos.append("description de %d caracteres" % len(meta["description"]))
    todo = "\n".join([meta["title"], meta["description"], meta["h1"], meta["etiqueta"]] + visible)
    for pat in PALABRAS_PROHIBIDAS:
        assert not re.search(pat, todo, re.I if pat.startswith("inteligencia") or pat.startswith("el ") else 0), \
            "%s: sale «%s», que no puede salir" % (n, pat)

    # ── HTML ──
    migas = ('<nav class="migas" aria-label="Migas de pan"><ol><li><a href="/">Kontrol</a></li>'
             '<li><span aria-current="page">%s</span></li></ol></nav>' % esc(nombre))
    fig = figura(meta["imagen"], piezas, n)
    cabecera = (
        '<header class="pagina-cab%s" id="inicio"><div class="pagina-cab-texto">'
        '<p class="antetitulo">%s</p><h1>%s</h1><p class="entradilla">%s</p>%s%s%s</div>%s</header>'
        % ("" if fig else " sin-figura", inline(meta["etiqueta"]), inline(meta["h1"]), inline(entradilla), piezas["acciones"],
           piezas["como_demo"], piezas["confianza"], fig)
    )
    puntos_html = (
        '<section class="bloque puntos-bloque" aria-labelledby="t-puntos"><div class="envoltura">'
        '<h2 id="t-puntos" class="titular">%s</h2><div class="puntos puntos-%d">%s</div></div></section>'
        % (inline(titulo_puntos), len(puntos),
           "".join('<article class="punto"><h3>%s</h3>%s</article>' % (inline(q), "".join("<p>%s</p>" % inline(x) for x in a))
                   for q, a in puntos))
    )
    faq_html = (
        '<section class="bloque preguntas-bloque" aria-labelledby="t-preguntas"><div class="envoltura">'
        '<h2 id="t-preguntas" class="titular">Lo que nos suelen preguntar.</h2><div class="faq">%s</div></div></section>'
        % "".join('<details><summary>%s<svg class="icono" aria-hidden="true"><use href="#i-chevron-down"/></svg></summary>%s</details>'
                  % (inline(q), "".join("<p>%s</p>" % inline(x) for x in a)) for q, a in faq)
    )
    sigue_html = (
        '<section class="sigue" aria-labelledby="t-sigue"><div class="envoltura"><h2 id="t-sigue">Más de Kontrol</h2><ul>%s</ul></div></section>'
        % "".join('<li><a href="%s">%s<svg class="icono" aria-hidden="true"><use href="#i-arrow-right"/></svg></a></li>'
                  % (u, esc(NOMBRES[u.strip("/")])) for u in enlaces)
    )

    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Kontrol", "item": DOMINIO + "/"},
            {"@type": "ListItem", "position": 2, "name": nombre, "item": url},
        ]},
        {"@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": plano(q), "acceptedAnswer": {"@type": "Answer", "text": " ".join(plano(x) for x in a)}}
            for q, a in faq]},
    ]}

    notas = "".join("\n" + c for c in previo)
    if meta.get("revisar"):
        notas += "\n<!-- REVISAR: %s -->" % meta["revisar"].replace("--", "—")
    pagina = """<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{titulo}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="website">
<meta property="og:locale" content="es_ES">
<meta property="og:site_name" content="Kontrol">
<meta property="og:url" content="{url}">
<meta property="og:title" content="{titulo}">
<meta property="og:description" content="{desc}">
<meta property="og:image" content="{og}">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#F5F1EA">
<link rel="icon" href="/img/favicon.png">
<link rel="apple-touch-icon" href="/img/apple-touch-icon.png">
<link rel="preload" href="/fuentes/bricolage-grotesque.woff2" as="font" type="font/woff2" crossorigin>
<script type="application/ld+json">
{ld}
</script>
{marca}
<link rel="stylesheet" href="/paginas.css">
</head>

<body>
{sprite}<a class="salta" href="#principal">Saltar al contenido</a>
{cabecera_web}
<div class="menu-velo" hidden></div>

<main id="principal">{notas}
  <div class="envoltura">
  {migas}
  {cabecera}
  </div>

  {puntos}
  {faq}
  {contacto}
  {sigue}

  {agenda}
</main>

{pie}

{barra}
<script src="/paginas.js"></script>
</body>
</html>
""".format(
        titulo=esc(meta["title"]), desc=html.escape(meta["description"], quote=True), url=url, og=OG_IMAGEN,
        ld=json.dumps(ld, ensure_ascii=False, indent=2).replace("</", "<\\/"),
        marca=piezas["marca"], sprite=piezas["sprite"], cabecera_web=piezas["cabecera"], notas=notas, migas=migas,
        cabecera=cabecera, puntos=puntos_html, faq=faq_html, contacto=piezas["contacto"], sigue=sigue_html,
        agenda=piezas["agenda"], pie=piezas["pie"], barra=piezas["barra"],
    )
    return slug, pagina, pendientes, avisos, palabras


def lastmod(rel):
    """Fecha del último commit de ese fichero; hoy si aún no está subido o tiene cambios sin guardar."""
    r = subprocess.run(["git", "log", "-1", "--format=%cs", "--", rel], cwd=RAIZ, capture_output=True, text=True).stdout.strip()
    sucio = subprocess.run(["git", "status", "--porcelain", "--", rel], cwd=RAIZ, capture_output=True, text=True).stdout.strip()
    return HOY if (sucio or not r) else r


def main():
    piezas = sacar_de_portada()
    css = ("/* GENERADO por seo/construir.py a partir de la <style> de index.html + lo propio de las páginas de contenido.\n"
           "   No se edita a mano: se vuelve a ejecutar el script. */\n" + piezas["css"].strip("\n") + "\n"
           + "/* Lo de la cabecera de la portada, para la de estas páginas (sale solo de index.html) */\n"
           + copiar_reglas(piezas["css"], ".portada .acciones", ".pagina-cab .acciones") + "\n"
           + copiar_reglas(piezas["css"], ".portada .entradilla", ".pagina-cab .entradilla") + "\n" + CSS_PROPIO)
    (WEB / "paginas.css").write_text(css, encoding="utf-8")
    js = ("/* GENERADO por seo/construir.py: los guiones del final de index.html (menú, tema claro/oscuro, agenda,\n"
          "   WhatsApp, teléfono, barra de abajo del móvil y lo que aparece al bajar). No se edita a mano. */\n" + piezas["js"].strip("\n") + "\n")
    (WEB / "paginas.js").write_text(js, encoding="utf-8")

    todas, problemas = [], []
    for ruta in sorted(TEXTOS.glob("*.md")):
        slug, pagina, pend, avisos, palabras = construir_pagina(ruta, piezas)
        carpeta = WEB / slug
        carpeta.mkdir(exist_ok=True)
        (carpeta / "index.html").write_text(pagina, encoding="utf-8")
        todas.append(slug)
        print("%-26s %3d palabras%s" % (slug, palabras, ("   ⚠ " + "; ".join(avisos)) if avisos else ""))
        problemas += ["PENDIENTE (%s): %s" % (slug, p) for p in pend]
    faltan = set(NOMBRES) - set(todas)
    assert not faltan, "faltan textos: %s" % faltan
    sobran = [d.name for d in WEB.iterdir() if d.is_dir() and (d / "index.html").exists() and d.name not in NOMBRES]
    assert not sobran, "hay páginas viejas en web/ que ya no se generan (bórralas): %s" % sobran

    # sitemap.xml: la portada y las páginas, con el día del último cambio de su texto
    filas = ['  <url><loc>%s/</loc><lastmod>%s</lastmod><changefreq>monthly</changefreq><priority>1.0</priority></url>'
             % (DOMINIO, lastmod("web/index.html"))]
    for s in NOMBRES:
        filas.append('  <url><loc>%s/%s/</loc><lastmod>%s</lastmod></url>' % (DOMINIO, s, lastmod("seo/textos/%s.md" % s)))
    (WEB / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n%s\n</urlset>\n'
                                     % "\n".join(filas), encoding="utf-8")
    for p in problemas:
        print(p)


if __name__ == "__main__":
    main()
