# PROGRESS.md — Multi-Marketplace Anti-Bot Scraper

## Status Keseluruhan
- [x] Tahap 1: Security check (AliExpress + Walmart) — SELESAI
- [x] Tahap 2: Struktur folder + LEARNINGS.md — SELESAI
- [x] Tahap 3: Scraper AliExpress — SELESAI (kode siap; runtime terkena captcha, deteksi & log bekerja)
- [x] Tahap 4: Scraper Walmart — SELESAI (kode siap; PerimeterX captcha, deteksi & log bekerja)
- [x] Tahap 5: Skema data terpadu + perbandingan — SELESAI (infrastruktur siap, terverifikasi dengan data sampel)

## Detail per Tahap

### Tahap 1 — Security Check (2026-07-29)
- AliExpress: `/search/*` Disallow, wholesale pages Allow. Lanjut via category/wholesale.
- Walmart: `/search` Disallow, `/browse` tidak di-disallow. Lanjut via browse.
- Kedua ToS tidak bisa diakses. Risiko dicatat di LEARNINGS.md.

### Tahap 2 — Struktur Folder (2026-07-29)
- `scrapers/` — modul scraper per sumber
- `data/` — output hasil scraping (JSON/CSV)
- `LEARNINGS.md` — log pembelajaran
- `PROGRESS.md` — file ini

### Tahap 3 — Scraper AliExpress (2026-07-29)
- File `scrapers/aliexpress.py` dibuat (329 lines).
- Playwright async, stealth dasar (UA, viewport, locale, timezone, hide webdriver), delay 3-5s jitter.
- Deteksi block/captcha eksplisit: title, URL, status code, shadow block.
- Retry maks 2 dengan exponential backoff 5s/10s.
- **Hasil runtime:** Captcha Interception di semua attempt. Scraper mendeteksi dengan benar dan graceful exit.

### Tahap 4 — Scraper Walmart (2026-07-29)
- File `scrapers/walmart.py` dibuat (373 lines).
- URL: `/browse/clothing/mens-graphic-tees/...` (bukan `/search`).
- Ekstraksi prioritas: `__NEXT_DATA__` (SSR hydration) → DOM fallback.
- **Hasil runtime:** PerimeterX (`Robot or human?`) di semua attempt. Scraper deteksi dan log dengan benar.

### Tahap 5 — Skema Terpadu & Perbandingan (2026-07-29)
- `scrapers/schema.py`: ProductFields, validate_product(), load/merge/save.
- `scrapers/compare.py`: merge + pandas analysis (price range, rating stats, top N).
- `scrapers/__init__.py`: package marker.
- Dependency: pandas terinstall di `.venv`.
- **Verifikasi:** logic perbandingan diuji dengan data sampel 6 produk (3 AliExpress + 3 Walmart) — price distribution, rating stats, top-N berfungsi.
- **Cara run:** `$env:PYTHONPATH = "."; .venv\Scripts\python scrapers/compare.py`

---

## EKSPERIMEN CLOSED — 2026-07-29

**Hasil:** Kedua scraper berhasil dibangun dengan deteksi block/captcha yang solid. Skema data terpadu dan fungsi perbandingan lintas sumber berfungsi (terverifikasi dengan data sampel). Namun, **tidak ada data aktual yang berhasil di-scrape** karena kedua sumber (AliExpress dan Walmart) memblokir 100% request dari environment ini sebelum produk sempat diekstrak.

**Kesimpulan:** Teknik stealth browser dasar (user-agent, viewport, hide webdriver) tidak cukup — IP/environment fingerprinting adalah garis pertahanan utama. Melanjutkan dengan proxy berbayar atau captcha solver berada di luar scope dan membawa pertimbangan etis/ToS yang tidak bisa diabaikan.

**Keputusan:** Eksperimen ditutup di titik ini dengan dokumentasi lengkap. Tidak dilanjutkan ke proxy/captcha solving. Semua file dipertahankan sebagai artefak pembelajaran.

**Baca LEARNINGS.md untuk:** ringkasan temuan, perbandingan dengan pendekatan API-first (Project 1), dan rekomendasi untuk pendekatan data sourcing di masa depan.
