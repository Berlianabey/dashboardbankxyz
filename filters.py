import streamlit as st
import pandas as pd
from utils.theme import WHITE, GRAY_BORDER, NAVY_DARK


def render_filters(df: pd.DataFrame) -> pd.DataFrame:
    """Render sidebar filters and return filtered dataframe."""
    with st.sidebar:
        st.markdown(f"""
        <div style="padding: 16px 0 8px 0;">
            <div style="font-size:1rem;font-weight:700;color:{WHITE};
                font-family:Poppins,sans-serif;margin-bottom:4px;">
                🏦 Bank XYZ
            </div>
            <div style="font-size:0.75rem;color:rgba(255,255,255,0.6);">
                Customer Experience Dashboard
            </div>
        </div>
        <hr style="border:none;border-top:1px solid rgba(255,255,255,0.2);margin:8px 0 16px 0;">
        """, unsafe_allow_html=True)

        st.markdown(f'<p style="color:rgba(255,255,255,0.8);font-size:0.8rem;font-weight:600;margin-bottom:8px;">🔍 FILTER DATA</p>', unsafe_allow_html=True)

        # ── Provinsi ─────────────────────────────────────────
        prov_options = ["Semua"] + sorted(df["PROV"].dropna().unique().tolist())
        prov_sel = st.selectbox("Provinsi", prov_options, key="filter_prov")

        # ── Cabang ───────────────────────────────────────────
        df_prov = df if prov_sel == "Semua" else df[df["PROV"] == prov_sel]
        cab_options = ["Semua"] + sorted(df_prov["CABANG"].dropna().unique().tolist())
        cab_sel = st.selectbox("Cabang", cab_options, key="filter_cab")

        # ── Panel / Touchpoint ───────────────────────────────
        panel_options = ["Semua"] + sorted(df["PANEL"].dropna().unique().tolist()) \
            if "PANEL" in df.columns else ["Semua"]
        panel_sel = st.selectbox("Touchpoint / Panel", panel_options, key="filter_panel")

        # ── Lama Nasabah ─────────────────────────────────────
        lama_order = [
            "1 bulan s/d 3 bulan", "3 bulan s/d 11 bulan",
            "1 tahun s/d 2 tahun 11 bulan",
            "3 tahun s/d 4 tahun 11 bulan", "5 tahun atau lebih",
        ]
        lama_options = ["Semua"] + [l for l in lama_order if l in df["S4"].values] \
            if "S4" in df.columns else ["Semua"]
        lama_sel = st.selectbox("Lama Nasabah", lama_options, key="filter_lama")

        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        st.markdown(f'<p style="color:rgba(255,255,255,0.5);font-size:0.7rem;text-align:center;">'
                    f'v2.0 · Revised 2026</p>', unsafe_allow_html=True)

    # ── Apply filters ────────────────────────────────────────
    df_out = df.copy()
    if prov_sel != "Semua":
        df_out = df_out[df_out["PROV"] == prov_sel]
    if cab_sel != "Semua":
        df_out = df_out[df_out["CABANG"] == cab_sel]
    if panel_sel != "Semua" and "PANEL" in df_out.columns:
        df_out = df_out[df_out["PANEL"] == panel_sel]
    if lama_sel != "Semua" and "S4" in df_out.columns:
        df_out = df_out[df_out["S4"] == lama_sel]

    return df_out
