import os
import pickle
import pandas as pd
import numpy as np
import streamlit as st

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _get_data_path(*parts):
    return os.path.join(BASE, "data", *parts)


# ── MAIN DATA ────────────────────────────────────────────────
@st.cache_data
def load_main_data() -> pd.DataFrame:
    path = _get_data_path("processed", "data_final.pkl")
    if os.path.exists(path):
        with open(path, "rb") as f:
            df = pickle.load(f)
    else:
        path_csv = _get_data_path("processed", "data_clean.csv")
        if os.path.exists(path_csv):
            df = pd.read_csv(path_csv)
        else:
            # fallback: raw csv uploaded directly
            path_raw = _get_data_path("raw", "data_clean.csv")
            df = pd.read_csv(path_raw)

    # ── Derived columns (jika belum ada) ──────────────────────
    if "NPS_category" not in df.columns and "G1A" in df.columns:
        df["NPS_category"] = pd.cut(
            df["G1A"],
            bins=[-1, 6, 8, 10],
            labels=["Detractor", "Passive", "Promoter"],
        )

    if "loyalty_segment" not in df.columns:
        df = _add_loyalty_segment(df)

    if "loyalty_segment_display" not in df.columns:
        df["loyalty_segment_display"] = df["loyalty_segment"].replace(
            {"Hidden Gem": "At Risk", "Lost Cause": "At Risk"}
        )

    if "service_failure" not in df.columns:
        _teller = df.get("failure_teller", pd.Series(False, index=df.index))
        _cs = df.get("failure_cs", pd.Series(False, index=df.index))
        df["service_failure"] = _teller | _cs

    # rata-rata dimensi
    _rata_map = {
        "rata_teller":   [c for c in df.columns if c.startswith("T_TL3_") and int(c.split("_")[-1]) % 3 == 2],
        "rata_cs":       [c for c in df.columns if c.startswith("T_CS3_") and int(c.split("_")[-1]) % 3 == 2],
        "rata_atm":      [c for c in df.columns if c.startswith("T_AT3_") and int(c.split("_")[-1]) % 3 == 2],
        "rata_fisik":    [c for c in df.columns if c.startswith("T_KC2_") and int(c.split("_")[-1]) % 3 == 2],
        "rata_sekuriti": [c for c in df.columns if c.startswith("T_SC2_") and int(c.split("_")[-1]) % 3 == 2],
        "rata_brand":    [c for c in df.columns if c.startswith("T_C1B_") and int(c.split("_")[-1]) % 3 == 2],
    }
    for col_name, src_cols in _rata_map.items():
        if col_name not in df.columns and src_cols:
            df[col_name] = df[src_cols].mean(axis=1, skipna=True)

    return df


def _add_loyalty_segment(df: pd.DataFrame) -> pd.DataFrame:
    high_sat = df["E1A"] >= 5 if "E1A" in df.columns else pd.Series(True, index=df.index)
    high_nps = df["G1A"] >= 9 if "G1A" in df.columns else pd.Series(True, index=df.index)

    conditions = [
        high_sat & high_nps,
        high_sat & ~high_nps,
        ~high_sat & high_nps,
        ~high_sat & ~high_nps,
    ]
    choices = ["Loyal Aman", "Latent Risk", "Hidden Gem", "Lost Cause"]
    df["loyalty_segment"] = np.select(conditions, choices, default="Latent Risk")
    return df


# ── IPA ──────────────────────────────────────────────────────
@st.cache_data
def load_ipa() -> dict:
    path = _get_data_path("processed", "hasil_ipa.pkl")
    if os.path.exists(path):
        with open(path, "rb") as f:
            return pickle.load(f)
    # Buat dari data mentah jika pkl belum ada
    return _compute_ipa()


