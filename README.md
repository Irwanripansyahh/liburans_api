# Hari Libur API

API sederhana untuk mengambil data hari libur nasional & cuti bersama dari kalenderku.id (contoh: https://kalenderku.id/2026).

## Dokumentasi API

Project ini punya 2 cara akses data:

1) **FastAPI (lokal / server sendiri)**
- Cocok untuk development / deploy ke server yang bisa menjalankan Python.

2) **GitHub Pages (static JSON)**
- Cocok untuk akses via `github.io` tanpa server.

### Format data

Response JSON per tahun berbentuk:

```json
{
	"year": 2026,
	"source": "https://kalenderku.id/2026",
	"scraped_at": "2026-04-22T03:37:56.841805+00:00",
	"holidays": [
		{
			"date": "2026-01-16",
			"name": "Isra Mikraj Nabi Muhammad SAW",
			"type": "Libur Nasional",
			"holiday_type": "libur"
		}
	]
}
```

Keterangan field item di `holidays`:
- `date` (ISO `YYYY-MM-DD`)
- `name`
- `type` (nilai asli dari sumber, mis. `Libur Nasional` / `Cuti Bersama`)
- `holiday_type` normalisasi: `libur` atau `cuti`

### Endpoint (FastAPI)

- `GET /healthz`
- `GET /holidays/{year}`
- `GET /holidays?year={year}`

Contoh:
- `GET http://127.0.0.1:8000/holidays/2026`

### Endpoint (GitHub Pages)

- `GET /` → dokumentasi
- `GET /api/{year}` → JSON
- `GET /api/{year}.json` → JSON
- `GET /api/index.json` → daftar tahun tersedia

Contoh (User/Org Pages):
- `https://<username>.github.io/api/2026`

Contoh (Project Pages):
- `https://<username>.github.io/<repo>/api/2026`

## Menjalankan lokal

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# generate data tahun 2026
python scripts/scrape_kalenderku.py --year 2026 --out data/holidays/2026.json

# atau: generate 5 tahun terakhir (mis. 2022-2026)
python scripts/scrape_kalenderku.py --out-dir data/holidays --years-back 5 --end-year 2026

# jalankan API
python -m uvicorn app.main:app --reload --port 8000
```

Coba:
- `GET http://127.0.0.1:8000/healthz`
- `GET http://127.0.0.1:8000/holidays/2026`

## GitHub Actions

Workflow akan menjalankan scraper terjadwal dan meng-commit update JSON bila ada perubahan.

Default workflow meng-update **2 tahun terakhir** (berdasarkan tahun saat workflow dijalankan).

### Cara menjalankan

1. Pastikan project ini sudah ada di repository GitHub (karena GitHub Actions jalan di repo).
2. Buka repository di GitHub → tab **Actions**.
3. Pilih workflow **Update holidays data**.
4. Klik tombol **Run workflow** → klik **Run workflow** lagi.
5. Tunggu selesai. Jika ada perubahan data, workflow akan membuat commit dan push update ke branch yang sama.

### Jadwal (schedule)

Workflow juga dijalankan otomatis **1x sebulan** (lihat file workflow). Perlu diingat, GitHub kadang menonaktifkan schedule jika repo lama tidak ada aktivitas.

### Jika gagal push

- Workflow butuh izin untuk menulis ke repo (`contents: write`).
- Jika branch kamu memakai branch protection (wajib PR, wajib review, dll), langkah commit/push dari workflow bisa gagal.
- Cek log error di tab **Actions** untuk detailnya.

## GitHub Pages (github.io)

GitHub Pages tidak bisa menjalankan FastAPI (tidak ada server), tapi kamu bisa publish JSON statis sehingga bisa diakses seperti “API”.

Workflow akan men-generate file di folder `docs/`:
- `docs/index.html` → halaman dokumentasi (path `/`)
- `docs/api/2026` → endpoint JSON (path `/api/2026`)
- `docs/api/2026.json` → endpoint JSON (path `/api/2026.json`)
- `docs/api/index.json` → daftar tahun tersedia

### Cara aktifkan

1. Buka repo di GitHub → **Settings** → **Pages**.
2. Source: pilih branch (biasanya `main`) dan folder **`/docs`**.
3. Simpan. Tunggu sampai Pages aktif.

URL-nya tergantung jenis Pages:
- Jika repo bernama `<username>.github.io` (User/Org Pages): `https://<username>.github.io/api/2026`
- Jika repo biasa (Project Pages): `https://<username>.github.io/<repo>/api/2026`
