/* GENERADO por seo/construir.py: los guiones del final de index.html (menú, tema claro/oscuro, agenda,
   WhatsApp, teléfono y barra de abajo del móvil). No se edita a mano. */
/* ── EL DESPLEGABLE «QUÉ HACE» (en el móvil, el menú entero) ── */
(function () {
  var menu = document.getElementById("menu"), velo = document.querySelector(".menu-velo");
  var botones = document.querySelectorAll("[data-menu]"), raiz = document.documentElement;
  if (!menu) return;
  var abierto = false, ultimo = null, anchoAntes = innerWidth, tCierre = null;
  var pc = matchMedia("(min-width: 900px)");
  function colocar(b) {
    if (!pc.matches) { menu.style.removeProperty("--menu-x"); return; }
    var env = menu.querySelector(".envoltura"), caja = menu.querySelector(".menu-caja");
    var e = env.getBoundingClientRect(), estilo = getComputedStyle(env);
    var izq = e.left + parseFloat(estilo.paddingLeft), libre = e.width - parseFloat(estilo.paddingLeft) - parseFloat(estilo.paddingRight);
    var x = b.getBoundingClientRect().left - izq - 12;
    menu.style.setProperty("--menu-x", Math.max(0, Math.min(x, libre - caja.offsetWidth)) + "px");
  }
  function abrir(b, conTeclado) {
    clearTimeout(tCierre);
    ultimo = b; abierto = true;
    menu.hidden = false; velo.hidden = false;
    colocar(b);
    requestAnimationFrame(function () { menu.classList.add("abierto"); velo.classList.add("abierto"); });
    botones.forEach(function (x) { x.setAttribute("aria-expanded", "true"); });
    raiz.classList.add("menu-abierto");
    if (conTeclado) { var a = menu.querySelector("a"); if (a) a.focus(); }
  }
  function cerrar(devolverFoco) {
    if (!abierto) return;
    abierto = false;
    menu.classList.remove("abierto"); velo.classList.remove("abierto");
    botones.forEach(function (x) { x.setAttribute("aria-expanded", "false"); });
    raiz.classList.remove("menu-abierto");
    tCierre = setTimeout(function () { if (!abierto) { menu.hidden = true; velo.hidden = true; } }, 220);
    if (devolverFoco && ultimo) ultimo.focus();
  }
  botones.forEach(function (b) {
    b.addEventListener("click", function (ev) { if (abierto) cerrar(false); else abrir(b, ev.detail === 0); });
  });
  menu.addEventListener("click", function (ev) { if (ev.target.closest("a")) cerrar(false); });
  velo.addEventListener("click", function () { cerrar(false); });
  document.addEventListener("click", function (ev) {
    if (abierto && !ev.target.closest("#menu") && !ev.target.closest("[data-menu]")) cerrar(false);
  });
  document.addEventListener("keydown", function (ev) { if (ev.key === "Escape" && abierto) cerrar(true); });
  addEventListener("resize", function () { if (innerWidth !== anchoAntes) { anchoAntes = innerWidth; cerrar(false); } });

  /* Dónde estás: se marca en el menú, y la cabecera se separa del fondo al bajar */
  var cab = document.querySelector(".cabecera");
  var enlaces = menu.querySelectorAll(".menu-lista a"), destinos = [];
  enlaces.forEach(function (a) { var d = document.getElementById(a.getAttribute("href").slice(1)); if (d) destinos.push([d, a]); });
  var pendiente = false;
  function mirar() {
    pendiente = false;
    cab.classList.toggle("bajada", scrollY > 8);
    var linea = innerHeight * 0.4, actual = null;
    destinos.forEach(function (p) { var r = p[0].getBoundingClientRect(); if (r.top <= linea && r.bottom > linea) actual = p[1]; });
    enlaces.forEach(function (a) { if (a === actual) a.setAttribute("aria-current", "true"); else a.removeAttribute("aria-current"); });
  }
  addEventListener("scroll", function () { if (!pendiente) { pendiente = true; requestAnimationFrame(mirar); } }, { passive: true });
  mirar();
})();

/* ── APARECER AL LLEGAR (y el tique que se imprime línea a línea) ── */
(function () {
  window.__aparece = true;
  document.querySelectorAll(".cascada").forEach(function (g) { Array.prototype.forEach.call(g.children, function (c, i) { c.style.setProperty("--i", i); }); });
  document.querySelectorAll(".lineas").forEach(function (l) { Array.prototype.forEach.call(l.children, function (c, i) { c.style.setProperty("--l", i); }); var t = l.parentElement.querySelector(".tique-total"); if (t) t.style.setProperty("--l", l.children.length); });
  if (!document.documentElement.classList.contains("con-movimiento")) return;
  var io = new IntersectionObserver(function (es) {
    es.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add("visto"); io.unobserve(e.target); } });
  }, { rootMargin: "0px 0px -8% 0px", threshold: 0.12 });
  document.querySelectorAll(".aparece").forEach(function (el) { io.observe(el); });
})();