def _compute_ipa() -> dict:
    df = load_main_data()

    raw_path = _get_data_path("raw", "Deka_project_dataset_BankXYZ.xlsx")
    try:
        df_raw = pd.read_excel(raw_path, header=0)
        kode_var = df_raw.iloc[0]
        label_map = {str(v).strip(): str(k).strip()
                     for k, v in kode_var.items() if pd.notna(v)}
    except Exception:
        label_map = {}

    dimensi_cfg = {
        "Fisik":    ("T_KC1_", "T_KC2_"),
        "Brand":    ("T_C1A_", "T_C1B_"),
        "Teller":   ("T_TL2_", "T_TL3_"),
        "CS":       ("T_CS2_", "T_CS3_"),
        "ATM":      ("T_AT2_", "T_AT3_"),
        "Sekuriti": ("T_SC1_", "T_SC2_"),
    }

    hasil = {}
    for nama, (pref_k, pref_p) in dimensi_cfg.items():
        cols_k = sorted([c for c in df.columns if c.startswith(pref_k)],
                        key=lambda x: int(x.split("_")[-1]))
        cols_p_raw = [c for c in df.columns if c.startswith(pref_p)
                      and int(c.split("_")[-1]) % 3 == 2]
        cols_p = sorted(cols_p_raw, key=lambda x: int(x.split("_")[-1]))

        if nama == "Teller":
            df_f = df[df["PANEL"] == "Teller (KUOTA 50%)"]
        elif nama == "CS":
            df_f = df[df["PANEL"] == "CS (KUOTA 50%)"]
        else:
            df_f = df

        rows = []
        n = min(len(cols_k), len(cols_p))
        for i in range(n):
            mk = df_f[cols_k[i]].mean(skipna=True)
            mp = df_f[cols_p[i]].mean(skipna=True)
            if pd.isna(mk) or pd.isna(mp):
                continue
            lbl = label_map.get(cols_k[i], cols_k[i])
            rows.append({
                "label": lbl,
                "kolom_k": cols_k[i],
                "kolom_p": cols_p[i],
                "mean_kepentingan": mk,
                "mean_kepuasan": mp,
                "gap": mk - mp,
            })

        if not rows:
            continue

        ipa_df = pd.DataFrame(rows)
        mean_k = ipa_df["mean_kepentingan"].mean()
        mean_p = ipa_df["mean_kepuasan"].mean()

        def _kuadran(row):
            if row["mean_kepentingan"] >= mean_k and row["mean_kepuasan"] < mean_p:
                return "Prioritas Utama"
            elif row["mean_kepentingan"] >= mean_k and row["mean_kepuasan"] >= mean_p:
                return "Pertahankan"
            elif row["mean_kepentingan"] < mean_k and row["mean_kepuasan"] < mean_p:
                return "Prioritas Rendah"
            else:
                return "Berlebihan"

        ipa_df["kuadran"] = ipa_df.apply(_kuadran, axis=1)
        hasil[nama] = ipa_df

    return hasil


# ── EMOTION ──────────────────────────────────────────────────
@st.cache_data
def load_emotion() -> dict:
    path = _get_data_path("processed", "emotion_results.pkl")
    if os.path.exists(path):
        with open(path, "rb") as f:
            return pickle.load(f)
    return _compute_emotion()


def _compute_emotion() -> dict:
    df = load_main_data()

    emosi_cols_xyz  = [c for c in df.columns if c.startswith("T_H1A_") and int(c.split("_")[-1]) % 3 == 2]
    emosi_cols_komp = [c for c in df.columns if c.startswith("T_H1A_") and int(c.split("_")[-1]) % 3 == 0]

    emosi_labels = [
        "Senang", "Puas", "Nyaman", "Percaya", "Bangga", "Kagum",
        "Kecewa", "Tidak Puas", "Frustrasi", "Tidak Percaya", "Malu", "Marah",
        "Khawatir", "Bingung", "Lelah",
    ]

    rows_emosi = []
    for i, (c_xyz, c_komp) in enumerate(zip(emosi_cols_xyz[:len(emosi_labels)],
                                             emosi_cols_komp[:len(emosi_labels)])):
        label = emosi_labels[i]
        mean_xyz  = df[c_xyz].mean(skipna=True)
        mean_komp = df[c_komp].mean(skipna=True)
        kategori  = "positif" if i < 6 else "negatif"
        rows_emosi.append({
            "emosi": label, "mean_xyz": mean_xyz,
            "mean_komp": mean_komp, "kategori": kategori,
        })
    df_emosi = pd.DataFrame(rows_emosi)

    # Korelasi dengan NPS
    rows_korr = []
    for i, c_xyz in enumerate(emosi_cols_xyz[:len(emosi_labels)]):
        label = emosi_labels[i]
        if "G1A" in df.columns:
            valid = df[[c_xyz, "G1A"]].dropna()
            if len(valid) > 10:
                korr = valid[c_xyz].corr(valid["G1A"])
                rows_korr.append({"emosi": label, "korelasi": korr})
    df_korelasi = pd.DataFrame(rows_korr)

    # Profil segmen
    rows_profil = []
    for i, c_xyz in enumerate(emosi_cols_xyz[:len(emosi_labels)]):
        label = emosi_labels[i]
        row = {"emosi": label, "kategori": "positif" if i < 6 else "negatif"}
        if "NPS_category" in df.columns:
            row["promoter"]  = df[df["NPS_category"] == "Promoter"][c_xyz].mean(skipna=True)
            row["passive"]   = df[df["NPS_category"] == "Passive"][c_xyz].mean(skipna=True)
            row["detractor"] = df[df["NPS_category"] == "Detractor"][c_xyz].mean(skipna=True)
        rows_profil.append(row)
    df_profil_segmen = pd.DataFrame(rows_profil)

    nama_emosi = emosi_labels
    emosi_xyz  = {row["emosi"]: row["mean_xyz"] for row in rows_emosi}

    return {
        "df_emosi": df_emosi,
        "df_korelasi": df_korelasi,
        "df_profil_segmen": df_profil_segmen,
        "nama_emosi": nama_emosi,
        "emosi_xyz": emosi_xyz,
    }


