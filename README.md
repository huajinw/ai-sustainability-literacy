# About the LLM Footprint Comparator Dashboard

A Streamlit dashboard for estimating and comparing the environmental footprint (energy, electricity, and cooling water) of LLM inference workloads against a plain Google Search baseline. This version is specifically developed for teaching about environment impact of LLMs, adapted from [a more comprehensive dashboard](https://cmu-lib.github.io/ai-sustainability/). The related teaching materials can be found in our [Lesson Plan](https://sites.google.com/pitt.edu/ai-sustainability), "The Environmental Cost of a “Better” Answer". 

## Dashboard Overview

The dashboard presents a single-page side-by-side comparison across three columns: **Scenario A**, **Scenario B**, and **Baseline (Google Search)**.

### Inputs
* **Scenario A & Scenario B:** Select a **Model**, calibration **Anchor**, and datacenter **Location**, then enter **Input Word Count** and **Output Word Count**.
* **Baseline (Google Search):** Enter the **# Searches** and select a datacenter **Location**.

### Outputs
* **Comparison Results:** Use the **Estimate** selector (`Low`, `Mid`, or `High`) to view three side-by-side bar charts comparing Scenario A, Scenario B, and Google Search across:
  1. **IT Equipment Energy (Wh)**
  2. **Data Center Electricity (Wh)**
  3. **Cooling Water (mL)**
* **Interval Output Table:** Displays the full `Low`, `Mid`, and `High` uncertainty intervals for every metric and scenario, with a button to download the results as `footprint_comparison.csv`.

## Terminology

### IT Equipment Energy
This is location-agnostic: it reflects only the compute energy of the model itself, not the surrounding datacenter infrastructure.

### Data Center Electricity
The IT energy is scaled by PUE (Power Usage Effectiveness) to account for datacenter overhead (cooling systems, power distribution losses, lighting, etc.)

### Cooling Water
Data center electricity is multiplied by WUE (Water Usage Effectiveness) to estimate direct on-site water evaporated for cooling. 

## Reference
[1] N. Jegham, M. Abdelatti, C. Y. Koh, L. Elmoubarki, and A. Hendawi, “How Hungry is AI? Benchmarking Energy, Water, and Carbon Footprint of LLM Inference,” Nov. 24, 2025, arXiv: arXiv:2505.09598. doi: 10.48550/arXiv.2505.09598.