/* ── LA FILA DE SUBIDA DE LA FOTO: «Teresa lo está leyendo…» y, al rato, «Leído» (como en la app) ── */
(function () {
  var chips = document.querySelectorAll("[data-progreso]");
  if (!chips.length) return;
  if (matchMedia("(prefers-reduced-motion: reduce)").matches || !("IntersectionObserver" in window)) {
    chips.forEach(function (c) { c.classList.add("leido"); });
    return;
  }
  var io = new IntersectionObserver(function (es) {
    es.forEach(function (e) {
      var c = e.target;
      if (e.isIntersecting) {
        if (c._t) return;
        c.classList.remove("leido");
        c._t = setTimeout(function () { c.classList.add("leido"); c._t = null; }, 2800);
      } else { clearTimeout(c._t); c._t = null; }
    });
  }, { threshold: 0.6 });
  chips.forEach(function (c) { io.observe(c); });
})();

/* ── LA HISTORIA: en el ordenador, el paso que está a media pantalla manda en la pantalla quieta
      (se ve entera, se acerca al dato y lo rodea, y abajo lo dice); en el móvil, cada vista se acerca
      sola al verse entera. ── */
(function () {
  var hist = document.querySelector(".historia");
  if (!hist) return;
  var pasos = [].slice.call(hist.querySelectorAll(".paso"));
  var esc = hist.querySelector(".escenario");
  var planos = [].slice.call(esc.querySelectorAll(".plano"));
  var datos = [].slice.call(esc.querySelectorAll(".datos .dato"));
  var marcas = [].slice.call(esc.querySelectorAll(".escenario-progreso i"));
  var quieto = matchMedia("(prefers-reduced-motion: reduce)").matches;
  var grande = matchMedia("(min-width: 1000px)");
  var actual = -1, tZoom = null;
  function activar(i) {
    if (i === actual) return;
    actual = i;
    pasos.forEach(function (p, k) { p.classList.toggle("activo", k === i); });
    planos.forEach(function (p, k) { p.classList.toggle("activo", k === i); p.classList.remove("zoom"); });
    datos.forEach(function (d, k) { d.classList.toggle("activo", k === i); });
    marcas.forEach(function (m, k) { m.classList.toggle("activo", k === i); });
    clearTimeout(tZoom);
    /* Con menos movimiento, directamente de cerca y con el recuadro, sin viaje */
    tZoom = setTimeout(function () { if (planos[i]) planos[i].classList.add("zoom"); }, quieto ? 0 : 750);
  }
  var pendiente = false;
  function medir() {
    pendiente = false;
    if (!grande.matches) return;
    var linea = innerHeight * 0.45, mejor = 0, dist = Infinity;
    pasos.forEach(function (p, k) {
      var r = p.getBoundingClientRect();
      var d = r.top <= linea && r.bottom >= linea ? 0 : Math.min(Math.abs(r.top - linea), Math.abs(r.bottom - linea));
      if (d < dist) { dist = d; mejor = k; }
    });
    activar(mejor);
  }
  addEventListener("scroll", function () { if (!pendiente) { pendiente = true; requestAnimationFrame(medir); } }, { passive: true });
  addEventListener("resize", medir);
  if (grande.addEventListener) grande.addEventListener("change", function () { actual = -1; medir(); });
  medir();

  /* En el móvil: cada vista se acerca al verse entera y se aleja al irse */
  var vistas = hist.querySelectorAll(".paso-vista .plano");
  if (quieto || !("IntersectionObserver" in window)) { vistas.forEach(function (p) { p.classList.add("zoom"); }); return; }
  var io = new IntersectionObserver(function (es) {
    es.forEach(function (e) {
      var pl = e.target.querySelector(".plano");
      if (e.intersectionRatio >= 0.6) {
        if (!pl._t) pl._t = setTimeout(function () { pl.classList.add("zoom"); pl._t = null; }, 450);
      } else if (e.intersectionRatio < 0.25) {
        clearTimeout(pl._t); pl._t = null; pl.classList.remove("zoom");
      }
    });
  }, { threshold: [0, 0.25, 0.6, 1] });
  hist.querySelectorAll(".paso-vista").forEach(function (v) { io.observe(v); });
})();

/* ── LOS VÍDEOS: se ponen en marcha al verse y se paran al salir (con menos movimiento, quietos y con mandos) ── */
(function () {
  var clips = document.querySelectorAll("video.clip");
  if (!clips.length) return;
  if (matchMedia("(prefers-reduced-motion: reduce)").matches || !("IntersectionObserver" in window)) {
    clips.forEach(function (v) { v.controls = true; v.preload = "metadata"; });
    return;
  }
  var io = new IntersectionObserver(function (es) {
    es.forEach(function (e) {
      var v = e.target;
      if (e.isIntersecting) { v.preload = "auto"; var p = v.play(); if (p && p.catch) p.catch(function () { v.controls = true; }); }
      else v.pause();
    });
  }, { threshold: 0.35 });
  clips.forEach(function (v) { io.observe(v); });
})();

