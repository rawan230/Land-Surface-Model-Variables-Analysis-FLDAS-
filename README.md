# 🌬️🌧️🔥 Land Surface Model Variables Analysis — India (FLDAS)

**Notebook:** [`Land Surface Model Variables Analysis.ipynb`](Land%20Surface%20Model%20Variables%20Analysis.ipynb)

## Step 4: Climatic Variables + Land Cover — Biswas et al.-Aligned Feature Set — India (2000–2022)

> **Renumbered 2026-08-17**: this was "Step 6" before — moved to Step 4 since it's
> an independent preprocessing step that always ran before assembly/training,
> regardless of its old number (the previous numbering was a historical artifact
> of when this notebook was added to the project, not a reflection of execution
> order). No content or code changed, only the label.

**Extends:** FLDAS_NOAH01_C_GL_M.001 (Noah Land Surface Model, MERRA-2 + CHIRPS
forced), monthly, 0.1°, plus the ESA CCI/C3S LCCS land-cover archive.
**Data:** `FLDAS_NOAH01_C_GL_M.A<YYYYMM>.001.nc`, one file per month
**Study period:** 1 Nov 2000 – 15 Dec 2022 (266 months, complete series) —
matches Step 1 (fire), Step 2 (NDVI), Step 3 (LST) and Step 5 (integration)
exactly, so every variable here is directly joinable on `(year, month)`
against those other steps' outputs.

### Biswas et al. variable coverage

This notebook targets the full baseline variable set (NDVI and LST Day/Night
are covered elsewhere, not repeated here) so results are directly comparable
to that study:

| # | Biswas et al. variable | Source | Status |
|---|---|---|---|
| 1 | Air Temperature (K) | `Tair_f_tavg` | New in this notebook |
| 2 | Wind Speed (m/s) | `Wind_f_tavg` | Carried over |
| 3 | Specific Humidity (kg/kg) | `Qair_f_tavg` | New (previously internal-only, used for RH) |
| 4 | Precipitation (mm/h) | `Rainf_f_tavg` × 3600 | New unit (previously mm/month only, kept alongside) |
| 5 | Soil Moisture (kg/m²) | `SoilMoi*_tavg` (4 depth layers) | New — surface (0-10cm) as the headline layer, full 0-200cm profile as a bonus |
| 6 | Net LW Radiation (W/m²) | `Lwnet_tavg` | New |
| 7 | Fire Points (CSV) | Step 1 archive | Carried over (fire coincidence check) |
| 8 | Land Cover (22 classes) | ESA CCI/C3S LCCS, reclassified to the 22 base LCCS parent codes | New |
| 9 | Burned Area | — | **Not available in this project** — no MODIS MCD64A1/FireCCI/GABAM archive present; fire points remain the only fire-occurrence signal |
| — | Relative Humidity (%) | Derived (Clausius-Clapeyron) | Bonus, not in Biswas et al. but kept since it's a byproduct of #1/#3 |

### What this step delivers

| # | Metric | Notes |
|---|---|---|
| 1–6 | Climatology, anomaly, Mann-Kendall trend (monthly) + significance (p-value) | Same treatment as wind/precip/RH for every new variable |
| 7 | Fire coincidence | Are fire-affected pixel-months drier / windier / lower-humidity / lower-soil-moisture? |
| 8 | NDVI-grid reprojection | `rasterio.warp.reproject`, bilinear (FLDAS 0.1° → NDVI grid 0.01° is upsampling) |
| 9 | Land cover 22-class fractions | Per-pixel fractional cover of each ESA CCI LCCS base class, area-averaged onto the NDVI grid |

### Design notes

- FLDAS is natively monthly (one file = one month already), unlike MODIS
  LST's 8-day composites, so there's no multi-observation-per-month
  aggregation step — each file is read, cropped to an India bounding box,
  and stacked directly.
- FLDAS is global at 0.1° with `Y` ascending (south→north); cropped to an
  India bounding box and flipped to north-up so its affine transform follows
  the same raster convention as the project's other layers.
- GPU-accelerated where it matters: CuPy runs a row-tiled (memory-bounded)
  Mann-Kendall trend test on the monthly arrays, with auto-fallback to CPU
  (NumPy) if no CUDA device is found. The trend test also computes a
  two-sided normal-approximation p-value (erf-based, same formula as Step
  2/NDVI and Step 3/LST), so trend significance is reported consistently
  across all three steps.

### How to run

```bash
pip install -r requirements.txt
jupyter nbconvert --to notebook --execute --inplace "Land Surface Model Variables Analysis.ipynb"
# or open it in Jupyter/VS Code and run all cells top to bottom
```

Requires the raw FLDAS monthly `.nc` archive in this folder (not tracked in
git — see `download_fldas_missing.py`) and Step 1's fire-point CSV.

### Getting the raw data

The 277 monthly `.nc` files (~32 GB total, ~120 MB each) are not tracked in
this repo. [`download_fldas_missing.py`](download_fldas_missing.py) fills in
any gaps against the GES DISC subset manifest already in this folder
(`subset_FLDAS_NOAH01_C_GL_M_001_*.txt`):

```bash
python download_fldas_missing.py --dry-run   # show what's missing
python download_fldas_missing.py             # download it
```

