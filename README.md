# Anti-Bot Scraping Experiment

Eksperimen pembelajaran: menguji kemampuan scraping murni (tanpa API) terhadap dua marketplace besar — **AliExpress** dan **Walmart** — untuk kategori "graphic t-shirt".

## Hasil

| | AliExpress | Walmart |
|---|---|---|
| Block rate | 100% | 100% |
| Metode deteksi | HTML Captcha Interception | PerimeterX JS Challenge |
| Stealth browser-level | ❌ Tidak cukup | ❌ Tidak cukup |

**Kesimpulan:** User-agent rotation, viewport spoofing, dan hide `navigator.webdriver` tidak cukup untuk platform e-commerce besar. IP/environment fingerprinting adalah garis pertahanan utama — block terjadi di request pertama.

## Struktur

```
scrapers/
├── aliexpress.py   # Playwright + detect block + retry
├── walmart.py      # Playwright + __NEXT_DATA__ extraction
├── schema.py       # Skema data terpadu
└── compare.py      # Analisis lintas sumber (pandas)
```

## Kenapa Tidak Dilanjutkan

Proxy residensial + captcha solver diperlukan untuk menembus pertahanan ini — keduanya di luar scope eksperimen dan membawa pertimbangan etis/ToS. Insight yang didapat suda cukup: **API-first approach (seperti eBay Finding API di Project 1) jauh lebih reliable dan sustainable.**

Baca `LEARNINGS.md` untuk dokumentasi lengkap.