/* ── CLARO / OSCURO: se abre en círculo desde el interruptor, como en la app, y se recuerda ── */
(function () {
  var bs = document.querySelectorAll(".tema-boton"), raiz = document.documentElement;
  if (!bs.length) return;
  function pinta() {
    var o = raiz.getAttribute("data-tema") === "oscuro";
    var txt = o ? "Pasar a modo claro" : "Pasar a modo oscuro";
    bs.forEach(function (b) { b.setAttribute("aria-pressed", String(o)); b.setAttribute("aria-label", txt); b.title = txt; });
    var m = document.querySelector('meta[name="theme-color"]'); if (m) m.setAttribute("content", o ? "#16241B" : "#F5F1EA");
  }
  pinta();
  bs.forEach(function (b) {
    b.addEventListener("click", function () {
      var aOscuro = raiz.getAttribute("data-tema") !== "oscuro";
      function hacer() {
        if (aOscuro) raiz.setAttribute("data-tema", "oscuro"); else raiz.removeAttribute("data-tema");
        try { localStorage.setItem("kontrol-web-tema", aOscuro ? "oscuro" : "claro"); } catch (e) {}
        pinta();
      }
      if (!document.startViewTransition || matchMedia("(prefers-reduced-motion: reduce)").matches) { hacer(); return; }
      var r = b.getBoundingClientRect(), x = r.left + r.width / 2, y = r.top + r.height / 2;
      var fin = Math.hypot(Math.max(x, innerWidth - x), Math.max(y, innerHeight - y));
      var vt = document.startViewTransition(hacer);
      vt.ready.then(function () {
        raiz.animate({ clipPath: ["circle(0px at " + x + "px " + y + "px)", "circle(" + fin + "px at " + x + "px " + y + "px)"] },
          { duration: 650, easing: "cubic-bezier(.16,1,.3,1)", pseudoElement: "::view-transition-new(root)" });
      }).catch(function () {});
    });
  });
})();

/* ── EL FORMULARIO DE CORREO ──
   Con MARCA.formulario (el flujo que envía el correo solo), se manda sin salir de la página.
   Mientras no exista, se abre el correo de quien escribe con todo ya puesto, y se le dice. */
(function () {
  var f = document.getElementById("form-contacto");
  if (!f) return;
  var M = window.MARCA || {}, t0 = Date.now();
  var estado = f.querySelector(".estado"), boton = f.querySelector('button[type="submit"]');
  function mal(id, texto) {
    var c = document.getElementById(id).closest(".campo, .acepto");
    c.setAttribute("data-mal", "");
    var e = c.querySelector(".error"); if (e) { e.textContent = texto; e.hidden = false; }
    document.getElementById(id).setAttribute("aria-invalid", "true");
  }
  function bien(c) {
    c.removeAttribute("data-mal");
    var e = c.querySelector(".error"); if (e) e.hidden = true;
    var i = c.querySelector("input, textarea"); if (i) i.removeAttribute("aria-invalid");
  }
  f.addEventListener("input", function (ev) { var c = ev.target.closest(".campo, .acepto"); if (c && c.hasAttribute("data-mal")) bien(c); });
  f.addEventListener("change", function (ev) { var c = ev.target.closest(".acepto"); if (c && c.hasAttribute("data-mal")) bien(c); });
  function hecho(d) {
    f.hidden = true;
    var ok = document.getElementById("contacto-hecho");
    ok.hidden = false; ok.querySelector("[data-a]").textContent = d.correo; ok.focus();
  }
  f.addEventListener("submit", function (ev) {
    ev.preventDefault();
    f.querySelectorAll("[data-mal]").forEach(bien);
    estado.textContent = "";
    var d = {
      nombre: f.nombre.value.trim(), negocio: f.negocio.value.trim(), correo: f.correo.value.trim(),
      telefono: f.telefono.value.trim(), mensaje: f.mensaje.value.trim(), web: f.web.value, producto: M.producto
    };
    var fallos = [];
    if (!d.nombre) { mal("c-nombre", "Escribe tu nombre."); fallos.push("c-nombre"); }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(d.correo)) { mal("c-correo", "Escribe un correo para poder contestarte, por ejemplo nombre@correo.com."); fallos.push("c-correo"); }
    if (!f.acepto.checked) { mal("c-acepto", "Márcala para que podamos contestarte."); fallos.push("c-acepto"); }
    if (fallos.length) { document.getElementById(fallos[0]).focus(); return; }
    /* Robots: rellenan la casilla escondida o envían en un instante. Se les dice que sí y no sale nada. */
    if (d.web || Date.now() - t0 < 2500) { hecho(d); return; }
    if (M.formulario) {
      boton.disabled = true; estado.textContent = "Enviando…";
      fetch(M.formulario, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(d) })
        .then(function (r) { if (!r.ok) throw new Error(String(r.status)); estado.textContent = ""; hecho(d); })
        .catch(function () {
          estado.innerHTML = "No se ha podido enviar ahora mismo. Prueba otra vez en un momento, o escríbenos a <b></b> o por WhatsApp.";
          estado.querySelector("b").textContent = M.correo;
        })
        .then(function () { boton.disabled = false; });
      return;
    }
    var asunto = M.producto + " · contacto desde la web: " + d.nombre + (d.negocio ? " (" + d.negocio + ")" : "");
    var cuerpo = "Nombre: " + d.nombre + "\nNegocio: " + (d.negocio || "-") + "\nCorreo: " + d.correo + "\nTeléfono: " + (d.telefono || "-") + "\n\n" + (d.mensaje || "");
    location.href = "mailto:" + M.correo + "?subject=" + encodeURIComponent(asunto) + "&body=" + encodeURIComponent(cuerpo);
    estado.innerHTML = "Se ha abierto tu programa de correo con el mensaje ya escrito: solo te queda darle a enviar. Si no se ha abierto, escríbenos a <b></b>.";
    estado.querySelector("b").textContent = M.correo;
  });
})();

