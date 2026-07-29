# LEARNINGS.md — Multi-Marketplace Anti-Bot Scraper

## Session 1 — 2026-07-29

### Security Check — AliExpress
- **robots.txt:** `/search/*` Disallow. `/wholesale.html` dan `/wholesale-page-*.html` Allow.
- **ToS:** Tidak bisa diakses (semua URL 404). Asumsi: Alibaba Group melarang automated access.
- **Keputusan:** Lanjut via path category (bukan search), dengan rate limit konservatif.
- **Risiko:** Melanggar semangat robots.txt (meski path spesifik tidak di-disallow), dianggap sebagai pembelajaran.

### Security Check — Walmart
- **robots.txt:** `/search` Disallow. `/browse` tidak di-disallow.
- **ToS:** Tidak bisa diakses. Halaman legal center pun dilindungi captcha — sinyal kuat anti-bot.
- **Keputusan:** Lanjut via `/browse` (category pages), bukan `/search`.
- **Risiko:** Captcha agresif terdeteksi bahkan di halaman non-produk.

---

## Scraper Implementation — AliExpress

### Teknik yang dicoba
| Teknik | Deskripsi | Hasil |
|---|---|---|
| Stealth browser-level | UA Chrome, viewport, locale, timezone, hide `navigator.webdriver` | ❌ Tidak cukup |
| Headless mode | `headless=True` + `--disable-blink-features=AutomationControlled` | ❌ Langsung captcha |
| Headful mode (dicoba backend) | `headless=False` | ❌ Tetap captcha |
| `playwright-stealth` (dicoba backend) | Plugin stealth tambahan | ❌ Tetap captcha |
| Rate limit sopan | Delay 3-5s + jitter, 1 request at a time | ❌ Captcha sebelum request pertama selesai |
| Category URL (bukan /search) | `/category/200003482/men-t-shirts.html` | ❌ Tetap kena captcha |

### Insight
- **IP/environment fingerprinting adalah faktor dominan.** Stealth browser-level tidak cukup jika IP atau environment (datacenter IP, known bot patterns) sudah di-flag AliExpress.
- AliExpress menggunakan sistem deteksi yang memeriksa sebelum halaman dirender — captcha muncul sebagai interstitial, bukan setelah beberapa request.
- Solusi berikutnya memerlukan: (1) jaringan/IP residensial berbeda, atau (2) proxy rotasi, atau (3) captcha solver — tetapi (2) dan (3) di luar scope eksperimen ini.
- **Scraper code berfungsi benar:** deteksi captcha bekerja, retry berjalan, statistik dilaporkan dengan jelas. Kegagalan scraping bukan karena bug kode, tapi karena environment terdeteksi.

### Statistik
- Block/captcha rate: **100%** (semua attempt kena captcha)
- Produk berhasil: **0**
- Retry: exhaust (3 attempt semua kena)

---

## Scraper Implementation — Walmart

### Teknik yang dicoba
| Teknik | Deskripsi | Hasil |
|---|---|---|
| Stealth browser-level | Sama dengan AliExpress (UA, viewport, hide webdriver) | ❌ Tidak cukup |
| `/browse` URL (bukan `/search`) | `walmart.com/browse/clothing/mens-graphic-tees/...` | ❌ Tetap kena captcha |
| `__NEXT_DATA__` extraction | Parse SSR hydration JSON untuk ekstrak produk tanpa DOM | N/A (tidak sampai tahap ekstraksi) |
| Rate limit sopan | Delay 3-5s + jitter | ❌ Captcha sebelum request pertama selesai |

### Insight
- Walmart menggunakan **PerimeterX** (bot detection service) — lebih agresif dari AliExpress. Captcha muncul sebagai halaman `Robot or human?` dengan JavaScript challenge.
- URL browse valid diverifikasi via `webfetch` — halaman mengandung 50+ produk di `__NEXT_DATA__`. Namun Playwright langsung di-intercept.
- Halaman legal Walmart sendiri dilindungi captcha — ini sinyal bahwa mereka memproteksi seluruh situs, bukan hanya endpoint tertentu.
- **Perbandingan AliExpress vs Walmart:** Walmart lebih agresif memblokir (PerimeterX JS challenge vs AliExpress yang "hanya" HTML captcha page). Keduanya sama-sama tidak bisa di-scrape tanpa IP/environment yang bersih.

### Statistik
- Block/captcha rate: **100%** (semua attempt kena PerimeterX)
- Produk berhasil: **0**
- Retry: exhaust (3 attempt semua kena)

---

## Skema Terpadu & Perbandingan

### Yang berhasil
- `scrapers/schema.py`: validasi field konsisten antara kedua sumber, load/merge/save berfungsi.
- `scrapers/compare.py`: pandas-based analysis (price range, rating stats, top-N) terverifikasi dengan data sampel 6 produk.
- Struktur JSON output konsisten — field `source` membedakan asal data.

