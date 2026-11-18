#!/usr/bin/env python3
"""Monta las páginas de contenido de kontrolapp.es (SEO, fase 1) a partir de los textos de seo/textos/*.md.

Uso, desde la raíz del repo:   python3 seo/construir.py

Qué hace:
  · web/<slug>/index.html por cada seo/textos/<slug>.md (URL limpia: /escandallos/).
  · web/paginas.css y web/paginas.js: la hoja de estilos y los guiones de la PORTADA (web/index.html) copiados
    tal cual, más lo propio de las páginas de texto. Se SACAN de index.html cada vez que se ejecuta: si Luis
    o Pablo cambian la cabecera, el menú, los colores o el «Pide tu demo» de la portada, basta volver a
    ejecutar esto y las páginas de texto los siguen (no hay que tocar nada a mano).
  · web/sitemap.xml con todas las direcciones y su lastmod.

Los textos NO se reescriben: Markdown → HTML y nada más. Los «[PENDIENTE DE PABLO: …]» pasan a comentario HTML.
Solo usa la biblioteca estándar.
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

# Nombre corto de cada página (migas de pan) y el orden en el pie.
NOMBRES = {
    "escandallos": "Escandallos",
    "facturas-y-albaranes": "Facturas y albaranes",
    "almacen-y-merma": "Almacén y merma",
    "personal-y-nominas": "Personal y nóminas",
    "ventas-y-cierres-de-caja": "Ventas y cierres de caja",
    "precios": "Precios",
    "restaurantes-y-bares": "Restaurantes y bares",
    "tiendas": "Tiendas",
    "menorca-y-baleares": "Menorca y Baleares",
    "verifactu": "Verifactu",
}


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
    codigos = []
    t = re.sub(r"`([^`]+)`", lambda m: (codigos.append(m.group(1)), "\x01%d\x01" % (len(codigos) - 1))[1], t)
    t = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", lambda m: '<a href="%s">%s</a>' % (enlace_interno(m.group(2)), m.group(1)), t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<![\*\w])\*(?!\s)([^*]+?)(?<!\s)\*(?![\*\w])", r"<em>\1</em>", t)
    t = re.sub(r"\x01(\d+)\x01", lambda m: "<code>%s</code>" % codigos[int(m.group(1))], t)
    return t.replace("\x00", "*")


def plano(t):
    """El mismo texto sin marcas, para el JSON-LD."""
    t = t.replace("VERI*FACTU", "VERI\x00FACTU")
    t = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", t)
    t = re.sub(r"\*\*(.+?)\*\*", r"\1", t)
    t = re.sub(r"(?<![\*\w])\*(?!\s)([^*]+?)(?<!\s)\*(?![\*\w])", r"\1", t)
    t = t.replace("`", "")
    return t.replace("\x00", "*")


def slug_titulo(t):
    t = plano(t).lower()
    t = (t.replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u").replace("ü", "u").replace("ñ", "n"))
    t = re.sub(r"[^a-z0-9]+", "-", t).strip("-")
    return t[:60].strip("-") or "seccion"


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


def bloques(cuerpo):
    """Trocea el cuerpo en bloques: (tipo, datos)."""
    out, lineas, i = [], cuerpo.split("\n"), 0
    while i < len(lineas):
        l = lineas[i]
        if not l.strip():
            i += 1
            continue
        if l.startswith("### "):
            out.append(("h3", l[4:].strip())); i += 1
        elif l.startswith("## "):
            out.append(("h2", l[3:].strip())); i += 1
        elif l.startswith("# "):
            out.append(("h1", l[2:].strip())); i += 1
        elif l.strip() == "---":
            sys.exit("raya --- suelta en el cuerpo: no la sé pintar")
        elif l.startswith("|"):
            filas = []
            while i < len(lineas) and lineas[i].startswith("|"):
                filas.append(lineas[i]); i += 1
            out.append(("tabla", filas))
        elif re.match(r"^- ", l):
            items = []
            while i < len(lineas) and lineas[i].strip() and (lineas[i].startswith("- ") or lineas[i].startswith("  ")):
                if lineas[i].startswith("- "):
                    items.append(lineas[i][2:].strip())
                else:
                    items[-1] += " " + lineas[i].strip()
                i += 1
            out.append(("lista", items))
        elif re.match(r"^\d+\. ", l):
            sys.exit("lista numerada: no la sé pintar (%s)" % l[:40])
        else:
            par = []
            while i < len(lineas) and lineas[i].strip() and not re.match(r"^(#|\||- |\d+\. )", lineas[i]):
                par.append(lineas[i].strip()); i += 1
            out.append(("p", " ".join(par)))
    return out


def celdas(fila):
    return [c.strip() for c in fila.strip().strip("|").split("|")]


def pinta_tabla(filas, nombre):
    cab, cuerpo = celdas(filas[0]), [celdas(f) for f in filas[2:]]
    n = len(cab)
    # Una columna «de cifras» si todo lo que lleva empieza por número, signo o %, y alguna celda no está vacía.
    def numerica(j):
        vals = [f[j] for f in cuerpo if j < len(f) and f[j]]
        return bool(vals) and all(re.match(r"^\**[\d−+\-]", v) for v in vals)
    num = [j > 0 and numerica(j) for j in range(n)]
    h = ['<div class="tabla-caja" role="region" tabindex="0" aria-label="%s"><table><thead><tr>' % esc(nombre)]
    for j, c in enumerate(cab):
        h.append('<th scope="col"%s>%s</th>' % (' class="num"' if num[j] else "", inline(c)))
    h.append("</tr></thead><tbody>")
    for f in cuerpo:
        h.append('<tr class="total">' if f and f[0].startswith("**") else "<tr>")
        for j in range(n):
            c = f[j] if j < len(f) else ""
            if j == 0 and c:
                h.append('<th scope="row">%s</th>' % inline(c))
            else:
                h.append("<td%s>%s</td>" % (' class="num"' if num[j] else "", inline(c)))
        h.append("</tr>")
    h.append("</tbody></table></div>")
    return "".join(h), n


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
    for a in ("como", "teresa", "preguntas"):
        cab = cab.replace('href="#%s"' % a, 'href="/#%s"' % a)
    cab = cab.replace('href="#precios"', 'href="/precios/"')
    cab = cab.replace('src="img/', 'src="/img/')
    p["cabecera"] = cab
    p["pie"] = pieza(idx, '<footer class="pie">', "</footer>").replace('src="img/', 'src="/img/')
    p["barra"] = pieza(idx, '<nav class="barra-movil"', "</nav>")
    p["agenda"] = pieza(idx, "<!-- AGENDAR UNA LLAMADA", "</dialog>")
    p["canales"] = pieza(idx, '<div class="canales">', "</div>\n      <p class=\"nota-facturas")[:-len('\n      <p class="nota-facturas')]
    # Los guiones del final de la portada (menú, tema, agenda, WhatsApp, barra de abajo)
    cola = idx[idx.index("</footer>"):]
    p["js"] = "\n".join(re.findall(r"<script>(.*?)</script>", cola, re.S))
    return p


# ───────────────────────────── Estilos y guiones propios de estas páginas ─────────────────────────────
CSS_PROPIO = r"""
/* ══════════════════════════════════════════════════════════════════════════════════════════
   PÁGINAS DE TEXTO (SEO, nov-2026). Todo lo de arriba es la hoja de la portada, copiada tal cual
   por seo/construir.py; esto de aquí abajo es lo único propio de estas páginas. Mismos colores,
   mismas variables: claro y oscuro salen solos.
   ══════════════════════════════════════════════════════════════════════════════════════════ */
