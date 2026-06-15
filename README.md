# Bank XYZ — Customer Experience Intelligence Dashboard

Dashboard Streamlit untuk analisis kepuasan nasabah Bank XYZ.

## Struktur Folder

```
bankxyz_dashboard/
├── app.py                   ← Entry point utama (REVISED)
├── requirements.txt
├── utils/
│   ├── load_data.py
│   ├── filters.py
│   ├── theme.py
│   ├── kpi_bar.py
│   └── ...
├── static/
│   └── indonesia.geojson
└── data/
    ├── raw/
    │   └── Deka_project_dataset_BankXYZ.xlsx
    └── processed/
        ├── data_clean.pkl
        └── data_final.pkl
```

## Urutan Tab (Revised)

| # | Tab | Isi |
|---|-----|-----|
| 1 | **Scorecard** | 5 KPI cards (Total Responden, NPS, Kepuasan Overall, Service Failure, **CES**) → Peta Provinsi → Kepuasan per Dimensi (Fisik Bank‑Brand Image‑Teller‑CS‑ATM‑Sekuriti) + Distribusi NPS → Distribusi Kepuasan & Loyalitas → Prioritas Perhatian |
| 2 | **Customer Service Index** | 4 KPI cards (Total Responden, Atribut Prioritas, Dimensi Terkritis, Gap Terbesar) → IPA filter dimensi + kuadran counter → Chart IPA → Atribut Prioritas Utama |
| 3 | **Loyalitas Index** | Segmentasi Loyalitas (sama seperti sebelumnya) |
| 4 | **Profil Cabang** | Top/Bottom 5 → Radar DNA → Waktu Tunggu (sama seperti sebelumnya) |
| 5 | **Peta Emosi & Profil Nasabah** | Peta Emosi (XYZ vs Kompetitor, Korelasi NPS, Profil Emosi) → kemudian Profil Nasabah |
| 6 | **Intelijen Kompetitor** | Radar + Gap → Distribusi Bank → NPS Comparison |

## Setup Lokal

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy ke Streamlit Cloud

1. Push semua file ke GitHub repo (pastikan `data/` dan `static/` ikut di-push)
2. Buka [share.streamlit.io](https://share.streamlit.io)
3. New app → pilih repo → **Main file path: `app.py`**
4. Deploy!

> **Catatan Google Drive**: File `app.py` di-revisi agar tidak bergantung pada Google Drive mount.  
> Pastikan file `data_clean.pkl`, `data_final.pkl`, dan `Deka_project_dataset_BankXYZ.xlsx`  
> ada di folder `data/raw/` dan `data/processed/` sebelum deploy.

## Perubahan dari Versi Sebelumnya

- ✅ Urutan tab diubah: Scorecard → CSI → Loyalitas → Profil Cabang → Peta Emosi+Nasabah → Kompetitor
- ✅ **Customer Effort Score (CES)** ditambahkan ke KPI Scorecard (dihitung dari kolom T_J1 — kemudahan layanan cabang, skala 1–6)
- ✅ Service Failure ditambahkan sebagai KPI card di Scorecard
- ✅ Urutan dimensi diseragamkan: Fisik Bank → Brand Image → Teller → CS → ATM → Sekuriti
- ✅ Tab "Prioritas Layanan" diubah nama menjadi "Customer Service Index"
- ✅ Peta Emosi dan Profil Nasabah digabung dalam satu tab (Peta Emosi tampil lebih dulu)
- ✅ Nuansa visual, warna, dan komponen lainnya tidak berubah
