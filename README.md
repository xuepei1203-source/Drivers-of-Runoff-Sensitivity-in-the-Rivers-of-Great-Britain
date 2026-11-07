# Drivers of Runoff Sensitivity in the Rivers of Great Britain

**Code and figure reproduction materials for:**

Xue, P., Spracklen, D., & Holden, J. (2026). *Drivers of runoff sensitivity in the rivers of Great Britain*. **Hydrological Processes**, 40(9), e70696. https://doi.org/10.1002/hyp.70696

This repository contains Python workflows for **all six main figures and seven supplementary figures** from the study. The analysis covers **547 catchments in Great Britain**, examining runoff sensitivity and its climatic, land-surface, and catchment controls using observational datasets and generalized additive models (GAMs).

**Execution status:** The author has run the main and supplementary figure workflows successfully in their local Jupyter/Python environment. 

## Repository layout

```text
runoff-sensitivity-great-britain/
├── data/           # Input spreadsheets (subject to data-sharing permissions)
├── geodata/        # Catchment polygons and other spatial boundaries
├── scripts/        # Figure-generation and shared Python modules
├── results/        # Generated model predictions and summary tables
├── figures/        # Generated figure images
├── requirements.txt
└── README.md
```

## Figure workflows

All paths below are relative to the repository root. Scripts are stored in `scripts/`; figure outputs are written to `figures/` unless noted otherwise.

| Figure | Script(s) | Primary input(s) | Description |
|---|---|---|---|
| Figure 1 | `figure_01_spatial_IQR.py` | `data/Catchments ID.xlsx`, catchment geodata | Spatial patterns of the three runoff sensitivity metrics |
| Figure 2 | `figure_02_annual_GAM.py` | `data/Catchments ID.xlsx` | Selected annual GAM response curves |
| Figure 3 | `figure_03_seasonal_GAM.py` | `data/seasonalanalysis2_normalized.xlsx` | Selected seasonal GAM response curves |
| Figure 4 | `figure_04_annual_importance.py` | Annual analysis workbook | Annual predictor importance |
| Figure 5 | `figure_05_seasonal_importance.py` | Seasonal analysis workbook | Seasonal predictor importance |
| Figure 6 | `figure_06_generate_deltas.py`, `figure_06_perturbation_maps.py` | Annual analysis workbook, geodata | Maps of GAM responses to +10% predictor perturbations |
| Supplementary Figure 1 | `supplementary_figure_01.py` | Annual/catchment workbook, `data/stations.xlsx`, geodata | Catchment and precipitation-related spatial summaries |
| Supplementary Figure 2 | `supplementary_figure_02.py` | `data/Catchments ID.xlsx`, geodata | Spatial distributions of environmental predictors |
| Supplementary Figure 3 | `supplementary_figure_03.py` | Annual/catchment workbook, geodata | Additional spatial analysis |
| Supplementary Figure 4 | `supplementary_figure_04.py` | `data/Catchments ID.xlsx` | Annual GAM curves omitted from main Figure 2 |
| Supplementary Figure 5 | `supplementary_figure_05.py` | `data/seasonalanalysis2_normalized.xlsx` | Seasonal GAM curves omitted from main Figure 3 |
| Supplementary Figure 6 | Same scripts as Figure 6 | Annual analysis workbook, geodata | Maps of GAM responses to +20% predictor perturbations |
| Supplementary Figure 7 | `supplementary_figure_07_generate_data.py`, `supplementary_figure_07.py` | `data/Catchments ID.xlsx` | Static-covariate P10-to-P90 GAM effects |

**Figure 6 and Supplementary Figure 6 are generated together** by the perturbation workflow. They do not need separate model-fitting runs.

Supplementary Figures 4 and 5 are generated using their **own scripts**, rather than being treated as outputs of the main Figure 2/3 scripts.

## Installation

Use a Python environment with the dependencies listed in `requirements.txt`:

```bash
python -m pip install -r requirements.txt
```

Geospatial figures additionally require a working installation of the relevant spatial libraries and their native dependencies.

## Input data

The main input files used in the completed local workflows include:

- `data/Catchments ID.xlsx` — annual catchment attributes, identifiers, and runoff sensitivity metrics.
- `data/seasonalanalysis2_normalized.xlsx` — seasonal analysis dataset.
- `data/stations.xlsx` — station-level data used for Supplementary Figure 1.
- `geodata/merged_output.*`, `geodata/infuse_gb_2011.*`, and `geodata/CTRY_DEC_2022_UK_BUC.*` — geospatial inputs used by relevant map scripts.