.migas{padding-top:18px}
.migas ol{list-style:none;margin:0;padding:0;display:flex;flex-wrap:wrap;align-items:center;gap:0 8px;font-size:14.5px;color:var(--texto-2)}
.migas li{display:inline-flex;align-items:center;min-height:32px}
.migas li+li::before{content:"/";margin-right:8px;color:var(--borde-fuerte)}
.migas a{color:inherit;text-decoration:underline;text-decoration-color:var(--borde-fuerte);text-underline-offset:4px}
.migas a:hover{color:var(--texto);text-decoration-color:currentColor}
.migas [aria-current]{color:var(--texto)}

.pagina{max-width:780px;margin-inline:auto}
.pagina-cab{padding-block:22px 6px}
.pagina-cab h1{font-size:clamp(31px,7.2vw,52px);line-height:1.04;letter-spacing:-.03em;max-width:25ch}
.pagina-cab .entradilla{max-width:58ch;font-size:clamp(18px,4.6vw,21px);margin-top:20px}
.pagina-cab .acciones{margin-top:26px}

.texto{padding-top:44px;padding-bottom:12px;font-size:18px;line-height:1.65}
.texto > :first-child{margin-top:0}
.texto h2{font-size:clamp(26px,5.6vw,36px);line-height:1.1;margin:60px 0 6px;max-width:26ch}
.texto h3{font-size:clamp(19px,4.6vw,22px);line-height:1.25;letter-spacing:-.012em;margin:32px 0 2px}
.texto p{margin-top:14px;max-width:66ch}
.texto h2 + p,.texto h3 + p{margin-top:12px}
.texto a{color:var(--acento-texto);text-decoration:underline;text-decoration-thickness:1px;text-underline-offset:4px;transition:color .2s ease}
.texto a:hover{color:var(--texto)}
.texto em{color:var(--texto-2)}
.texto .nota-ejemplo{color:var(--texto-2);font-size:16px;margin-top:22px}
.texto ul{list-style:none;margin:14px 0 0;padding:0;max-width:66ch;display:grid;gap:8px}
.texto ul li{position:relative;padding-left:26px}
.texto ul li::before{content:"";position:absolute;left:4px;top:.72em;width:8px;height:8px;border-radius:50%;background:var(--acento)}
.texto code{font-size:.9em;padding:1px 6px;border-radius:6px;background:var(--acento-sutil)}

