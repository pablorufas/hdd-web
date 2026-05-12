// HdD — interacciones mínimas
(function () {

  /* ── Reloj en vivo (cabecera + hero) ────────────────────── */
  var clocks = document.querySelectorAll("[data-live-clock]");
  if (clocks.length) {
    var update = function () {
      var d = new Date();
      var hh = String(d.getHours()).padStart(2, "0");
      var mm = String(d.getMinutes()).padStart(2, "0");
      var sep = d.getSeconds() % 2 === 0 ? ":" : " ";
      var txt = hh + sep + mm;
      clocks.forEach(function (el) { el.textContent = txt; });
    };
    update();
    setInterval(update, 1000);
  }

  /* ── Nav móvil ───────────────────────────────────────────── */
  var toggle = document.querySelector(".nav-toggle");
  var nav    = document.querySelector(".nav");

  function closeNav() {
    nav.classList.remove("open");
    toggle.setAttribute("aria-expanded", "false");
    toggle.setAttribute("aria-label", "Abrir menú");
    toggle.textContent = "☰";
    document.body.classList.remove("nav-open");
  }

  function openNav() {
    nav.classList.add("open");
    toggle.setAttribute("aria-expanded", "true");
    toggle.setAttribute("aria-label", "Cerrar menú");
    toggle.textContent = "✕";
    document.body.classList.add("nav-open");
  }

  if (toggle && nav) {
    toggle.addEventListener("click", function () {
      nav.classList.contains("open") ? closeNav() : openNav();
    });

    // Cerrar al hacer clic en cualquier enlace del menú
    nav.querySelectorAll("a").forEach(function (link) {
      link.addEventListener("click", closeNav);
    });

    // Cerrar con Escape
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && nav.classList.contains("open")) {
        closeNav();
        toggle.focus();
      }
    });
  }

  /* ── Fecha de hoy (opcional, para elementos con data-today) ─ */
  document.querySelectorAll("[data-today]").forEach(function (el) {
    var d  = new Date();
    var dd = String(d.getDate()).padStart(2, "0");
    var mm = String(d.getMonth() + 1).padStart(2, "0");
    var yy = String(d.getFullYear()).slice(-2);
    el.textContent = dd + "·" + mm + "·" + yy;
  });

  /* ── Sistema de diapositivas ─────────────────────────────── */
  var slidesView = document.getElementById("slides-view");
  if (slidesView) {
    var slides        = Array.from(slidesView.querySelectorAll(".slide"));
    var progressFill  = slidesView.querySelector(".slide-progress-fill");
    var dotsWrap      = slidesView.querySelector(".slide-dots");
    var counter       = slidesView.querySelector(".slide-counter");
    var prevBtn       = slidesView.querySelector(".slide-nav__btn--prev");
    var nextBtn       = slidesView.querySelector(".slide-nav__btn--next");
    var total         = slides.length;
    var current       = 0;
    var isAnimating   = false;

    /* Construir dots */
    if (dotsWrap) {
      slides.forEach(function (_, i) {
        var dot = document.createElement("button");
        dot.className = "slide-dot" + (i === 0 ? " is-active" : "");
        dot.setAttribute("aria-label", "Ir a diapositiva " + (i + 1));
        dot.setAttribute("role", "tab");
        dot.setAttribute("aria-selected", i === 0 ? "true" : "false");
        dot.addEventListener("click", function () { goTo(i); });
        dotsWrap.appendChild(dot);
      });
    }

    function goTo(index) {
      if (index === current || isAnimating) return;
      isAnimating = true;

      var prevSlide = slides[current];
      prevSlide.classList.remove("is-active");
      prevSlide.classList.add("is-exiting");
      setTimeout(function () { prevSlide.classList.remove("is-exiting"); }, 350);

      current = index;
      slides[current].classList.add("is-active");
      slides[current].scrollTop = 0;
      window.scrollTo(0, 0);

      /* Actualizar UI */
      if (progressFill) progressFill.style.width = ((current + 1) / total * 100) + "%";
      if (counter)      counter.textContent = (current + 1) + "/" + total;

      if (dotsWrap) dotsWrap.querySelectorAll(".slide-dot").forEach(function (d, i) {
        d.classList.toggle("is-active", i === current);
        d.setAttribute("aria-selected", i === current ? "true" : "false");
      });

      if (prevBtn) prevBtn.disabled = current === 0;
      if (nextBtn) nextBtn.disabled = current === total - 1;

      setTimeout(function () { isAnimating = false; }, 400);
    }

    if (prevBtn) prevBtn.addEventListener("click", function () { if (current > 0) goTo(current - 1); });
    if (nextBtn) nextBtn.addEventListener("click", function () { if (current < total - 1) goTo(current + 1); });

    /* Teclado */
    document.addEventListener("keydown", function (e) {
      if (slidesView.classList.contains("mode-flow")) return;
      if (e.key === "ArrowRight" || e.key === "ArrowDown") {
        if (current < total - 1) { e.preventDefault(); goTo(current + 1); }
      }
      if (e.key === "ArrowLeft" || e.key === "ArrowUp") {
        if (current > 0) { e.preventDefault(); goTo(current - 1); }
      }
    });

    /* Swipe táctil */
    var touchX = 0, touchY = 0;
    slidesView.addEventListener("touchstart", function (e) {
      touchX = e.touches[0].clientX;
      touchY = e.touches[0].clientY;
    }, { passive: true });
    slidesView.addEventListener("touchend", function (e) {
      if (slidesView.classList.contains("mode-flow")) return;
      var dx = touchX - e.changedTouches[0].clientX;
      var dy = Math.abs(touchY - e.changedTouches[0].clientY);
      if (Math.abs(dx) > 50 && dy < 80) {
        if (dx > 0 && current < total - 1) goTo(current + 1);
        if (dx < 0 && current > 0) goTo(current - 1);
      }
    }, { passive: true });

    /* Toggle modo de lectura */
    document.querySelectorAll(".mode-btn").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var mode = btn.dataset.mode;
        document.querySelectorAll(".mode-btn").forEach(function (b) {
          b.classList.toggle("is-active", b.dataset.mode === mode);
        });
        if (mode === "flow") {
          slidesView.classList.add("mode-flow");
          /* Forzar visibilidad de todas las slides en modo texto */
          slides.forEach(function (s) {
            s.style.opacity    = "1";
            s.style.transform  = "none";
            s.style.transition = "none";
          });
        } else {
          slidesView.classList.remove("mode-flow");
          /* Restaurar estado de slides: solo la activa visible */
          slides.forEach(function (s, i) {
            s.style.opacity    = "";
            s.style.transform  = "";
            s.style.transition = "";
            s.classList.toggle("is-active", i === current);
          });
        }
      });
    });

    /* Init: activar primera slide */
    slides[0].classList.add("is-active");
    if (prevBtn) prevBtn.disabled = true;
    if (progressFill) progressFill.style.width = (1 / total * 100) + "%";
    if (counter) counter.textContent = "1/" + total;
  }

})();