Some scripts may require additional columns or inputs defined in their source code. Check the script's default paths and expected columns if adapting this workflow to another dataset.

The annual workflows have been updated to use **`Catchments ID.xlsx` where applicable**, replacing earlier references to `ReID.xlsx`. No local drive letters or machine-specific absolute paths are required in the updated figure workflows.

The catchment dataset has an associated public record at https://zenodo.org/records/17350054. **Before uploading input spreadsheets or shapefiles to a public repository, confirm the redistribution rights for each dataset.** For ESRI shapefiles, retain the associated `.shp`, `.shx`, `.dbf`, and `.prj` files together.

## Running the figures

From the **repository root**, run the following commands in order. Where an individual script exposes optional command-line arguments, see its `--help` output.

```bash
# Main figures 1–5
python scripts/figure_01_spatial_IQR.py
python scripts/figure_02_annual_GAM.py
python scripts/figure_03_seasonal_GAM.py
python scripts/figure_04_annual_importance.py
python scripts/figure_05_seasonal_importance.py

# Figure 6 + Supplementary Figure 6 (10% and 20% perturbations)
python scripts/figure_06_generate_deltas.py
python scripts/figure_06_perturbation_maps.py

# Supplementary Figures 1–5
python scripts/supplementary_figure_01.py
python scripts/supplementary_figure_02.py
python scripts/supplementary_figure_03.py
python scripts/supplementary_figure_04.py
python scripts/supplementary_figure_05.py

# Supplementary Figure 7 (generate predictions before plotting)
python scripts/supplementary_figure_07_generate_data.py
python scripts/supplementary_figure_07.py
```

In Jupyter Notebook, scripts can instead be executed from the repository root with `%run`, for example:

```python
%run scripts/supplementary_figure_07_generate_data.py
%run scripts/supplementary_figure_07.py
```

For scripts using `Path(__file__).resolve().parents[1]`, execute the `.py` file with `python` or `%run` rather than pasting the entire source into a notebook cell.

## Generated results

- Figures are saved as PNG images under `figures/`.
- Figure 6 perturbation results are saved as `results/10_deltas.xlsx` and `results/20_deltas.xlsx`.
- Supplementary Figure 7 generates `results/static_P10_P90_deltas.xlsx`, followed by `figures/supplementary_figure_07.png` and `results/Static_structural_sensitivity_summary.xlsx`.

## Methodological notes

**Runoff sensitivity metrics:** The study considers IQR1, IQR2, and IQR3, reflecting alternative runoff and runoff-ratio sensitivity measures. See the published article for the formal definitions and interpretation.

**GAM fitting:** The figure scripts use pyGAM to estimate smooth predictor–response relationships. Where `Re ID` is included as a factor term, this should not be interpreted as identical to a mixed-model random intercept. Predictor importance based on GAM response ranges is not SHAP importance.

**Figure 6 / Supplementary Figure 6:** The workflow perturbs all 14 predictors by 10% and 20%, respectively, and clips values to the observed training range. Because the model predictors are normalized, multiplying these values by 1.10 or 1.20 is **not necessarily equivalent to increasing the corresponding physical quantity by 10% or 20%**. Within each response metric, the two map sets use shared 2nd–98th percentile colour limits.

**Supplementary Figure 7:** This is a separate P10-to-P90 experiment for five static catchment properties: catchment area, root depth, drainage density, terrain slope, and saturated hydraulic conductivity. The figure summarizes the resulting GAM-predicted differences; it does not replace the 14-predictor perturbation analysis.

**Spatial processing:** Some supplied plotting workflows use zero-filled missing values or panel-specific colour scales. Review these decisions before reusing the code for new scientific inference.

## Reproducibility and licensing

The author has successfully executed the figure workflows locally. Reproduction on another computer depends on having the required input files, compatible package versions, and functioning geospatial dependencies. 

Code licensing and data redistribution are separate matters. Add a `LICENSE` file once a code licence has been selected, and verify the terms of each underlying dataset before distributing it through GitHub.

## Citation

If you use this repository, please cite:

> Xue, P., Spracklen, D., & Holden, J. (2026). Drivers of runoff sensitivity in the rivers of Great Britain. *Hydrological Processes*, 40(9), e70696. https://doi.org/10.1002/hyp.70696