/* Las tablas de ejemplo: el scroll de lado es solo de la tabla, nunca de la página */
.tabla-caja{margin:18px 0 6px;max-width:100%;overflow-x:auto;overscroll-behavior-x:contain;border-radius:18px;background:var(--superficie);box-shadow:var(--filo),0 0 0 1px var(--borde),var(--sombra-1);-webkit-overflow-scrolling:touch}
.tabla-caja table{width:100%;min-width:480px;border-collapse:collapse;font-size:16px;line-height:1.4;font-variant-numeric:tabular-nums}
.tabla-caja th,.tabla-caja td{padding:12px 16px;text-align:left;vertical-align:top;border-bottom:1px solid var(--borde)}
.tabla-caja thead th{font-size:12.5px;font-weight:700;letter-spacing:.09em;text-transform:uppercase;color:var(--texto-2);background:var(--superficie-alt);white-space:nowrap}
.tabla-caja tbody th{font-weight:400}
.tabla-caja .num{text-align:right}
.tabla-caja td.num{white-space:nowrap}
.tabla-caja tbody tr:last-child > *{border-bottom:0}
.tabla-caja tr.total{background:var(--acento-sutil)}
.tabla-caja tr.total > *,.tabla-caja strong{font-weight:700}
.tabla-caja:focus-visible{outline-offset:2px}

.texto .faq{margin-top:24px;grid-template-columns:1fr}
.texto .faq details:nth-last-child(2){border-bottom:0}
.texto .faq details:last-child{border-bottom:1px solid var(--borde)}
.texto .faq details p{max-width:62ch;margin-top:0}
.texto .faq details ul{padding-bottom:20px;color:var(--texto-2)}
.texto .faq summary{font-size:clamp(17px,4.4vw,19px)}
.texto .faq a{color:var(--acento-texto)}

.contacto.demo-pagina .titular{max-width:22ch}
.contacto.demo-pagina .explica{max-width:62ch}
.contacto .nota-facturas{margin-top:18px;font-size:14.5px;color:var(--texto-2)}