/* ── Retention bar (artículos: 30s orgánico, 10s social) ─────── */
(function () {
  var KEY = 'hdd-ret-v1';
  if (sessionStorage.getItem(KEY)) return;
  var path = location.pathname;
  var isArticle = path !== '/' && path !== '/index.html' &&
    path !== '/noticias.html' && path !== '/educacion.html' &&
    path !== '/newsletter.html' && path !== '/manifiesto.html' &&
    path.indexOf('.html') > -1;
  if (!isArticle) return;

  // Detectar tráfico social para ajustar timing y mensaje
  var ref = document.referrer || '';
  var isSocial = /instagram|facebook|fb\.com|twitter|t\.co|tiktok/.test(ref)
    || /utm_source=(ig|fb|instagram|facebook)/i.test(location.search);
  var delay = isSocial ? 10000 : 30000;
  var scrollTrigger = isSocial ? 0.4 : 0.6;

  var shown = false;
  function showBar() {
    if (shown) return;
    shown = true;
    var bar = document.createElement('div');
    bar.id = 'retention-bar';
    bar.innerHTML = '<div class="ret-inner">'
      + '<span class="ret-icon">🔔</span>'
      + '<div class="ret-text">'
      + '<strong>' + (isSocial ? '¿Quieres más análisis así?' : '¿Te ha resultado útil?') + '</strong>'
      + '<span>' + (isSocial ? 'Activa las notificaciones y recibe dos informativos al día' : 'Activa las notificaciones para no perderte nada') + '</span>'
      + '</div>'
      + '<button class="ret-btn" id="ret-btn-yes">Activar</button>'
      + '<button class="ret-close" id="ret-btn-no" aria-label="Cerrar">✕</button>'
      + '</div>';
    document.body.appendChild(bar);
    setTimeout(function () { bar.classList.add('show'); }, 50);

    if (typeof gtag === 'function') {
      gtag('event', 'retention_bar_shown', { source: isSocial ? 'social' : 'organic', page_path: path });
    }

    function dismiss() {
      bar.classList.remove('show');
      sessionStorage.setItem(KEY, '1');
    }

    document.getElementById('ret-btn-no').addEventListener('click', dismiss);
    document.getElementById('ret-btn-yes').addEventListener('click', function () {
      dismiss();
      if (window.OneSignalDeferred) {
        window.OneSignalDeferred.push(function (O) { O.User.PushSubscription.optIn(); });
      }
      if (typeof gtag === 'function') {
        gtag('event', 'retention_bar_accept', { source: isSocial ? 'social' : 'organic', page_path: path });
      }
    });
  }

  setTimeout(showBar, delay);
  window.addEventListener('scroll', function () {
    if (shown) return;
    var pct = window.scrollY / Math.max(1, document.body.scrollHeight - window.innerHeight);
    if (pct > scrollTrigger) showBar();
  }, { passive: true });
})();