# ── COMPETITIVE ───────────────────────────────────────────────
@st.cache_data
def load_competitive() -> dict:
    path = _get_data_path("processed", "competitive_results.pkl")
    if os.path.exists(path):
        with open(path, "rb") as f:
            return pickle.load(f)
    return _compute_competitive()


def _compute_competitive() -> dict:
    df = load_main_data()

    rata_map = {
        "Fisik":    ("rata_fisik",    [c for c in df.columns if c.startswith("T_KC2_") and int(c.split("_")[-1]) % 3 == 0]),
        "Brand":    ("rata_brand",    [c for c in df.columns if c.startswith("T_C1B_")  and int(c.split("_")[-1]) % 3 == 0]),
        "Teller":   ("rata_teller",   [c for c in df.columns if c.startswith("T_TL3_") and int(c.split("_")[-1]) % 3 == 0]),
        "CS":       ("rata_cs",       [c for c in df.columns if c.startswith("T_CS3_") and int(c.split("_")[-1]) % 3 == 0]),
        "ATM":      ("rata_atm",      [c for c in df.columns if c.startswith("T_AT3_") and int(c.split("_")[-1]) % 3 == 0]),
        "Sekuriti": ("rata_sekuriti", [c for c in df.columns if c.startswith("T_SC2_") and int(c.split("_")[-1]) % 3 == 0]),
    }

    rows = []
    dimensi_xyz  = {}
    dimensi_komp = {}
    for nama, (col_xyz, cols_komp) in rata_map.items():
        mean_xyz  = df[col_xyz].mean(skipna=True) if col_xyz in df.columns else np.nan
        mean_komp = df[cols_komp].mean(skipna=True).mean() if cols_komp else np.nan
        rows.append({
            "dimensi": nama, "mean_xyz": mean_xyz,
            "mean_komp": mean_komp, "gap": mean_xyz - mean_komp,
        })
        dimensi_xyz[nama]  = mean_xyz
        dimensi_komp[nama] = mean_komp

    df_benchmark = pd.DataFrame(rows)

    # NPS
    nps_xyz = nps_komp = 0
    if "G1A" in df.columns and "G1B" in df.columns:
        def _nps(series):
            p = (series >= 9).mean() * 100
            d = (series < 7).mean() * 100
            return p - d
        nps_xyz  = _nps(df["G1A"].dropna())
        nps_komp = _nps(df["G1B"].dropna())

    return {
        "df_benchmark": df_benchmark,
        "dimensi_xyz":  dimensi_xyz,
        "dimensi_komp": dimensi_komp,
        "nps_xyz":  nps_xyz,
        "nps_komp": nps_komp,
    }


# ── SEGMENTS ─────────────────────────────────────────────────
@st.cache_data
def load_segments() -> dict:
    df = load_main_data()
    seg = df["loyalty_segment_display"].value_counts().to_dict() if "loyalty_segment_display" in df.columns else {}
    return {"counts": seg}
