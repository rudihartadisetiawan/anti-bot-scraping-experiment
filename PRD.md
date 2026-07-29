# PRD.md — Multi-Marketplace Anti-Bot Scraper (Eksperimen Level Sulit)

## 1. Latar Belakang & Tujuan

Ini **eksperimen pembelajaran**, bukan project portofolio final yang langsung di-deploy — tujuannya menguji dan membangun kemampuan teknis untuk Level Sulit di roadmap portofolio, secara terpisah dari tekanan "harus siap ditunjukkan ke klien". Kalau hasilnya solid, baru dipertimbangkan jadi portofolio ketiga yang dipoles.

**Dua kemampuan yang diuji sekaligus:**
1. **Anti-bot scraping** — scraping situs yang punya proteksi bot dasar-menengah (bukan proxy/stealth browser, bukan yang sekelas Amazon), tanpa API resmi
2. **Multi-source aggregation** — menggabungkan data produk sejenis dari lebih dari satu sumber ke satu skema terpadu, supaya bisa dibandingkan lintas platform

**Perbedaan sengaja dari Project 1 (eBay Price Monitor):** project itu API-first dan single-source. Eksperimen ini justru sengaja mengambil pendekatan scraping murni dan multi-source, buat melengkapi skill yang belum tersentuh di project sebelumnya.

## 2. Target Sumber Data

Dua marketplace dengan proteksi anti-bot level menengah (bukan yang paling ekstrem, supaya realistis untuk dipelajari dalam waktu wajar):

- **AliExpress** — rendering JS, ada deteksi bot dasar, ToS relatif longgar untuk scraping ringan dengan rate limit sopan
- **Walmart** — punya proteksi bot menengah, struktur data produk konsisten, baik untuk uji coba teknik anti-deteksi

**Kategori produk contoh:** pilih satu kategori spesifik yang tersedia di kedua platform (misal "wireless earbuds" atau kategori lain yang konsisten) — supaya perbandingan lintas sumber bermakna, bukan asal comot kategori beda-beda.

**Kepatuhan:** cek `robots.txt` dan ringkasan ToS masing-masing sumber sebelum implementasi. Kalau salah satu sumber ternyata secara eksplisit melarang scraping di ToS-nya, ganti ke alternatif yang lebih longgar (bukan dipaksakan).

## 3. Fitur Inti (Scope Eksperimen)

1. **Scraper per sumber** (2 modul terpisah, `scrapers/aliexpress.py` dan `scrapers/walmart.py`):
   - Rendering JS via Playwright
   - User-agent rotation dasar + header yang realistis
   - Delay/jitter antar request (bukan fixed interval, biar tidak pola-terdeteksi)
   - Retry dengan backoff kalau kena block/captcha — **bukan bypass captcha**, cukup deteksi dan skip dengan graceful degradation
2. **Skema data terpadu** — satu tabel `produk` dengan kolom `source` (aliexpress/walmart) yang bisa diisi dari kedua scraper, supaya produk sejenis dari sumber berbeda bisa dibandingkan
3. **Perbandingan lintas sumber** — fungsi analisis sederhana: produk sejenis (berdasarkan keyword pencarian yang sama), bandingkan rentang harga antar platform
4. **Logging deteksi block** — kalau scraper kena block/captcha, catat itu ke log (bukan cuma silent fail) — ini bagian penting dari pembelajaran, supaya kelihatan seberapa sering dan di kondisi apa proteksi anti-bot itu terpicu

## 4. Yang TIDAK Masuk Scope (Sengaja Dibatasi)

- **Proxy rotation berbayar/komersial** (Bright Data, dll) — di eksperimen awal ini, coba dulu tanpa itu, supaya kelihatan batas kemampuan teknik dasar sebelum lompat ke tools berbayar
- **Bypass captcha aktif** (solving service, dll) — kalau kena captcha, sistem cukup mendeteksi dan skip, bukan mencoba menembusnya
- Dashboard web atau deployment publik — ini eksperimen lokal dulu
- Scheduling otomatis (GitHub Actions) — jalankan manual selama fase eksperimen
- ML forecasting — itu eksperimen terpisah, jangan digabung supaya scope tetap fokus

## 5. Kriteria Keberhasilan Eksperimen

Ini bukan "Definition of Done" yang kaku kayak project production — lebih ke pertanyaan yang perlu terjawab setelah eksperimen:

- [ ] Apakah scraper berhasil mengambil data dari AliExpress tanpa kena block dalam kondisi wajar (rate rendah, delay sopan)?
- [ ] Apakah scraper berhasil mengambil data dari Walmart dengan kondisi yang sama?
- [ ] Seberapa sering masing-masing sumber mendeteksi/memblokir upaya scraping? (ini data pembelajaran, bukan kegagalan)
- [ ] Apakah skema data terpadu berhasil menyatukan produk dari 2 sumber untuk dibandingkan?
- [ ] Insight apa yang didapat soal teknik mana yang efektif vs tidak untuk masing-masing target?

## 6. Tech Stack

| Layer | Tools |
|---|---|
| Scraping & rendering | Playwright (Python), dengan stealth plugin dasar (`playwright-stealth` atau setara) |
| Storage | MySQL lokal (Laragon) — cukup untuk eksperimen, tidak perlu hosted dulu |
| Analisis perbandingan | pandas |
| Version control | Git (lokal dulu, push ke GitHub kalau hasilnya layak jadi portofolio) |

## 7. Output Eksperimen

Bukan portofolio siap pakai, tapi:
- Kode scraper untuk 2 sumber, dengan catatan teknik yang dipakai
- Log/catatan hasil percobaan: tingkat keberhasilan, pola block yang ditemui, teknik yang efektif
- `LEARNINGS.md` — ringkasan pembelajaran (apa yang berhasil, apa yang tidak, kenapa) — ini yang nanti jadi dasar keputusan apakah lanjut dipoles jadi portofolio ketiga, dan pendekatan apa yang dipakai kalau iya