.sigue{padding-block:8px 72px}
.sigue h2{font-size:clamp(26px,5.4vw,36px)}
.sigue ul{list-style:none;margin:24px 0 0;padding:0;display:grid;gap:12px}
.sigue a{display:flex;align-items:center;justify-content:space-between;gap:16px;min-height:64px;padding:16px 20px;border-radius:20px;background:var(--superficie);background-image:linear-gradient(to bottom,color-mix(in srgb,var(--luz) 40%,transparent),transparent 40%);box-shadow:var(--filo),0 0 0 1px var(--borde),var(--sombra-1);color:var(--texto);font-weight:700;font-size:18px;line-height:1.25;text-decoration:none;transition:transform .25s var(--curva),box-shadow .25s var(--curva)}
:root[data-tema="oscuro"] .sigue a{background-image:none}
.sigue a:hover{transform:translateY(-3px);box-shadow:var(--filo),0 0 0 1px var(--borde-fuerte),var(--sombra-2)}
.sigue a .icono{color:var(--acento);transition:transform .25s var(--curva)}
.sigue a:hover .icono{transform:translateX(3px)}
@media (min-width:700px){.sigue ul{grid-template-columns:1fr 1fr}}

@media (min-width:900px){.contacto.demo-pagina.bloque{padding-block:96px}.texto h2{margin-top:72px}}
"""



# ───────────────────────────── Una página ─────────────────────────────
def construir_pagina(ruta, piezas):
    meta, cuerpo = leer_md(ruta)
    slug = meta["slug"]
    assert slug == ruta.stem, "el slug no coincide con el nombre del fichero: " + ruta.name
    h1 = meta["h1"]
    bl = bloques(cuerpo)
    assert bl[0] == ("h1", h1), "%s: el H1 del cuerpo no es el de la cabecera" % ruta.name
    bl = bl[1:]
    url = "%s/%s/" % (DOMINIO, slug)
    nombre = NOMBRES[slug]
    pendientes = []

    # Entradilla: el primer párrafo; los PENDIENTES que haya antes del primer h2 se quedan como comentarios.
    entradilla, previo, extra, i = None, [], [], 0
    while i < len(bl) and bl[i][0] != "h2":
        t, d = bl[i]
        pe = pendiente(d) if t == "p" else None
        if pe:
            previo.append(pe[0]); pendientes.append(pe[1])
        elif t == "p" and entradilla is None:
            entradilla = d
        else:
            extra.append((t, d))        # lo que siga a la entradilla (p. ej. la nota de fechas de Verifactu), antes del primer ##
        i += 1
    resto = bl[i:]

    cuerpo_html, faq, demo, sigue = [], [], None, []
    if extra:
        cuerpo_html.append(pinta_bloques(extra, pendientes, "Introducción"))
    j = 0
    while j < len(resto):
        t, d = resto[j]
        assert t == "h2", "%s: se esperaba un ## y hay %s" % (ruta.name, t)
        titulo = d
        j += 1
        sec = []
        while j < len(resto) and resto[j][0] != "h2":
            sec.append(resto[j]); j += 1
        if titulo == "Preguntas frecuentes":
            q = None
            for t2, d2 in sec:
                if t2 == "h3":
                    q = {"q": d2, "a": [], "p": []}; faq.append(q)
                elif q is not None:
                    q["a"].append((t2, d2))
                else:
                    sys.exit("%s: algo antes de la primera pregunta" % ruta.name)
        elif titulo == "Pide tu demo":
            demo = [d2 for t2, d2 in sec if t2 == "p"]
            assert len(demo) == 1 and len(sec) == 1, "%s: «Pide tu demo» debe ser un párrafo" % ruta.name
        elif titulo == "Sigue leyendo":
            assert len(sec) == 1 and sec[0][0] == "lista"
            for it in sec[0][1]:
                m = re.match(r"^\[(.+?)\]\((/[^)]+)\)$", it)
                assert m, "%s: «Sigue leyendo» con un elemento raro: %s" % (ruta.name, it)
                sigue.append((m.group(1), enlace_interno(m.group(2))))
        else:
            cuerpo_html.append('<h2 id="%s">%s</h2>' % (slug_titulo(titulo), inline(titulo)))
            cuerpo_html.append(pinta_bloques(sec, pendientes, titulo))
    assert demo and sigue, "%s: faltan «Pide tu demo» o «Sigue leyendo»" % ruta.name
    for _, u in sigue:
        assert u.strip("/") in NOMBRES, "%s: enlaza a una página que no existe: %s" % (ruta.name, u)

    # Preguntas frecuentes (en la página, como la portada: <details>)
    faq_html, faq_ld = [], []
    for q in faq:
        partes = pinta_bloques(q["a"], pendientes, q["q"])
        faq_html.append('<details><summary>%s<svg class="icono" aria-hidden="true"><use href="#i-chevron-down"/></svg></summary>%s</details>' % (inline(q["q"]), partes))
        txt = []
        for t2, d2 in q["a"]:
            txt.extend([plano(x) for x in d2] if t2 == "lista" else [plano(d2)])
        faq_ld.append({"@type": "Question", "name": plano(q["q"]), "acceptedAnswer": {"@type": "Answer", "text": " ".join(txt)}})
    if faq:
        cuerpo_html.append('<h2 id="preguntas-frecuentes">Preguntas frecuentes</h2><div class="faq">%s</div>' % "".join(faq_html))

    # «Pide tu demo»: el párrafo del .md, con el correo y el teléfono pulsables, y los tres canales de la portada
    d = inline(demo[0])
    d = d.replace("ventas@kontrolapp.es", '<a data-correo href="mailto:ventas@kontrolapp.es">ventas@kontrolapp.es</a>')
    d = d.replace("686 679 713", '<a data-tel href="tel:+34686679713"><span data-telefono>686 679 713</span></a>')
    demo_html = (
        '<section class="contacto bloque demo-pagina" id="contacto" aria-labelledby="t-contacto"><div class="envoltura">'
        '<h2 id="t-contacto" class="titular">Pide tu demo</h2><p class="explica">%s</p>%s'
        '<p class="nota-facturas">Tus facturas solo las usamos para preparar tu demo.</p></div></section>' % (d, piezas["canales"])
    )
    sigue_html = (
        '<section class="sigue" aria-labelledby="t-sigue"><div class="envoltura"><h2 id="t-sigue" class="titular" style="max-width:none">Sigue leyendo</h2><ul>%s</ul></div></section>'
        % "".join('<li><a href="%s">%s<svg class="icono" aria-hidden="true"><use href="#i-arrow-right"/></svg></a></li>' % (u, inline(t)) for t, u in sigue)
    )

    # Cabecera de las páginas de texto
    ent_html = '<p class="entradilla">%s</p>' % inline(entradilla)
    hero = (
        '<header class="pagina-cab" id="inicio"><h1>%s</h1>%s'
        '<div class="acciones"><a class="boton" data-wa href="https://wa.me/34686679713" target="_blank" rel="noopener"><svg class="icono" aria-hidden="true"><use href="#i-message-circle"/></svg>Pide tu demo gratis</a>'
        '<a class="boton boton-borde" data-mail-demo href="mailto:ventas@kontrolapp.es"><svg class="icono" aria-hidden="true"><use href="#i-mail"/></svg>Por correo</a></div></header>'
        % (inline(h1), ent_html)
    )
    migas = (
        '<nav class="migas" aria-label="Migas de pan"><ol><li><a href="/">Kontrol</a></li><li><span aria-current="page">%s</span></li></ol></nav>' % esc(nombre)
    )

    ld = {
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "BreadcrumbList", "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Kontrol", "item": DOMINIO + "/"},
                {"@type": "ListItem", "position": 2, "name": nombre, "item": url},
            ]},
        ],
    }
    if faq_ld:
        ld["@graph"].append({"@type": "FAQPage", "mainEntity": faq_ld})

    titulo, desc = meta["title"], meta["description"]
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
{cabecera}
<div class="menu-velo" hidden></div>

<main id="principal">
  <article class="pagina envoltura">
  {migas}
  {hero}
  <div class="texto">{notas}
{cuerpo}
  </div>
  </article>

  {demo}
  {sigue}

  {agenda}
</main>

{pie}

{barra}
<script src="/paginas.js"></script>
</body>
</html>
""".format(
        titulo=esc(titulo), desc=html.escape(desc, quote=True), url=url, og=OG_IMAGEN,
        ld=json.dumps(ld, ensure_ascii=False, indent=2).replace("</", "<\\/"),
        marca=piezas["marca"], sprite=piezas["sprite"], cabecera=piezas["cabecera"], migas=migas, hero=hero,
        notas=notas, cuerpo="\n".join(cuerpo_html), demo=demo_html, sigue=sigue_html, agenda=piezas["agenda"],
        pie=piezas["pie"], barra=piezas["barra"],
    )
    return slug, pagina, pendientes