/* ── AGENDAR UNA LLAMADA ──
   Las horas las da el flujo de n8n (MARCA.horas) mirando el calendario «Llamadas Kontrol»: la web
   no decide nada, enseña lo que le dicen y lo vuelve a pedir cada 40 s mientras está abierta (y al
   volver a la pestaña). Al apuntarla (MARCA.agendar) n8n comprueba OTRA VEZ que sigue libre: si otra
   persona la ha cogido justo antes, se dice y se vuelven a enseñar las horas.
   Sin MARCA.horas (el artifact) o abierta como fichero: horas de ejemplo y no se apunta nada. */
(function () {
  var dlg = document.getElementById("agenda"), abrir = document.querySelectorAll("[data-agenda]");
  if (!dlg || !abrir.length) return;
  var M = window.MARCA || {}, raiz = document.documentElement;
  if (typeof dlg.showModal !== "function") {
    /* Navegadores muy viejos sin ventanas: al WhatsApp, que siempre funciona */
    abrir.forEach(function (b) { b.addEventListener("click", function () { location.href = "https://wa.me/" + M.whatsapp; }); });
    return;
  }
  var demo = !M.horas || location.protocol === "file:";
  var caja = dlg.querySelector(".agenda-caja"), aviso = dlg.querySelector(".agenda-aviso");
  var pasos = {};
  dlg.querySelectorAll("[data-paso]").forEach(function (p) { pasos[p.getAttribute("data-paso")] = p; });
  var mesNombre = dlg.querySelector(".mes-nombre"), mesDias = dlg.querySelector(".mes-dias"), flechas = dlg.querySelectorAll("[data-mes]");
  var horasDia = dlg.querySelector(".horas-dia"), horasLista = dlg.querySelector(".horas-lista");
  var horasFallo = dlg.querySelector(".horas-fallo"), horasPie = dlg.querySelector(".horas-pie"), horasEstado = dlg.querySelector(".horas-estado");
  var f = document.getElementById("form-llamada"), estado = f.querySelector(".estado"), boton = f.querySelector('button[type="submit"]');
  var fDia = new Intl.DateTimeFormat("es-ES", { weekday: "long", day: "numeric", month: "long", timeZone: "UTC" });
  var fDiaLocal = new Intl.DateTimeFormat("es-ES", { weekday: "long", day: "numeric", month: "long" });
  var fMes = new Intl.DateTimeFormat("es-ES", { month: "long", year: "numeric", timeZone: "UTC" });
  var fHora = new Intl.DateTimeFormat("es-ES", { hour: "2-digit", minute: "2-digit" });
  var fHoraMadrid = new Intl.DateTimeFormat("es-ES", { hour: "2-digit", minute: "2-digit", timeZone: "Europe/Madrid" });
  var st = { dias: [], mes: "", dia: "", hora: "", paso: "elegir", reloj: 0, pidiendo: false, t2: 0, hecha: null };

  function dos(n) { return (n < 10 ? "0" : "") + n; }
  function hoy() { var d = new Date(); return d.getFullYear() + "-" + dos(d.getMonth() + 1) + "-" + dos(d.getDate()); }
  /* Un día «AAAA-MM-DD» dicho en largo, sin que la zona horaria lo mueva: «lunes 28 de septiembre» */
  function diaLargo(fecha) { return fDia.format(new Date(fecha + "T12:00:00Z")).replace(",", ""); }
  function cuando(iso) { var t = new Date(iso); return fDiaLocal.format(t).replace(",", "") + " a las " + fHora.format(t); }
  function libres(d) { return d.horas.filter(function (h) { return h.libre; }).length; }
  function buscaDia(fecha) { return st.dias.filter(function (d) { return d.fecha === fecha; })[0] || null; }
  function buscaHora(iso) {
    for (var i = 0; i < st.dias.length; i++) for (var j = 0; j < st.dias[i].horas.length; j++) if (st.dias[i].horas[j].inicio === iso) return st.dias[i].horas[j];
    return null;
  }
  function meses() { var m = []; st.dias.forEach(function (d) { var x = d.fecha.slice(0, 7); if (m.indexOf(x) < 0) m.push(x); }); return m; }
  function decir(texto) { aviso.textContent = texto; aviso.hidden = !texto; }

  /* Horas de ejemplo (el artifact y el fichero suelto): el mismo horario, alguna ya cogida */
  function ejemplo() {
    var dias = [], ahora = Date.now(), base = new Date();
    for (var d = 0; d <= 14; d++) {
      var dia = new Date(base.getFullYear(), base.getMonth(), base.getDate() + d);
      if (dia.getDay() === 0 || dia.getDay() === 6) continue;
      var horas = [];
      [[10, 0], [10, 30], [11, 0], [11, 30], [12, 0], [12, 30], [13, 0], [16, 0], [16, 30], [17, 0], [17, 30], [18, 0], [18, 30]].forEach(function (hm, i) {
        var t = new Date(dia.getFullYear(), dia.getMonth(), dia.getDate(), hm[0], hm[1]);
        if (t.getTime() < ahora + 2 * 3600000) return;
        horas.push({ inicio: t.toISOString().replace(/\.\d{3}Z$/, "Z"), libre: (d * 7 + i * 5) % 6 !== 0 });
      });
      if (horas.length) dias.push({ fecha: dia.getFullYear() + "-" + dos(dia.getMonth() + 1) + "-" + dos(dia.getDate()), horas: horas });
    }
    return { dias: dias };
  }

  function cargar(callado) {
    if (st.pidiendo) return;
    st.pidiendo = true;
    if (!callado) { dlg.classList.add("cargando"); dlg.setAttribute("aria-busy", "true"); esqueleto(); }
    var pedir = demo
      ? new Promise(function (ok) { setTimeout(function () { ok(ejemplo()); }, 500); })
      : fetch(M.horas, { cache: "no-store" }).then(function (r) { if (!r.ok) throw new Error(String(r.status)); return r.json(); });
    pedir.then(function (d) { horasFallo.hidden = true; horasPie.hidden = false; dlg.classList.remove("cargando"); aplicar(d.dias || []); })
      .catch(function () { if (!callado || !st.dias.length) fallo(); })
      .then(function () { st.pidiendo = false; dlg.classList.remove("cargando"); dlg.removeAttribute("aria-busy"); });
  }

  function aplicar(dias) {
    var antes = st.hora;
    st.dias = dias;
    /* ¿Sigue libre la hora que tenía marcada? Si no, se dice y se vuelve a elegir */
    if (antes) {
      var h = buscaHora(antes);
      if (!h || !h.libre) {
        st.hora = "";
        decir("La hora que habías elegido la acaba de coger otra persona. Elige otra, por favor.");
        if (st.paso === "datos") ir("elegir");
      }
    }
    var d = st.dia && buscaDia(st.dia);
    if (!d || !libres(d)) {
      st.dia = "";
      for (var i = 0; i < st.dias.length; i++) if (libres(st.dias[i])) { st.dia = st.dias[i].fecha; break; }
    }
    var m = meses();
    if (st.dia) st.mes = st.dia.slice(0, 7);
    else if (m.indexOf(st.mes) < 0) st.mes = m[0] || hoy().slice(0, 7);
    pintarMes(); pintarHoras();
  }

  function pintarMes(gris) {
    var y = +st.mes.slice(0, 4), m = +st.mes.slice(5, 7) - 1, lista = meses(), donde = lista.indexOf(st.mes);
    mesNombre.textContent = fMes.format(new Date(Date.UTC(y, m, 15)));
    flechas[0].disabled = gris || donde <= 0;
    flechas[1].disabled = gris || donde < 0 || donde >= lista.length - 1;
    var hueco = (new Date(Date.UTC(y, m, 1)).getUTCDay() + 6) % 7, total = new Date(Date.UTC(y, m + 1, 0)).getUTCDate(), hoyEs = hoy();
    mesDias.textContent = "";
    for (var i = 0; i < hueco; i++) mesDias.appendChild(document.createElement("i"));
    for (var n = 1; n <= total; n++) {
      var fecha = st.mes + "-" + dos(n), d = !gris && buscaDia(fecha), el;
      if (d) {
        var l = libres(d);
        el = document.createElement("button");
        el.type = "button"; el.className = "dia" + (l ? "" : " lleno");
        el.setAttribute("data-fecha", fecha);
        el.setAttribute("aria-pressed", String(fecha === st.dia));
        el.setAttribute("aria-label", diaLargo(fecha) + (l ? ", " + l + (l === 1 ? " hora libre" : " horas libres") : ", completo"));
        if (!l) el.disabled = true;
      } else {
        el = document.createElement("span"); el.className = "dia"; el.setAttribute("aria-hidden", "true");
      }
      if (fecha === hoyEs) el.classList.add("hoy");
      el.appendChild(document.createTextNode(String(n)));
      mesDias.appendChild(el);
    }
  }

  function pintarHoras() {
    horasLista.textContent = "";
    var d = st.dia && buscaDia(st.dia);
    if (!d) { horasDia.textContent = st.dias.length ? "Ese día ya no quedan horas libres." : "No quedan horas libres estos días."; return; }
    horasDia.textContent = diaLargo(d.fecha);
    var grupos = [["Por la mañana", []], ["Por la tarde", []]];
    d.horas.forEach(function (h) { grupos[new Date(h.inicio).getHours() < 15 ? 0 : 1][1].push(h); });
    grupos.forEach(function (g) {
      if (!g[1].length) return;
      var p = document.createElement("p"); p.className = "horas-grupo"; p.textContent = g[0];
      var fila = document.createElement("div"); fila.className = "fila"; fila.setAttribute("role", "group"); fila.setAttribute("aria-label", g[0]);
      g[1].forEach(function (h) {
        var b = document.createElement("button"), txt = fHora.format(new Date(h.inicio));
        b.type = "button"; b.className = "hora"; b.textContent = txt; b.setAttribute("data-inicio", h.inicio);
        if (h.libre) b.setAttribute("aria-pressed", String(h.inicio === st.hora));
        else { b.disabled = true; b.classList.add("cogida"); b.setAttribute("aria-label", txt + ", ya cogida"); }
        fila.appendChild(b);
      });
      horasLista.appendChild(p); horasLista.appendChild(fila);
    });
    /* Quien no está en la hora de Madrid (Canarias, fuera de España) ve SU hora, y se le dice */
    var t = new Date(d.horas[0].inicio);
    horasEstado.textContent = fHora.format(t) !== fHoraMadrid.format(t) ? "Las horas van en tu hora. Las tachadas ya están cogidas." : "Las horas tachadas ya están cogidas.";
  }

  /* Mientras llegan las horas: el mes y unas horas en gris, del mismo tamaño que lo de verdad */
  function esqueleto() {
    if (!st.mes) st.mes = hoy().slice(0, 7);
    pintarMes(true);
    horasDia.textContent = "Mirando las horas libres…";
    horasLista.textContent = "";
    var fila = document.createElement("div"); fila.className = "fila"; fila.setAttribute("aria-hidden", "true");
    for (var i = 0; i < 9; i++) { var s = document.createElement("span"); s.className = "hora"; s.textContent = "00:00"; fila.appendChild(s); }
    horasLista.appendChild(fila);
  }

  function fallo() {
    horasFallo.hidden = false; horasPie.hidden = true;
    horasDia.textContent = ""; horasLista.textContent = "";
    pintarMes(true);
  }

  function ir(p) {
    st.paso = p;
    Object.keys(pasos).forEach(function (k) { pasos[k].hidden = k !== p; });
    if (p === "datos") {
      dlg.querySelector("[data-elegida-dia]").textContent = diaLargo(st.dia);
      dlg.querySelector("[data-elegida-hora]").textContent = "a las " + fHora.format(new Date(st.hora));
      st.t2 = Date.now();
    }
    caja.scrollTop = 0;
  }

  function reiniciar() { st.hora = ""; st.hecha = null; f.reset(); estado.textContent = ""; decir(""); ir("elegir"); }

  function abrirAgenda() {
    if (st.paso === "hecho") reiniciar();
    decir("");
    dlg.showModal();
    raiz.classList.add("agenda-abierta");
    if (!st.dias.length) esqueleto();
    cargar(st.dias.length > 0);
    clearInterval(st.reloj);
    st.reloj = setInterval(function () { if (!document.hidden) cargar(true); }, 40000);
  }
  abrir.forEach(function (b) { b.addEventListener("click", abrirAgenda); });
  dlg.addEventListener("close", function () { raiz.classList.remove("agenda-abierta"); clearInterval(st.reloj); });
  /* Tocar fuera del tique lo cierra (en el móvil ocupa toda la pantalla: ahí se cierra con la X) */
  dlg.addEventListener("click", function (e) { if (e.target === dlg) dlg.close(); });
  dlg.querySelectorAll("[data-cerrar]").forEach(function (b) { b.addEventListener("click", function () { dlg.close(); }); });
  document.addEventListener("visibilitychange", function () { if (dlg.open && !document.hidden) cargar(true); });
  dlg.querySelector("[data-reintentar]").addEventListener("click", function () { cargar(false); });

  mesDias.addEventListener("click", function (e) {
    var b = e.target.closest("button.dia");
    if (!b || b.disabled) return;
    st.dia = b.getAttribute("data-fecha"); st.hora = ""; decir("");
    pintarMes(); pintarHoras();
    mesDias.querySelector('[data-fecha="' + st.dia + '"]').focus();
    if (innerWidth < 760) horasDia.scrollIntoView({ block: "start", behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
  });
  flechas.forEach(function (b) {
    b.addEventListener("click", function () {
      var lista = meses(), nuevo = lista[lista.indexOf(st.mes) + Number(b.getAttribute("data-mes"))];
      if (!nuevo) return;
      st.mes = nuevo;
      if (st.dia.slice(0, 7) !== nuevo) {
        var d = st.dias.filter(function (x) { return x.fecha.slice(0, 7) === nuevo && libres(x); })[0];
        st.dia = d ? d.fecha : ""; st.hora = "";
      }
      pintarMes(); pintarHoras();
    });
  });
  horasLista.addEventListener("click", function (e) {
    var b = e.target.closest("button.hora");
    if (!b || b.disabled) return;
    st.hora = b.getAttribute("data-inicio"); decir("");
    ir("datos");
    document.getElementById("l-nombre").focus({ preventScroll: true });
  });
  dlg.querySelector("[data-volver]").addEventListener("click", function () {
    ir("elegir"); pintarHoras();
    var b = horasLista.querySelector('[aria-pressed="true"]'); if (b) b.focus();
  });

  /* El formulario: lo justo para poder llamar (nombre y teléfono), y el resto si quieren */
  function mal(id, texto) {
    var c = document.getElementById(id).closest(".campo, .acepto");
    c.setAttribute("data-mal", "");
    var e = c.querySelector(".error"); if (e) { e.textContent = texto; e.hidden = false; }
    document.getElementById(id).setAttribute("aria-invalid", "true");
  }
  function bien(c) {
    c.removeAttribute("data-mal");
    var e = c.querySelector(".error"); if (e) e.hidden = true;
    var i = c.querySelector("input, textarea"); if (i) i.removeAttribute("aria-invalid");
  }
  f.addEventListener("input", function (ev) { var c = ev.target.closest(".campo, .acepto"); if (c && c.hasAttribute("data-mal")) bien(c); });
  f.addEventListener("change", function (ev) { var c = ev.target.closest(".acepto"); if (c && c.hasAttribute("data-mal")) bien(c); });

  function hecha(d) {
    st.hecha = { inicio: st.hora, fin: new Date(new Date(st.hora).getTime() + 30 * 60000).toISOString(), tel: d.telefono };
    dlg.querySelector("[data-hecho-cuando]").textContent = cuando(st.hora);
    dlg.querySelector("[data-hecho-tel]").textContent = d.telefono;
    dlg.querySelector(".agenda-demo").hidden = !demo;
    dlg.querySelector("[data-ics]").hidden = demo;   /* en la vista previa no se puede descargar nada */
    ir("hecho");
    pasos.hecho.focus();
  }

  f.addEventListener("submit", function (ev) {
    ev.preventDefault();
    f.querySelectorAll("[data-mal]").forEach(bien);
    estado.textContent = "";
    var d = {
      inicio: st.hora, nombre: f.nombre.value.trim(), telefono: f.telefono.value.trim(), negocio: f.negocio.value.trim(),
      correo: f.correo.value.trim(), nota: f.nota.value.trim(), acepto: f.acepto.checked, web: f.web.value, producto: M.producto
    };
    var fallos = [];
    if (!d.nombre) { mal("l-nombre", "Escribe tu nombre."); fallos.push("l-nombre"); }
    if ((d.telefono.match(/\d/g) || []).length < 9) { mal("l-telefono", "Escribe un teléfono para poder llamarte, por ejemplo 600\u00a0123\u00a0456."); fallos.push("l-telefono"); }
    if (d.correo && !/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(d.correo)) { mal("l-correo", "Revisa el correo (o déjalo vacío), por ejemplo nombre@correo.com."); fallos.push("l-correo"); }
    if (!d.acepto) { mal("l-acepto", "Márcala para que podamos llamarte."); fallos.push("l-acepto"); }
    if (fallos.length) { document.getElementById(fallos[0]).focus(); return; }
    /* Robots: rellenan la casilla escondida o envían en un instante. Se les dice que sí y no sale nada. */
    if (d.web || Date.now() - st.t2 < 2000) { hecha(d); return; }
    boton.disabled = true; estado.textContent = "Apuntando la llamada…";
    if (demo) { setTimeout(function () { boton.disabled = false; estado.textContent = ""; hecha(d); }, 700); return; }
    fetch(M.agendar, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(d) })
      .then(function (r) { return r.json().catch(function () { return {}; }).then(function (j) { return { r: r, j: j }; }); })
      .then(function (x) {
        var j = x.j || {};
        if (x.r.ok && j.ok) { estado.textContent = ""; hecha(d); return; }
        if (j.motivo === "ocupada" || j.motivo === "hora") {
          estado.textContent = ""; st.hora = "";
          if (j.dias) aplicar(j.dias);
          decir(j.motivo === "ocupada" ? "Esa hora la acaba de coger otra persona. Elige otra, por favor." : "Esa hora ya no se puede coger. Elige otra, por favor.");
          ir("elegir");
          return;
        }
        if (j.motivo === "ya") { estado.textContent = "Ya tienes una llamada apuntada el " + cuando(j.inicio) + ". Si quieres cambiarla, escríbenos por WhatsApp."; return; }
        if (j.motivo === "datos") { estado.textContent = ""; mal("l-telefono", "Revisa el teléfono: tiene que ser un número al que podamos llamar."); document.getElementById("l-telefono").focus(); return; }
        throw new Error(String(x.r.status));
      })
      .catch(function () { estado.textContent = "No se ha podido apuntar ahora mismo. Prueba otra vez en un momento, o escríbenos por WhatsApp."; })
      .then(function () { boton.disabled = false; });
  });

  /* «Añadir a mi calendario»: un .ics con la llamada (el móvil lo abre con su calendario) */
  dlg.querySelector("[data-ics]").addEventListener("click", function () {
    var h = st.hecha; if (!h) return;
    function z(iso) { return iso.replace(/\.\d{3}Z$/, "Z").replace(/[-:]/g, ""); }
    function e(s) { return String(s).replace(/([,;\\])/g, "\\$1"); }
    var ics = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//" + e(M.producto) + "//Llamada//ES", "METHOD:PUBLISH", "BEGIN:VEVENT",
      "UID:" + z(h.inicio) + "-" + Math.random().toString(36).slice(2) + "@" + (location.hostname || "kontrol"),
      "DTSTAMP:" + z(new Date().toISOString()), "DTSTART:" + z(h.inicio), "DTEND:" + z(h.fin),
      "SUMMARY:" + e("Llamada de " + M.producto), "DESCRIPTION:" + e("Te llamamos al " + h.tel + "."),
      "END:VEVENT", "END:VCALENDAR"].join("\r\n");
    var a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([ics], { type: "text/calendar;charset=utf-8" }));
    a.download = "llamada-" + String(M.producto || "kontrol").toLowerCase() + ".ics";
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(function () { URL.revokeObjectURL(a.href); }, 5000);
  });
})();


