/*
  home.js
  - 3D Carousel untuk "Let's Get to Know Detectify"
  - Validasi formulir Subscribe (Client-side)
*/

document.addEventListener("DOMContentLoaded", () => {
  "use strict";

  // =========================================
  // 1. 3D CAROUSEL LOGIC
  // =========================================
  const carouselRoot = document.querySelector('[data-carousel="know"]');

  if (carouselRoot) {
    const stage = carouselRoot.querySelector(".carousel3d__stage");
    // Mengambil semua card yang ada di dalam stage
    const cards = Array.from(stage.querySelectorAll(".carousel3d__card"));
    const prevBtn = carouselRoot.querySelector(".carousel3d__nav--prev");
    const nextBtn = carouselRoot.querySelector(".carousel3d__nav--next");
    const total = cards.length;
    
    let activeIndex = 0;

    // Fungsi Modulo yang aman untuk angka negatif
    const mod = (n, m) => ((n % m) + m) % m;

    const render = () => {
      cards.forEach((card, i) => {
        // Hitung jarak relatif terhadap activeIndex
        let rel = mod(i - activeIndex, total);
        
        // Sesuaikan logika posisi agar:
        // 0 -> Center
        // 1 -> Kanan
        // total-1 -> Kiri
        // Sisanya -> Belakang/Tersembunyi
        
        let pos = 2; // Default: belakang (hidden)
        if (rel === 0) pos = 0;
        else if (rel === 1) pos = 1;
        else if (rel === total - 1) pos = -1;

        card.dataset.pos = pos;
        
        // Set z-index agar yang tengah paling depan
        if (pos === 0) card.style.zIndex = 10;
        else if (pos === 1 || pos === -1) card.style.zIndex = 5;
        else card.style.zIndex = 0;
      });
    };

    const next = () => {
      activeIndex = mod(activeIndex + 1, total);
      render();
    };

    const prev = () => {
      activeIndex = mod(activeIndex - 1, total);
      render();
    };

    // Event Listeners Navigasi
    if (nextBtn) nextBtn.addEventListener("click", next);
    if (prevBtn) prevBtn.addEventListener("click", prev);

    // Klik pada card untuk navigasi
    cards.forEach((card, i) => {
      card.addEventListener("click", () => {
        const currentPos = parseInt(card.dataset.pos);
        if (currentPos === 1) next();
        else if (currentPos === -1) prev();
      });
    });

    // Keyboard Navigation (Opsional)
    carouselRoot.addEventListener("keydown", (e) => {
      if (e.key === "ArrowLeft") prev();
      if (e.key === "ArrowRight") next();
    });

    // Inisialisasi awal
    render();
  }

  // =========================================
  // 2. SUBSCRIBE FORM LOGIC
  // =========================================
  const subscribeForm = document.getElementById("subscribeForm");
  
  if (subscribeForm) {
    subscribeForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      
      const inputEmail = document.getElementById("subscribeEmail");
      const hint = document.getElementById("subscribeHint");
      const emailValue = inputEmail.value.trim();

      // Reset state
      if (hint) {
        hint.style.color = "var(--text-muted)";
        hint.textContent = "";
      }

      // Validasi Email Sederhana
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(emailValue)) {
        if (hint) {
          hint.style.color = "red";
          hint.textContent = "Please enter a valid email address.";
        }
        return;
      }

      // --- LOGIKA KIRIM KE BACKEND (OPSIONAL) ---
      // Jika nanti sudah ada endpoint backend, uncomment bagian ini:
      /*
      try {
        const response = await fetch('/api/subscribe', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email: emailValue })
        });
        if (!response.ok) throw new Error('Failed');
      } catch (err) {
        // Handle error
      }
      */
      
      // Simulasi Sukses
      if (hint) {
        hint.style.color = "green";
        hint.textContent = "Thank you for subscribing!";
      }
      inputEmail.value = ""; // Clear input
    });
  }
});