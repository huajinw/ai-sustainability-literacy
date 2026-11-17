"""
Word- and token-based estimation of LLM inference energy, electricity, and cooling water use
using precomputed per-token energy coefficient intervals (alpha ranges).

Workflow:
1) Convert user-entered word counts to estimated token counts (1 word ≈ 1.33 tokens).
2) Load alpha ranges (Wh/token) derived from Table 4 (mean ± std) and stored externally.
3) Scale alpha by total tokens to obtain IT energy.
4) Apply location-specific PUE and WUE to estimate data center electricity and
   direct on-site cooling water consumption.
"""

import csv
import json
import os
from dataclasses import dataclass
from typing import Dict

# Standard English approximation: 3 words ≈ 4 tokens (1 word ≈ 1.33 tokens)
TOKENS_PER_WORD: float = 4.0 / 3.0


def words_to_tokens(words: int) -> int:
    """Convert an English word count into an estimated token count."""
    return round(int(words) * TOKENS_PER_WORD)


# =====================================================================
# 1) Load precomputed alpha ranges
# =====================================================================
with open("alpha_range_data/alpha_ranges_full_anchors.json", "r", encoding="utf-8") as f:
    ALPHA_TABLE = json.load(f)


# =====================================================================
# 2) Core data structure
# =====================================================================

@dataclass(frozen=True)
class Interval:
    """Closed interval representation for uncertainty propagation."""
    lo: float
    mid: float
    hi: float


# =====================================================================
# 3) IT energy estimation (model-level, location-agnostic)
# =====================================================================

def estimate_it_energy_interval(
    model: str,
    anchor: str,
    total_tokens: int,
) -> Interval:
    """Estimate inference-time IT energy consumption (Wh) as an interval."""
    entry = ALPHA_TABLE[model][anchor]

    alpha_lo  = entry["alpha_min_wh_per_token"]
    alpha_mid = entry["alpha_mid_wh_per_token"]
    alpha_hi  = entry["alpha_max_wh_per_token"]

    return Interval(
        lo=alpha_lo  * total_tokens,
        mid=alpha_mid * total_tokens,
        hi=alpha_hi  * total_tokens,
    )


# =====================================================================
# 4) Location-specific scaling parameters
# =====================================================================

def _load_location_params(csv_path: str) -> Dict[str, Dict[str, float]]:
    params: Dict[str, Dict[str, float]] = {}
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            params[row["location"]] = {
                "pue": float(row["pue"]),
                "wue": float(row["wue"]),
            }
    return params


_LOCATION_CSV = os.path.join(os.path.dirname(__file__), "config", "location_params.csv")
LOCATION_PARAMS: Dict[str, Dict[str, float]] = _load_location_params(_LOCATION_CSV)


# =====================================================================
# 5) End-to-end footprint estimation (IT → electricity → water)
# =====================================================================

def estimate_footprint_interval(
    model: str,
    anchor: str,
    total_tokens: int,
    location: str,
):
    """
    Estimate energy, electricity, and on-site cooling water consumption
    as uncertainty intervals.
    """
    energy_it = estimate_it_energy_interval(
        model=model,
        anchor=anchor,
        total_tokens=total_tokens,
    )

    pue = LOCATION_PARAMS[location]["pue"]
    wue = LOCATION_PARAMS[location]["wue"]

    electricity_dc = Interval(
        lo=(energy_it.lo  / 1000.0) * pue,
        mid=(energy_it.mid / 1000.0) * pue,
        hi=(energy_it.hi  / 1000.0) * pue,
    )

    water_onsite = Interval(
        lo=electricity_dc.lo  * wue,
        mid=electricity_dc.mid * wue,
        hi=electricity_dc.hi  * wue,
    )

    return {
        "energy_it_wh": energy_it,
        "electricity_dc_kwh": electricity_dc,
        "water_onsite_l": water_onsite,
    }