(function () {
  var M = window.MARCA || {};
  document.querySelectorAll("[data-marca]").forEach(function (el) { var v = M[el.getAttribute("data-marca")]; if (v) el.textContent = v; });
  var texto = String(M.mensaje || "").replace("{producto}", M.producto);
  document.querySelectorAll("[data-wa]").forEach(function (a) { a.href = "https://wa.me/" + M.whatsapp + "?text=" + encodeURIComponent(texto); });
  document.querySelectorAll("[data-entrar]").forEach(function (a) { a.href = M.entrar; });
  var n = String(M.whatsapp || "").replace(/^34/, "");
  document.querySelectorAll("[data-telefono]").forEach(function (el) { el.textContent = n.replace(/(\d{3})(\d{3})(\d{3})/, "$1 $2 $3"); });
  document.querySelectorAll("[data-correo]").forEach(function (el) { el.textContent = M.correo; if (el.tagName === "A") el.href = "mailto:" + M.correo; });
  document.title = document.title.replace(/Kontrol/g, M.producto);
  var d = document.querySelector('meta[name="description"]');
  if (d) d.setAttribute("content", d.getAttribute("content").replace(/Kontrol/g, M.producto).replace(/Teresa/g, M.ayudante));
  /* Tema forzado desde fuera (vistas previas): #claro / #oscuro */
  function tema() {
    var h = location.hash.slice(1);
    if (h === "oscuro") document.documentElement.setAttribute("data-tema", "oscuro");
    if (h === "claro") document.documentElement.removeAttribute("data-tema");
  }
  addEventListener("hashchange", tema);
})();


