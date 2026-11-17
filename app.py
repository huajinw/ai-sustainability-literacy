import csv as csv_module
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

from evaluation import (
    estimate_footprint_interval,
    words_to_tokens,
    TOKENS_PER_WORD,
    LOCATION_PARAMS,
    Interval,
    ALPHA_TABLE,
)

# ──────────────────────────────────────────────────────────────────────────────
# Config & constants
# ──────────────────────────────────────────────────────────────────────────────

def _load_baseline_params(csv_path: str) -> dict:
    with open(csv_path, newline="", encoding="utf-8") as f:
        return {row["name"]: row for row in csv_module.DictReader(f)}

_BASELINE_PARAMS = _load_baseline_params("config/baseline_params.csv")
_GOOGLE = _BASELINE_PARAMS["google-search"]
GOOGLE_WH_PER_QUERY = float(_GOOGLE["energy_wh_per_query"])
GOOGLE_LABEL  = _GOOGLE["label"]
GOOGLE_SOURCE = _GOOGLE["source"]
GOOGLE_YEAR   = _GOOGLE["year"]

PALETTE = ["#4C72B0", "#DD8452"]
GOOGLE_COLOR = "#8172B2"

st.set_page_config(page_title="LLM Footprint Comparator", layout="wide")
st.title("🌍 LLM Footprint Comparator")
st.caption(
    f"Google baseline: {GOOGLE_LABEL} = {GOOGLE_WH_PER_QUERY} Wh/query "
    f"({GOOGLE_SOURCE}, {GOOGLE_YEAR})  ·  "
    f"Word-to-token conversion: 1 word ≈ {TOKENS_PER_WORD:.2f} tokens"
)

models    = sorted(ALPHA_TABLE.keys())
anchors   = sorted(ALPHA_TABLE[models[0]].keys())
locations = list(LOCATION_PARAMS.keys())

# ──────────────────────────────────────────────────────────────────────────────
# Core helpers
# ──────────────────────────────────────────────────────────────────────────────

def interval_from_wh(wh: Interval, location: str):
    pue = LOCATION_PARAMS[location]["pue"]
    wue = LOCATION_PARAMS[location]["wue"]
    elec  = Interval(lo=(wh.lo / 1000) * pue, mid=(wh.mid / 1000) * pue, hi=(wh.hi / 1000) * pue)
    water = Interval(lo=elec.lo * wue,        mid=elec.mid * wue,        hi=elec.hi * wue)
    return elec, water

def compute_from_words(model: str, anchor: str, location: str, in_words: int, out_words: int):
    in_tok = words_to_tokens(in_words)
    out_tok = words_to_tokens(out_words)
    result = estimate_footprint_interval(
        model=model,
        anchor=anchor,
        total_tokens=in_tok + out_tok,
        location=location,
    )
    return result, in_tok, out_tok

def kwh_to_wh(iv: Interval) -> Interval:
    return Interval(lo=iv.lo * 1000, mid=iv.mid * 1000, hi=iv.hi * 1000)

def l_to_ml(iv: Interval) -> Interval:
    return Interval(lo=iv.lo * 1000, mid=iv.mid * 1000, hi=iv.hi * 1000)

# ──────────────────────────────────────────────────────────────────────────────
# Summary bar chart
# ──────────────────────────────────────────────────────────────────────────────