Requires a free NASA Earthdata Login with the "NASA GESDISC DATA ARCHIVE"
application authorized, and a `_netrc` file with those credentials (see the
script's docstring for exact setup).

## Results (2000-11-01 → 2022-12-15, 266 months)

- **Grid**: FLDAS cropped to India bounds is 335 × 315 px at 0.1° resolution; the India boundary mask keeps 29,056 of 105,525 pixels (27.5%).
- **All 266 months** streamed and cropped in **40.3 seconds**.

**National monthly means (2000–2022):**

| Variable | Mean |
|---|---:|
| Wind speed | 4.46 m/s |
| Precipitation | 94.5 mm/month (0.129 mm/h) |
| Relative humidity | 52.6 % |
| Air temperature | 296.1 K (22.9 °C) |
| Net LW radiation | −84.7 W/m² |
| Soil moisture (0–10cm) | 26.5 kg/m² |

**Mann-Kendall trend (τ, monthly resolution, computed in ~21s GPU-tiled):**

| Variable | Mean τ | Median τ |
|---|---:|---:|
| Wind | −0.026 | −0.034 |
| Precipitation | +0.045 | +0.037 |
| Relative humidity | +0.096 | +0.075 |
| Air temperature | −0.007 | −0.014 |
| Net LW radiation | +0.082 | +0.068 |
| Soil moisture | +0.090 | +0.072 |

**Trend significance** (two-sided normal-approximation p-value on the same S-statistic,
identical formula to Step 2/NDVI and Step 3/LST's Mann-Kendall test — diagnostic only,
doesn't change the τ/anomaly values above):

| Variable | Significant increasing (p<0.05) | Significant decreasing (p<0.05) | Total significant | % of valid pixels |
|---|---:|---:|---:|---:|
| Wind | 1,159 | 2,569 | 3,728 / 28,813 | 12.9% |
| Precipitation | 2,662 | 92 | 2,754 / 28,813 | 9.6% |
| Relative humidity | 13,298 | 115 | 13,413 / 28,813 | 46.6% |
| Air temperature | 634 | 2 | 636 / 28,813 | 2.2% |
| Net LW radiation | 10,197 | 0 | 10,197 / 28,759 | 35.5% |
| Soil moisture | 11,587 | 28 | 11,615 / 28,759 | 40.4% |

Relative humidity, net LW radiation, and soil moisture show the most spatially extensive
significant trends (35–47% of valid pixels), almost entirely increasing. Air temperature
has the weakest and least significant trend (2.2% of pixels), consistent with its
near-zero mean τ. `FLDAS_trend_summary.csv` also carries `p_mean` and
`n_significant_increasing_p05`/`n_significant_decreasing_p05`/`n_valid_pixels` per
variable for the full per-variable breakdown.

**Fire coincidence** (541,545 Step 1 fire points, 100% inside the FLDAS grid bounds) — conditions at fire pixel-months vs. the grid-wide average:

| Variable | At fire pixel-months | Grid-wide |
|---|---:|---:|
| Precipitation anomaly | −5.6 mm | +0.7 mm |
| Wind anomaly | +0.00 m/s | −0.01 m/s |
| RH anomaly | −1.8 % | +0.3 % |
| Air temp anomaly | +0.29 K | −0.01 K |
| Soil moisture anomaly | −0.48 kg/m² | +0.13 kg/m² |

Fire-affected pixel-months are drier (both precipitation and soil moisture
below normal) and slightly warmer than the grid-wide average — consistent
with expected fire-weather conditions.

**Land cover (ESA CCI/C3S, 2020, 22 base classes, reclassified and computed in 26.9s):**

Top 5 classes by national mean fraction (India-masked):

| Class | Mean fraction |
|---|---:|
| Cropland, rainfed | 35.00% |
| Cropland, irrigated | 20.94% |
| Tree, broadleaved deciduous | 8.02% |
| Grassland | 5.34% |
| Mosaic natural vegetation | 4.72% |

### Outputs (`FLDAS_Outputs/`)

| File | Contents |
|---|---|
| `FLDAS_monthly_statistics_NDVI_aligned.csv` | Monthly wind/precip/RH/air temp/specific humidity/net LW radiation/soil moisture means + anomalies + fire counts; join key `(year, month)` |
| `FLDAS_trend_summary.csv` | Mann-Kendall τ summary (monthly resolution), 6 variables — tau_mean/tau_std/n_increasing_pixels/n_decreasing_pixels plus p_mean and significant-pixel counts (p<0.05) |
| Per-pixel GeoTIFFs (native FLDAS grid) | Climatology, anomaly, τ, fire count — 6 climatic variables |
| `NDVI_Aligned_GeoTIFFs/` | Same monthly features reprojected (bilinear) onto the NDVI/LST/fire/LULC grid (not tracked in git — regenerate by re-running) |
| `LandCover_22Class_Fractions_2020.tif` | 22-band GeoTIFF, one band per ESA CCI base class, fractional cover per NDVI pixel (~40 MB) |
| `LandCover_22Class_NationalMeanFraction.png` | Which classes actually dominate India's land surface |
| `FLDAS_Summary_Analysis.png`, `FLDAS_Summary_Analysis_Additional.png`, `FLDAS_Fire_Coincidence.png` | Summary plots |

**Biswas et al. variable coverage after this notebook:** 10 of 11 variables
are now produced and aligned (NDVI + LST Day/Night from other steps; air
temperature, wind speed, specific humidity, precipitation, soil moisture,
net LW radiation, fire points, and land cover from this notebook). **Burned
area is the one gap** — no MODIS MCD64A1/FireCCI/GABAM archive exists in
this project; only fire hotspot points are available as a fire-occurrence
signal.

## Citation

- Biswas, S. et al. (2025). *[see notebook header for full reference]*

## License

No license has been chosen yet for this repository's code. FLDAS data is
produced by NASA GSFC and is subject to NASA/GES DISC data-use terms. ESA
CCI/C3S land-cover data is subject to Copernicus data-use terms.