/* ── Service Worker (PWA) ────────────────────────────────────── */
if ('serviceWorker' in navigator) {
  window.addEventListener('load', function() {
    navigator.serviceWorker.register('/sw.js').catch(function() {});
  });
}

/* ── Tracking: sesiones desde la app instalada ───────────────── */
(function () {
  var isStandalone = navigator.standalone
    || window.matchMedia('(display-mode: standalone)').matches;
  if (!isStandalone) return;
  // GA4 puede tardar en cargar — esperamos al evento load
  window.addEventListener('load', function () {
    if (typeof gtag === 'function') {
      gtag('event', 'pwa_session', {
        display_mode: 'standalone',
        page_path: location.pathname
      });
    }
  });
})();

/* ── App Install Banner ──────────────────────────────────────── */
(function () {
  var KEY = 'hdd-aib-v2';

  // Ya instalada como app o ya descartada → salir
  if (navigator.standalone) return;
  if (window.matchMedia('(display-mode: standalone)').matches) return;
  if (sessionStorage.getItem(KEY)) return;

  var ua  = navigator.userAgent;
  var dpr = window.devicePixelRatio || 1;

  // Detección de plataforma y navegador
  var isIOS     = /iPad|iPhone|iPod/.test(ua) && !window.MSStream;
  var isAndroid = /Android/.test(ua);
  var isMobile  = isIOS || isAndroid || /Mobi/.test(ua);

  var isSamsungBrowser = /SamsungBrowser/.test(ua);
  var isEdge           = /Edg\//.test(ua);
  var isFirefox        = /Firefox/.test(ua) && !/Seamonkey/.test(ua);
  var isOpera          = /OPR\/|Opera/.test(ua);
  var isChrome         = /Chrome\//.test(ua) && !isEdge && !isOpera && !isSamsungBrowser;
  var isSafari         = /^((?!chrome|android).)*safari/i.test(ua) && !isChrome;
  var isIOSSafari      = isIOS && isSafari;
  var isIOSChrome      = isIOS && isChrome;
  var isIOSFirefox     = isIOS && isFirefox;

  var deferredPrompt = null;

  // Capturar evento instalación nativa (Chrome/Edge/Android)
  window.addEventListener('beforeinstallprompt', function (e) {
    e.preventDefault();
    deferredPrompt = e;
  });

  // Resolver qué instrucciones mostrar
  function getConfig() {
    // iOS Safari — única forma de instalar en iOS
    if (isIOSSafari) {
      return {
        browser: 'Safari',
        browserIcon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><path d="M12 2v4M12 18v4M2 12h4M18 12h4" stroke-width="1"/><path d="M16.24 7.76l-2.83 2.83M10.59 13.41l-2.83 2.83M16.24 16.24l-2.83-2.83M10.59 10.59L7.76 7.76"/></svg>',
        steps: [
          { n:1, html: 'Pulsa el botón <strong>Compartir</strong> <span class="tag">⎙</span> en la barra inferior de Safari' },
          { n:2, html: 'Desplázate y toca <span class="tag">Añadir a pantalla de inicio</span>' },
          { n:3, html: 'Pulsa <span class="tag">Añadir</span> — aparecerá el icono de HdD en tu pantalla' }
        ],
        btnText: 'Entendido',
        btnClass: '',
        canInstall: false
      };
    }

    // iOS Chrome/Firefox — solo pueden abrir en Safari
    if (isIOSChrome || isIOSFirefox) {
      var bName = isIOSChrome ? 'Chrome' : 'Firefox';
      return {
        browser: bName + ' (iOS)',
        browserIcon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="4"/></svg>',
        steps: [
          { n:1, html: 'Toca <span class="tag">⋯</span> o <span class="tag">↗ Abrir en Safari</span>' },
          { n:2, html: 'En Safari: pulsa <span class="tag">⎙ Compartir</span> → <span class="tag">Añadir a pantalla de inicio</span>' }
        ],
        btnText: 'Entendido',
        btnClass: '',
        canInstall: false
      };
    }

    // Android / Desktop con beforeinstallprompt disponible o probable
    if (isChrome) {
      return {
        browser: isMobile ? 'Chrome para Android' : 'Chrome',
        browserIcon: '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="4" fill="#EA4335"/><path d="M12 8a4 4 0 1 1 0 8 4 4 0 0 1 0-8z" fill="none" stroke="#EA4335" stroke-width="8"/></svg>',
        steps: isMobile ? [
          { n:1, html: 'Pulsa <strong>Instalar</strong> aquí abajo' },
          { n:2, html: 'Confirma en el diálogo de Chrome' },
          { n:3, html: 'El icono de HdD aparece en tu pantalla de inicio' }
        ] : [
          { n:1, html: 'Pulsa <strong>Instalar</strong> aquí abajo o el icono <span class="tag">⊕</span> en la barra de dirección' },
          { n:2, html: 'Confirma en el diálogo de Chrome' },
          { n:3, html: 'HdD se abre como una app sin barra del navegador' }
        ],
        btnText: 'Instalar app',
        btnClass: 'red',
        canInstall: true
      };
    }

    if (isEdge) {
      return {
        browser: 'Microsoft Edge',
        browserIcon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M3 12C3 7 7 3 12 3c6 0 9 4 9 8 0 3-2 5-5 5H8c-2 0-3-1-3-3 0-3 3-5 7-5 2 0 3 1 3 2"/></svg>',
        steps: [
          { n:1, html: 'Pulsa <strong>Instalar</strong> o el icono <span class="tag">⊕</span> en la barra de dirección' },
          { n:2, html: 'Selecciona <span class="tag">Instalar</span> en el diálogo' }
        ],
        btnText: 'Instalar app',
        btnClass: 'red',
        canInstall: true
      };
    }

    if (isSamsungBrowser) {
      return {
        browser: 'Samsung Internet',
        browserIcon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="5" y="2" width="14" height="20" rx="2"/><circle cx="12" cy="17" r="1"/></svg>',
        steps: [
          { n:1, html: 'Pulsa <span class="tag">⋮ Menú</span> (tres puntos)' },
          { n:2, html: 'Elige <span class="tag">Añadir página a</span> → <span class="tag">Pantalla de inicio</span>' }
        ],
        btnText: 'Entendido',
        btnClass: '',
        canInstall: false
      };
    }

    if (isFirefox) {
      if (isMobile) {
        return {
          browser: 'Firefox',
          browserIcon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="9"/><path d="M12 3C8 3 5 7 5 12"/></svg>',
          steps: [
            { n:1, html: 'Pulsa <span class="tag">⋮ Menú</span> → <span class="tag">Instalar</span>' },
            { n:2, html: 'Si no aparece, prueba abrir la web en Chrome para Android' }
          ],
          btnText: 'Entendido',
          btnClass: '',
          canInstall: false
        };
      }
      return null; // Firefox escritorio no soporta PWA install
    }

    // Safari escritorio (macOS Ventura+ sí soporta)
    if (isSafari && !isMobile) {
      return {
        browser: 'Safari',
        browserIcon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><path d="M12 6v12M6 12h12" stroke-width="1"/></svg>',
        steps: [
          { n:1, html: 'Pulsa <span class="tag">Archivo</span> en la barra de menú' },
          { n:2, html: 'Elige <span class="tag">Añadir al Dock</span>' }
        ],
        btnText: 'Entendido',
        btnClass: '',
        canInstall: false
      };
    }

    // Fallback genérico
    return {
      browser: 'tu navegador',
      browserIcon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><path d="M2 12h20M12 2a15 15 0 0 1 0 20M12 2a15 15 0 0 0 0 20"/></svg>',
      steps: [
        { n:1, html: 'Busca en el menú de tu navegador la opción <span class="tag">Instalar app</span> o <span class="tag">Añadir a pantalla de inicio</span>' }
      ],
      btnText: 'Entendido',
      btnClass: '',
      canInstall: false
    };
  }

  var cfg = getConfig();
  if (!cfg) return; // navegador incompatible

  function buildBanner() {
    var stepsHTML = cfg.steps.map(function (s) {
      return '<div class="aib-step">'
        + '<span class="aib-step-dot">' + s.n + '</span>'
        + '<span class="aib-step-text">' + s.html + '</span>'
        + '</div>';
    }).join('');

    var el = document.createElement('div');
    el.id = 'aib';
    el.setAttribute('role', 'dialog');
    el.setAttribute('aria-label', 'Instalar HdD como app');
    el.innerHTML = ''
      + '<div class="aib-backdrop" id="aib-backdrop"></div>'
      + '<div class="aib-card">'
      +   '<div class="aib-top">'
      +     '<div class="aib-appicon"><span class="hdd-letters">HdD</span></div>'
      +     '<div class="aib-info">'
      +       '<h3>Instala HdD como app</h3>'
      +       '<p>Sin App Store &middot; sin publicidad &middot; gratis</p>'
      +     '</div>'
      +     '<button class="aib-close" id="aib-close" aria-label="Cerrar">&times;</button>'
      +   '</div>'
      +   '<div class="aib-divider"></div>'
      +   '<div class="aib-browser-badge">' + cfg.browserIcon + 'Instrucciones para ' + cfg.browser + '</div>'
      +   '<div class="aib-steps-title">Cómo hacerlo en 30 segundos</div>'
      +   '<div class="aib-steps">' + stepsHTML + '</div>'
      +   '<button class="aib-btn ' + cfg.btnClass + '" id="aib-btn">' + cfg.btnText + '</button>'
      +   '<p class="aib-btn-note"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 22C6.48 22 2 17.52 2 12S6.48 2 12 2s10 4.48 10 10-4.48 10-10 10zm-1-7h2v2h-2v-2zm0-8h2v6h-2V7z"/></svg>La app es la misma web, sin barra del navegador</p>'
      + '</div>';

    document.body.appendChild(el);

    // Mostrar con pequeño delay
    setTimeout(function () { el.classList.add('show'); }, 1200);

    function dismiss() {
      el.classList.remove('show');
      sessionStorage.setItem(KEY, '1');
    }

    document.getElementById('aib-close').addEventListener('click', dismiss);
    document.getElementById('aib-backdrop').addEventListener('click', dismiss);

    var btn = document.getElementById('aib-btn');
    btn.addEventListener('click', function () {
      if (cfg.canInstall && deferredPrompt) {
        // Evento: usuario pulsa "Instalar" → se abre el diálogo nativo
        if (typeof gtag === 'function') gtag('event', 'pwa_install_prompt', { browser: cfg.browser });
        deferredPrompt.prompt();
        deferredPrompt.userChoice.then(function (r) {
          // Evento: resultado del diálogo (accepted / dismissed)
          if (typeof gtag === 'function') gtag('event', 'pwa_install_choice', { outcome: r.outcome, browser: cfg.browser });
          if (r.outcome === 'accepted') dismiss();
          deferredPrompt = null;
        });
      } else {
        dismiss();
      }
    });

    // Evento: instalación completada (Chrome/Edge lo disparan al terminar)
    window.addEventListener('appinstalled', function () {
      if (typeof gtag === 'function') gtag('event', 'pwa_installed', { browser: cfg.browser });
      dismiss();
    });

    // Cerrar con Escape
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && el.classList.contains('show')) dismiss();
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', buildBanner);
  } else {
    buildBanner();
  }
})();