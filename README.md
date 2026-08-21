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
matches Step 1 (fire), Step 2 (NDVI), Step 3 (LST) and Step 6 (integration,
renumbered 2026-08-19 from Step 5 to make room for Step 5 Terrain & Accessibility Analysis)
exactly, so every variable here is directly joinable on `(year, month)`
against those other steps' outputs.

### Biswas et al. variable coverage

> **Corrected 2026-08-18**: this table previously claimed Biswas et al. use an
> "11-variable" set with burned area as the sole gap. That was wrong on two counts,
> verified by direct extraction from the user's own copy of the paper: (1) their
> actual MaxEnt model (Table 3) uses **15 predictor variables**, not 11; (2) fire
> points, land cover, and burned area — previously counted here as three of the
> "11" — are **not** Table 3 predictors at all. Fire points are the response
> variable (what's being predicted, in both their study and this project); land
> cover is a forest-masking *input* used to filter fire points, not a model
> predictor; burned area is a Table 2 dataset used elsewhere in their paper, never
> a Table 3 predictor. Split below into what's actually comparable.

**Actual Table 3 MaxEnt predictors this notebook targets** (NDVI and LST Day/Night
are covered elsewhere, not repeated here):

| # | Biswas et al. variable | Importance % / Contribution % | Source | Status |
|---|---|---:|---|---|
| 1 | Air Temperature (K) | 13.1 / 3.8 | `Tair_f_tavg` | Covered |
| 2 | Specific Humidity (kg/kg) | 13.0 / 15.0 | `Qair_f_tavg` | Covered (previously internal-only, used for RH) |
| 3 | Soil Moisture (kg/m²) | 3.8 / 0.9 | `SoilMoi*_tavg` (4 depth layers) | Covered — surface (0-10cm) as the headline layer, full 0-200cm profile as a bonus |
| 4 | Precipitation (mm/h) | 3.6 / 1.7 | `Rainf_f_tavg` × 3600 | Covered (new unit; previously mm/month only, kept alongside) |
| 5 | Near-surface Wind Speed (m/s) | 2.4 / 4.3 | `Wind_f_tavg` | Covered |
| 6 | Net LW Radiation (W/m²) | 1.8 / 0.6 | `Lwnet_tavg` | Covered |
| 7 | **Distance to Roads** | 5.7 / 2.6 | OpenStreetMap (2022) | **Not yet computed anywhere in this pipeline** |
| 8 | **Distance to Railways** | 4.6 / 4.9 | OpenStreetMap (2022) | **Not yet computed anywhere in this pipeline** |
| 9 | **Distance to Waterways** | 0.5 / 1.7 | OpenStreetMap (2022) | **Not yet computed anywhere in this pipeline** |
| 10 | **Slope (°)** | 5.6 / 16.7 | DEM-derived | **Not yet computed anywhere in this pipeline** |
| 11 | **Aspect (°)** | 1.7 / 3.8 | DEM-derived | **Not yet computed anywhere in this pipeline** |
| 12 | **Elevation (m)** | 2.4 / 2.0 | DEM-derived | **Not yet computed anywhere in this pipeline** |

Plus NDVI (Step 2, 22.3/28.4%) and LST day/night (Step 3, 9.6/4.5% and 10.1/8.9%) —
**9 of the real 15 predictors covered, 6 genuinely missing**, all six being the
distance-to-infrastructure and topographic variables above (combined 10.8% + 9.7% =
20.5% of Biswas et al.'s total model contribution).

**Supporting datasets this notebook also carries, not Table 3 predictors in either
study**:

| Dataset | Source | Status | Role in Biswas et al. |
|---|---|---|---|
| Fire Points (CSV) | Step 1 archive | Carried over (fire coincidence check) | Response variable — what the model predicts, not an input |
| Land Cover (22 classes) | ESA CCI/C3S LCCS, reclassified to the 22 base LCCS parent codes | Covered | Used to build the forest-only fire-point mask (same role in this project's Step 1), not a Table 3 predictor |
| Burned Area | — | **Not available in this project** — no MODIS MCD64A1/FireCCI/GABAM archive present | A Table 2 dataset in their paper, but never appears in their Table 3 predictor list — was never actually a predictor gap |
| Relative Humidity (%) | Derived (Clausius-Clapeyron) | Bonus | Not in Biswas et al. at all, kept since it's a byproduct of #1/#2 above |

### What this step delivers

| # | Metric | Notes |
|---|---|---|
| 1–6 | Climatology, anomaly, Mann-Kendall trend (monthly) + significance (p-value) | Same treatment as wind/precip/RH for every new variable |
| 7 | Fire coincidence | Are fire-affected pixel-months drier / windier / lower-humidity / lower-soil-moisture? |
| 8 | NDVI-grid reprojection | `rasterio.warp.reproject`, bilinear (FLDAS 0.1° → NDVI grid 0.01° is upsampling) |
| 9 | Land cover 22-class fractions | Per-pixel fractional cover of each ESA CCI LCCS base class, area-averaged onto the NDVI grid |

Note: bilinear interpolation does not recover genuine sub-grid detail; FLDAS-derived
features carry ~11km effective spatial resolution despite being stored on the 1km
analysis grid, and should not be read as independent 1km observations.

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
doesn't change the τ/anomaly values above), reported both as the **raw p<0.05 count
(uncorrected)** and after **Benjamini-Hochberg FDR correction** (Wilks 2006, "On 'Field
Significance' and the False Discovery Rate," *J. Appl. Meteor. Climatol.* 45:1181) — the
same multiple-comparisons fix already applied to Step 3 (LST)'s Mann-Kendall trend maps.
FDR is applied per-variable across that variable's full set of valid (n_valid≥10)
per-pixel p-values (`statsmodels.stats.multitest.multipletests(method='fdr_bh',
alpha=0.05)`); the **FDR-corrected columns are what the pipeline treats as real** —
the raw columns are kept only so the shrinkage from correction is visible and honestly
reported, not silently swapped out:

| Variable | Raw p<0.05 total | FDR-corrected total | FDR increasing | FDR decreasing | % of valid pixels (FDR) |
|---|---:|---:|---:|---:|---:|
| Wind | 3,728 / 28,813 | 1,015 | 385 | 630 | 3.5% |
| Precipitation | 2,754 / 28,813 | 1,840 | 1,830 | 10 | 6.4% |
| Relative humidity | 13,413 / 28,813 | 10,818 | 10,738 | 80 | 37.5% |
| Air temperature | 636 / 28,813 | 0 | 0 | 0 | 0.0% |
| Net LW radiation | 10,197 / 28,759 | 7,204 | 7,204 | 0 | 25.0% |
| Soil moisture | 11,615 / 28,759 | 6,926 | 6,908 | 18 | 24.1% |

Relative humidity, net LW radiation, and soil moisture remain the most spatially extensive
significant trends after correction (24–38% of valid pixels), almost entirely increasing.
Air temperature's already-weak raw signal (2.2% of pixels, 636 raw-significant) does not
survive FDR correction at all — **zero pixels remain significant**, meaning its apparent
raw trend was consistent with multiple-testing noise rather than a real spatial pattern.
The other five variables retain 27–81% of their raw-significant pixels after correction
(wind lowest at 27%, relative humidity highest at 81%) — a real but much gentler
shrinkage than Step 3 (LST)'s far larger pixel count saw, since FDR's correction strength
scales with how many tests are run: FLDAS's ~28,800 valid pixels per variable produce
far less p-value inflation to begin with than LST's millions. `FLDAS_trend_summary.csv` carries `p_mean` plus both
`n_significant_*_pixels_raw_p05` and `n_significant_*_pixels_fdr` (increasing/decreasing/
total) and `n_valid_pixels` per variable for the full per-variable breakdown.

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
| `FLDAS_trend_summary.csv` | Mann-Kendall τ summary (monthly resolution), 6 variables — tau_mean/tau_std/n_increasing_pixels/n_decreasing_pixels plus p_mean and BOTH raw p<0.05 (uncorrected) and Benjamini-Hochberg FDR-corrected (Wilks 2006) significant-pixel counts |
| Per-pixel GeoTIFFs (native FLDAS grid) | Climatology, anomaly, τ, FDR-corrected q-value and significance mask, fire count — 6 climatic variables |
| `NDVI_Aligned_GeoTIFFs/` | Same monthly features reprojected (bilinear) onto the NDVI/LST/fire/LULC grid (not tracked in git — regenerate by re-running) |
| `LandCover_22Class_Fractions_2020.tif` | 22-band GeoTIFF, one band per ESA CCI base class, fractional cover per NDVI pixel (~40 MB) |
| `LandCover_22Class_NationalMeanFraction.png` | Which classes actually dominate India's land surface |
| `FLDAS_Summary_Analysis.png`, `FLDAS_Summary_Analysis_Additional.png`, `FLDAS_Fire_Coincidence.png` | Summary plots |

**Biswas et al. variable coverage after this notebook (corrected 2026-08-18):** 9 of
their real 15 Table 3 predictors are now produced and aligned — NDVI + LST Day/Night
from other steps; air temperature, specific humidity, wind speed, precipitation, soil
moisture, and net LW radiation from this notebook. **Six predictors are still
genuinely missing**, none of them burned area: distance to roads / railways /
waterways (OSM, 10.8% combined contribution in their model) and slope / aspect /
elevation (DEM-derived, 9.7% combined contribution) — see the corrected table above.
Land cover and fire points are also produced by this notebook, but as supporting
datasets (forest-masking input and response variable respectively), not as Table 3
predictors in either study. Burned area was never actually a Table 3 predictor gap —
it's a Table 2 dataset in their paper used elsewhere, not one of the 15 — though this
project still has no MODIS MCD64A1/FireCCI/GABAM archive if it's wanted for other
purposes.

## Citation

- Biswas, S. et al. (2025). *[see notebook header for full reference]*

## License

No license has been chosen yet for this repository's code. FLDAS data is
produced by NASA GSFC and is subject to NASA/GES DISC data-use terms. ESA
CCI/C3S land-cover data is subject to Copernicus data-use terms.