def pinta_bloques(sec, pendientes, contexto):
    h = []
    for t, d in sec:
        if t == "h3":
            h.append('<h3>%s</h3>' % inline(d))
        elif t == "p":
            pe = pendiente(d)
            if pe:
                h.append(pe[0]); pendientes.append(pe[1])
            elif re.match(r"^\*[^*].*[^*]\*$", d) and d.count("*") == 2:
                h.append('<p class="nota-ejemplo">%s</p>' % inline(d))
            else:
                h.append("<p>%s</p>" % inline(d))
        elif t == "lista":
            h.append("<ul>%s</ul>" % "".join("<li>%s</li>" % inline(x) for x in d))
        elif t == "tabla":
            th, _ = pinta_tabla(d, "Ejemplo: " + plano(contexto))
            h.append(th)
        else:
            sys.exit("bloque no previsto: " + t)
    return "".join(h)


def lastmod(rel):
    """Fecha del último commit de ese fichero; hoy si aún no está subido o tiene cambios sin guardar."""
    r = subprocess.run(["git", "log", "-1", "--format=%cs", "--", rel], cwd=RAIZ, capture_output=True, text=True).stdout.strip()
    sucio = subprocess.run(["git", "status", "--porcelain", "--", rel], cwd=RAIZ, capture_output=True, text=True).stdout.strip()
    return HOY if (sucio or not r) else r


