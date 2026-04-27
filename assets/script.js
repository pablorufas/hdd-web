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
    slides.forEach(function (_, i) {
      var dot = document.createElement("button");
      dot.className = "slide-dot" + (i === 0 ? " is-active" : "");
      dot.setAttribute("aria-label", "Ir a diapositiva " + (i + 1));
      dot.setAttribute("role", "tab");
      dot.setAttribute("aria-selected", i === 0 ? "true" : "false");
      dot.addEventListener("click", function () { goTo(i); });
      dotsWrap.appendChild(dot);
    });

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

      /* Actualizar UI */
      if (progressFill) progressFill.style.width = ((current + 1) / total * 100) + "%";
      if (counter)      counter.textContent = (current + 1) + "/" + total;

      dotsWrap.querySelectorAll(".slide-dot").forEach(function (d, i) {
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

/* ── Service Worker (PWA) ────────────────────────────────────── */
if ('serviceWorker' in navigator) {
  window.addEventListener('load', function() {
    navigator.serviceWorker.register('/sw.js').catch(function() {});
  });
}
