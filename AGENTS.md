# AGENTS.md — Multi-Marketplace Anti-Bot Scraper (Eksperimen)

Dibaca oleh semua subagent di awal tiap sesi. Ini project **eksperimen**, bukan production — prioritaskan pembelajaran dan iterasi cepat di atas kesempurnaan kode.

## Arsitektur Agent

- **Manager** — orkestrasi task, breakdown kerja, review hasil eksperimen (bukan cuma review kode, tapi juga insight yang didapat)
- **Backend** — implementasi scraper (Playwright), skema data, analisis perbandingan
- **Security** — evaluasi risiko teknik anti-deteksi yang dipakai, pastikan tidak melanggar batas etis (rate limit sopan, tidak agresif), cek robots.txt/ToS sebelum implementasi tiap sumber

**Catatan:** agent `frontend` tidak dipakai di project ini — sesuai scope, tidak ada dashboard di fase eksperimen.

## Pemilihan Model per Jenis Tugas

| Jenis tugas | Contoh konkret | Model |
|---|---|---|
| Boilerplate & tugas rutin | Setup struktur folder, parsing HTML dasar | `opencode-go/deepseek-v4-flash` |
| Implementasi scraper & anti-deteksi | Playwright automation, stealth technique, retry/backoff logic | `opencode-go/kimi-k2.7-code` |
| Keputusan arsitektur & evaluasi risiko | Desain skema data terpadu, evaluasi teknik mana yang dicoba, keputusan lanjut/stop | `opencode-go/deepseek-v4-pro` (manager) |
| Review etika/legal scraping | Cek robots.txt, ToS, batas rate yang wajar | `opencode-go/qwen3.7-max` (security) |

## Aturan Umum (Semua Agent)

1. **Ikuti PRD.md sebagai sumber kebenaran scope.** Ini eksperimen — kalau ada dorongan menambah fitur di luar scope (dashboard, ML, proxy berbayar), catat sebagai ide masa depan di `LEARNINGS.md`, jangan langsung diimplementasi.
2. **Kegagalan itu data, bukan cuma bug.** Kalau scraper kena block, jangan cuma di-retry membabi buta — catat kondisinya (rate berapa, pola apa) sebagai pembelajaran.
3. **Update PROGRESS.md di akhir sesi**, sertakan insight, bukan cuma status selesai/belum.
4. **Session handoff:** baca PROGRESS.md dan LEARNINGS.md (kalau sudah ada) di awal sesi.

## Aturan Khusus Backend

- **Rate limit sopan wajib** — delay antar request harus ada jitter (bukan interval tetap), minimal 2-5 detik antar request per sumber. Jangan agresif meski secara teknis bisa lebih cepat.
- Deteksi block/captcha harus eksplisit di-log dengan konteks (bukan exception generik) — ini data penting buat `LEARNINGS.md`.
- Skema data (`produk` dengan kolom `source`) harus konsisten antara AliExpress dan Walmart, supaya perbandingan lintas sumber valid.
- Kalau satu sumber ternyata terus-menerus gagal meski sudah dicoba teknik wajar, laporkan ke manager untuk keputusan lanjut/ganti sumber — jangan dipaksakan berjam-jam.

## Aturan Khusus Security

- **Cek robots.txt dan ringkasan ToS tiap sumber SEBELUM implementasi scraper dimulai**, bukan setelah.
- Kalau ada indikasi kuat bahwa scraping situs tertentu melanggar ToS secara eksplisit, laporkan ke manager — pertimbangkan ganti sumber, jangan lanjutkan.
- Evaluasi teknik anti-deteksi yang dipakai (user-agent rotation, delay, dll) — pastikan semuanya masuk kategori "menyamar sebagai browser wajar", bukan teknik yang secara aktif merusak/membebani server target (jangan sampai masuk kategori serangan).
- Tidak ada credential/API key yang relevan di project ini (tidak pakai proxy berbayar), tapi tetap cek tidak ada data sensitif ter-hardcode kalau nanti ditambah proxy service di iterasi berikutnya.

## Batas Scope

Jangan implementasi tanpa diminta: proxy rotation berbayar, captcha solving, dashboard, scheduling otomatis, ML forecasting. Semua ini di luar scope eksperimen ini — dorongan ke arah situ dicatat sebagai next step di `LEARNINGS.md`, bukan langsung dikerjakan.
