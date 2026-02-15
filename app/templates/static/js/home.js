/*
  home.js
  - 3D carousel for "Let's Get to Know Detectify"
  - Simple subscribe form validation (client-side only)
*/
(() => {
  "use strict";

  // -------------------------
  // 3D Carousel
  // -------------------------
  const carousel = document.querySelector('[data-carousel="know"]');

  (function () {
  function setupCarousel3D(root) {
    const stage = root.querySelector(".carousel3d__stage");
    const cards = Array.from(root.querySelectorAll(".carousel3d__card[data-slide]"));
    const prevBtn = root.querySelector(".carousel3d__nav--prev");
    const nextBtn = root.querySelector(".carousel3d__nav--next");
    const n = cards.length;

    if (!stage || cards.length === 0) return;

    let active = 0;

    function mod(a, b) {
      return ((a % b) + b) % b;
    }

    function render() {
      cards.forEach((card, i) => {
        const rel = mod(i - active, n); 
        // Mapping agar tampil: kiri (-1), center (0), kanan (1), atas (2)
        // rel: 0 -> 0
        // rel: 1 -> 1 (kanan)
        // rel: 2 -> 2 (atas)
        // rel: n-1 -> -1 (kiri)
        let pos = 99;

        if (rel === 0) pos = 0;
        else if (rel === 1) pos = 1;
        else if (rel === 2) pos = 2;
        else if (rel === n - 1) pos = -1;

        card.dataset.pos = String(pos);
        card.setAttribute("aria-hidden", pos === 99 ? "true" : "false");
      });
    }

    function next() {
      active = mod(active + 1, n);
      render();
    }

    function prev() {
      active = mod(active - 1, n);
      render();
    }

    // Button handlers
    prevBtn?.addEventListener("click", prev);
    nextBtn?.addEventListener("click", next);

    // Klik card kiri/kanan untuk pindah
    cards.forEach((card, i) => {
      card.addEventListener("click", () => {
        const pos = card.dataset.pos;
        if (pos === "-1") prev();
        else if (pos === "1") next();
        else if (pos === "0") {
          // optional: bisa open detail / scroll ke app, dll
        } else {
          // kalau user klik card tersembunyi, set active langsung
          active = i;
          render();
        }
      });
    });

    // Keyboard navigation (saat fokus di dalam carousel/section)
    root.setAttribute("tabindex", "0");
    root.addEventListener("keydown", (e) => {
      if (e.key === "ArrowLeft") prev();
      if (e.key === "ArrowRight") next();
    });

    render();
  }

  document.querySelectorAll('.carousel3d[data-carousel="know"]').forEach(setupCarousel3D);
})();


  // -------------------------
  // Subscribe validation
  // -------------------------
  document.getElementById("subscribeForm")?.addEventListener("submit", (e) => {
  e.preventDefault();
  const input = document.getElementById("subscribeEmail");
  const hint = document.getElementById("subscribeHint");
  const email = (input?.value || "").trim();

  const ok = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);

  if (!hint) return;

  if (!ok) {
    hint.textContent = "Please enter a valid email address.";
    return;
  }

  hint.textContent = "Thanks! You’ve been subscribed.";
  input.value = "";
});
})();