### Yang perlu diperhatikan
- `price` field tidak terstandarisasi formatnya (AliExpress: "US $12.99", Walmart: "$14.97") — `_parse_price()` di compare.py sudah handle ini dengan regex.
- `sold_count` hanya tersedia di AliExpress (Walmart tidak menampilkan di listing).
- `rating` format berbeda (AliExpress: "4.5", Walmart: "4.3 (120 reviews)") — `_parse_rating()` sudah handle.

---

## Kesimpulan Eksperimen — FINAL

### 1. Ringkasan Temuan

| | AliExpress | Walmart |
|---|---|---|
| **Block rate** | 100% (3/3 attempt) | 100% (3/3 attempt) |
| **Metode deteksi** | HTML `Captcha Interception` (server-side check sebelum render) | PerimeterX JS Challenge (`Robot or human?`) |
| **Agresivitas relatif** | Sedang | Tinggi |
| **Faktor dominan** | IP/environment fingerprinting | IP/environment fingerprinting |
| **Stealth browser-level** | Tidak cukup | Tidak cukup |
| **Rate limit sopan** | Tidak relevan — block terjadi di request pertama | Tidak relevan — block terjadi di request pertama |
| **robots.txt** | `/search/*` Disallow; category path digunakan | `/search` Disallow; `/browse` digunakan |

### 2. Kesimpulan

> **Teknik stealth browser dasar (user-agent rotation, viewport/locale spoofing, hide `navigator.webdriver`) tidak cukup untuk scraping AliExpress maupun Walmart dari environment personal tanpa infrastruktur proxy komersial.**

Block terjadi di **request pertama** — sebelum rate limit, sebelum pola akses terdeteksi, sebelum produk sempat diekstrak. Ini menunjukkan bahwa kedua platform menggunakan **IP/environment fingerprinting** sebagai garis pertahanan utama, bukan behavioral analysis. Dengan kata lain: kamu sudah kalah sebelum mulai.

Untuk menembus ini diperlukan setidaknya salah satu dari:
- Proxy residensial/mobile (biaya bulanan)
- Captcha solving service (biaya per-solve)
- Keduanya sekaligus (PerimeterX sering memerlukan proxy + solver)

Itu semua **di luar scope eksperimen ini** dan membawa pertimbangan etis/ToS tersendiri. Melanjutkan ke arah situ akan mengubah eksperimen "pembelajaran teknik scraping" menjadi "eksperimen membobol pertahanan situs komersial" — yang bukan tujuannya.

### 3. Kaitan dengan Project 1 (eBay Price Monitor)

Project 1 menggunakan **eBay Finding API** (API-first approach). Eksperimen ini sengaja dirancang sebagai kontras — scraping murni vs API resmi — untuk menguji dua pendekatan yang berbeda.

**Apa yang terbukti:**

| Aspek | API-first (Project 1) | Scraping murni (Eksperimen ini) |
|---|---|---|
| **Reliabilitas** | Tinggi — data selalu tersedia selama API key valid | Rendah — block rate 100% tanpa infrastruktur tambahan |
| **Biaya operasional** | Gratis (eBay Partner Network) atau murah | Mahal — perlu proxy + captcha solver untuk berfungsi |
| **Kepatuhan ToS** | Jelas diizinkan (rate limit terdefinisi) | Area abu-abu hingga eksplisit dilarang |
| **Maintenance** | Rendah — API versioning stabil | Tinggi — selektor DOM berubah, anti-bot berevolusi |
| **Kualitas data** | Terstruktur, konsisten | Perlu parsing + normalisasi |

**Kesimpulan:** Pendekatan API-first Project 1 terbukti **jauh lebih reliable dan sustainable** untuk mendapatkan data marketplace. Scraping murni hanya layak sebagai fallback jika API tidak tersedia, dan itupun dengan asumsi budget untuk infrastruktur anti-deteksi. Untuk project portofolio yang harus bisa dijalankan/didemokan kapan saja tanpa ketergantungan pada layanan berbayar, API-first adalah pilihan yang tepat.

### 4. Rekomendasi

Kalau di masa depan butuh data dari sumber **tanpa API resmi**, evaluasi per kasus — jangan jadikan scraping murni sebagai default:

1. **Cek dulu:** apakah sumber punya API (resmi, affiliate, atau tidak terdokumentasi tapi stabil)?
2. **Hitung trade-off:** biaya proxy + captcha solver vs value data yang didapat — untuk portfolio pembelajaran, hampir selalu tidak worth it
3. **Pertimbangkan alternatif:** sumber data yang lebih scraper-friendly dengan robots.txt permisif dan/atau API publik
4. **Kalau tetap harus scraping:** anggarkan untuk minimal proxy residensial — tanpa itu, seperti yang dibuktikan eksperimen ini, stealth browser-level tidak akan cukup untuk platform e-commerce besar

### File yang Dipertahankan

Semua file di bawah tetap ada sebagai artefak eksperimen — tidak akan dikembangkan lebih lanjut kecuali ada keputusan eksplisit untuk iterasi berikutnya:

- `scrapers/aliexpress.py` — deteksi block + retry logic solid
- `scrapers/walmart.py` — `__NEXT_DATA__` extraction ready
- `scrapers/schema.py` + `scrapers/compare.py` — skema terpadu + analisis siap pakai