def _clean(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", alpha=0.22, linestyle="--")

def plot_summary_bars(entries, title, ylabel, estimate="Mid"):
    fig, ax = plt.subplots(figsize=(5.5, 4.8))
    labels = [e[0] for e in entries]
    mids   = [e[1] for e in entries]
    los    = [e[2] for e in entries]
    his    = [e[3] for e in entries]

    colors = PALETTE[: len(entries) - 1] + [GOOGLE_COLOR]
    xs = range(len(labels))
    vals = los if estimate == "Low" else (his if estimate == "High" else mids)

    ax.bar(xs, vals, color=colors, alpha=0.85, width=0.55)

    for i, v in enumerate(vals):
        ax.text(i, v, f"{v:.4f}", ha="center", va="bottom", fontsize=8, color="#222222")

    ax.set_xticks(list(xs))
    ax.set_xticklabels(labels, rotation=15, ha="right", fontsize=9.5)
    ax.set_title(title, fontsize=11, fontweight="bold", pad=10)
    ax.set_ylabel(ylabel, fontsize=9)
    ax.set_xlabel(f"showing {estimate.lower()} estimate", fontsize=8, color="#888888")
    ax.margins(y=0.15)
    _clean(ax)
    plt.tight_layout()
    return fig

# ══════════════════════════════════════════════════════════════════════════════
# SCENARIO INPUTS (2 Scenarios + Google Search Baseline)
# ══════════════════════════════════════════════════════════════════════════════

colA, colB, colG = st.columns(3)

with colA:
    st.subheader("Scenario A")
    model_a     = st.selectbox("Model",        models,    key="ma")
    anchor_a    = st.selectbox("Anchor",       anchors,   key="aa")
    loc_a       = st.selectbox("Location",     locations, key="la")
    in_words_a  = st.number_input("Input Words",  0, 375000, 20,  key="ina")
    out_words_a = st.number_input("Output Words", 0, 375000, 640, key="outa")
    rA, in_tok_a, out_tok_a = compute_from_words(model_a, anchor_a, loc_a, in_words_a, out_words_a)
    st.caption(f"≈ {in_tok_a + out_tok_a:,} tokens ({in_tok_a:,} in + {out_tok_a:,} out)")

with colB:
    st.subheader("Scenario B")
    model_b     = st.selectbox("Model",        models,    key="mb")
    anchor_b    = st.selectbox("Anchor",       anchors,   key="ab")
    loc_b       = st.selectbox("Location",     locations, key="lb")
    in_words_b  = st.number_input("Input Words",  0, 375000, 75,  key="inb")
    out_words_b = st.number_input("Output Words", 0, 375000, 225, key="outb")
    rB, in_tok_b, out_tok_b = compute_from_words(model_b, anchor_b, loc_b, in_words_b, out_words_b)
    st.caption(f"≈ {in_tok_b + out_tok_b:,} tokens ({in_tok_b:,} in + {out_tok_b:,} out)")

with colG:
    st.subheader(f"Baseline ({GOOGLE_LABEL})")
    searches   = st.number_input("# Searches", 1, 500, 1)
    google_loc = st.selectbox("Location", locations, key="gloc")
    g_energy = Interval(
        lo=GOOGLE_WH_PER_QUERY * searches,
        mid=GOOGLE_WH_PER_QUERY * searches,
        hi=GOOGLE_WH_PER_QUERY * searches,
    )
    g_elec, g_water = interval_from_wh(g_energy, google_loc)

# ══════════════════════════════════════════════════════════════════════════════
# COMPARISON RESULTS
# ══════════════════════════════════════════════════════════════════════════════

energy_ents = [
    ("Scenario A",    rA["energy_it_wh"].mid, rA["energy_it_wh"].lo, rA["energy_it_wh"].hi),
    ("Scenario B",    rB["energy_it_wh"].mid, rB["energy_it_wh"].lo, rB["energy_it_wh"].hi),
    ("Google Search", g_energy.mid,           g_energy.lo,           g_energy.hi),
]
elec_ents = [
    ("Scenario A",    kwh_to_wh(rA["electricity_dc_kwh"]).mid, kwh_to_wh(rA["electricity_dc_kwh"]).lo, kwh_to_wh(rA["electricity_dc_kwh"]).hi),
    ("Scenario B",    kwh_to_wh(rB["electricity_dc_kwh"]).mid, kwh_to_wh(rB["electricity_dc_kwh"]).lo, kwh_to_wh(rB["electricity_dc_kwh"]).hi),
    ("Google Search", kwh_to_wh(g_elec).mid,                   kwh_to_wh(g_elec).lo,                   kwh_to_wh(g_elec).hi),
]
water_ents = [
    ("Scenario A",    l_to_ml(rA["water_onsite_l"]).mid, l_to_ml(rA["water_onsite_l"]).lo, l_to_ml(rA["water_onsite_l"]).hi),
    ("Scenario B",    l_to_ml(rB["water_onsite_l"]).mid, l_to_ml(rB["water_onsite_l"]).lo, l_to_ml(rB["water_onsite_l"]).hi),
    ("Google Search", l_to_ml(g_water).mid,              l_to_ml(g_water).lo,              l_to_ml(g_water).hi),
]

st.divider()
st.subheader("Comparison Results")
ESTIMATE = st.selectbox("Estimate", ["Low", "Mid", "High"], index=1, key="estimate_manual")
c1, c2, c3 = st.columns(3)
with c1:
    st.pyplot(plot_summary_bars(energy_ents, "IT Equipment Energy (Wh)", "Wh", estimate=ESTIMATE))
with c2:
    st.pyplot(plot_summary_bars(elec_ents, "Data Center Electricity (Wh)", "Wh", estimate=ESTIMATE))
with c3:
    st.pyplot(plot_summary_bars(water_ents, "Cooling Water (mL)", "mL", estimate=ESTIMATE))

st.divider()
st.subheader("Interval Output Table")

def _make_df(ents, metric):
    return pd.DataFrame([
        {"Scenario": e[0], "Low": e[2], "Mid": e[1], "High": e[3], "Metric": metric}
        for e in ents
    ])

df_all = pd.concat([
    _make_df(energy_ents, "IT Equipment Energy (Wh)"),
    _make_df(elec_ents,   "Data Center Electricity (Wh)"),
    _make_df(water_ents,  "Cooling Water (mL)"),
])
st.dataframe(df_all, width="stretch")
st.download_button(
    "Download results as CSV",
    df_all.to_csv(index=False).encode("utf-8"),
    "footprint_comparison.csv",
    "text/csv",
)