/* ── v4: EL TELÉFONO SE PUEDE PULSAR Y LA BARRA DE ABAJO DEL MÓVIL ──
   El número sale de MARCA.whatsapp (el mismo que el WhatsApp). La barra aparece al pasar la
   portada y se esconde cuando ya se ve la sección de contacto, para no repetir botones. */
(function () {
  var M = window.MARCA || {};
  /* La promo: «quedan X de 10 plazas», desde MARCA.plazas; con 0 desaparece */
  var libres = Number(M.plazas), total = Number(M.plazasTotal) || 10;
  /* Con todas las plazas libres: «para los 10 primeros negocios»; en cuanto entra uno: «· quedan 7 plazas» */
  document.querySelectorAll("[data-promo-texto]").forEach(function (el) {
    el.textContent = libres < total ? "· quedan " + libres + (libres === 1 ? " plaza" : " plazas") : "para los " + total + " primeros negocios";
  });
  if (!(libres > 0)) document.querySelectorAll("[data-promo]").forEach(function (el) { el.hidden = true; });
  /* «Por correo»: se abre el correo con el asunto y el texto ya puestos; solo falta adjuntar las facturas */
  var asunto = "Demo de " + M.producto + ": mis facturas", cuerpo = "Hola,\n\nOs adjunto 3 o 4 facturas para ver cómo quedaría " + M.producto + " con los datos de mi negocio.\n\nNombre:\nNegocio:\nTeléfono:\n";
  document.querySelectorAll("[data-mail-demo]").forEach(function (a) { a.href = "mailto:" + M.correo + "?subject=" + encodeURIComponent(asunto) + "&body=" + encodeURIComponent(cuerpo); });
  if (M.whatsapp) document.querySelectorAll("[data-tel]").forEach(function (a) { a.href = "tel:+" + M.whatsapp; });
  var barra = document.querySelector(".barra-movil");
  if (!barra) return;
  document.body.classList.add("con-barra");
  var portada = document.getElementById("inicio"), contacto = document.getElementById("contacto");
  var pendiente = false;
  function mirar() {
    pendiente = false;
    var pasada = portada.getBoundingClientRect().bottom < 80;
    var r = contacto.getBoundingClientRect(), enContacto = r.top < innerHeight * 0.85 && r.bottom > 0;
    barra.classList.toggle("visible", pasada && !enContacto);
  }
  addEventListener("scroll", function () { if (!pendiente) { pendiente = true; requestAnimationFrame(mirar); } }, { passive: true });
  addEventListener("resize", mirar);
  mirar();
})();