def main():
    piezas = sacar_de_portada()
    # CSS y JS compartidos
    css = ("/* GENERADO por seo/construir.py a partir de la <style> de index.html + lo propio de las páginas de texto.\n"
           "   No se edita a mano: se vuelve a ejecutar el script. */\n" + piezas["css"].strip("\n") + "\n" + CSS_PROPIO)
    (WEB / "paginas.css").write_text(css, encoding="utf-8")
    js = ("/* GENERADO por seo/construir.py: los guiones del final de index.html (menú, tema claro/oscuro, agenda,\n"
          "   WhatsApp, teléfono y barra de abajo del móvil). No se edita a mano. */\n" + piezas["js"].strip("\n") + "\n")
    (WEB / "paginas.js").write_text(js, encoding="utf-8")

    todas, pendientes = [], {}
    for ruta in sorted(TEXTOS.glob("*.md")):
        slug, pagina, pend = construir_pagina(ruta, piezas)
        carpeta = WEB / slug
        carpeta.mkdir(exist_ok=True)
        (carpeta / "index.html").write_text(pagina, encoding="utf-8")
        todas.append(slug)
        if pend:
            pendientes[slug] = pend
    faltan = set(NOMBRES) - set(todas)
    assert not faltan, "faltan textos: %s" % faltan

    # sitemap.xml: la portada y las páginas, con el día del último cambio de su texto
    lm_portada = lastmod("web/index.html")
    orden = ["escandallos", "facturas-y-albaranes", "almacen-y-merma", "personal-y-nominas", "ventas-y-cierres-de-caja",
             "precios", "restaurantes-y-bares", "tiendas", "menorca-y-baleares", "verifactu"]
    filas = ['  <url><loc>%s/</loc><lastmod>%s</lastmod><changefreq>monthly</changefreq><priority>1.0</priority></url>' % (DOMINIO, lm_portada)]
    for s in orden:
        filas.append('  <url><loc>%s/%s/</loc><lastmod>%s</lastmod></url>' % (DOMINIO, s, lastmod("seo/textos/%s.md" % s)))
    (WEB / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n%s\n</urlset>\n' % "\n".join(filas), encoding="utf-8")

    print("Páginas:", ", ".join(todas))
    for s, ps in pendientes.items():
        for p in ps:
            print("PENDIENTE (%s): %s" % (s, p))


if __name__ == "__main__":
    main()
