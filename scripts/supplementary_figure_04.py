"""Supplementary Figure 4: annual GAM partial dependence for variables omitted from Figure 2.

Based on cells 7–8 of 250930draft8.ipynb. The published workbook uses
renamed columns; mappings below are explicit. The GAM includes a categorical
Re ID term, matching the notebook (pyGAM factor term, not a mixed-model fit).

Bootstrap: refit GAM on catchment-level samples, then evaluate smooth terms
on fixed grids. One bootstrap fit is reused across all 14 terms for efficiency.
This yields the same bootstrap procedure but a different random draw sequence
than the unseeded notebook; exact pixel identity is not guaranteed.
"""
from __future__ import annotations
import argparse
from pathlib import Path
from functools import reduce
from operator import add
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator, FormatStrFormatter
from pygam import LinearGAM, s, f

ROOT = Path(__file__).resolve().parents[1]
# Preferred Windows project location for generated figures.
OUTPUT_DIR = ROOT / 'figures'
PREDICTORS = [
    'mean_daily_PET', 'temperature', 'mean_daily_precipitation',
    'number_of_precipitation_days', 'Area', 'Depth_available_for_roots',
    'drainage_density', 'Mean_terrain_slope', 'saturated hydraulic conductivity',
    'dwood_perc', 'ewood_perc', 'grass_perc', 'shrub_perc', 'urban_perc'
]
LABELS = [
    'Mean Daily PET', 'Temperature', 'Mean Daily Precipitation',
    'Number of Precipitation Days', 'Area', 'Depth Available for Roots',
    'Drainage Density', 'Mean Terrain Slope', 'Saturated Hydraulic Conductivity',
    'Deciduous Woodland %', 'Evergreen Woodland %', 'Grass %', 'Shrub %', 'Urban %'
]
SELECTED = {
    'IQR1': ['ewood_perc', 'saturated hydraulic conductivity'],
    'IQR2': ['mean_daily_PET', 'temperature', 'ewood_perc', 'shrub_perc',
             'mean_daily_precipitation', 'Mean_terrain_slope'],
    'IQR3': ['mean_daily_PET', 'temperature', 'mean_daily_precipitation',
             'Area', 'urban_perc', 'Mean_terrain_slope'],
}


def prepare(df):
    required = PREDICTORS + ['Re ID', 'IQR1', 'IQR2', 'IQR3']
    missing = sorted(set(required) - set(df.columns))
    if missing:
        raise ValueError(f'Missing workbook columns: {missing}')
    numeric = df[PREDICTORS + ['IQR1', 'IQR2', 'IQR3']].apply(pd.to_numeric, errors='raise')
    if not np.isfinite(numeric.to_numpy()).all() or df['Re ID'].isna().any():
        raise ValueError('Non-finite predictor/target values or missing Re ID')
    values = numeric[PREDICTORS].to_numpy(dtype=float)
    if (values < -1.00001).any() or (values > 1.00001).any():
        raise ValueError('Predictors expected to be already normalised to [-1, 1]')
    group = df['Re ID'].astype('category').cat.codes.to_numpy()
    return np.column_stack([values, group]), numeric


def fit_curves(X, y, bootstraps, seed):
    terms = reduce(add, [s(i) for i in range(14)]) + f(14)
    model = LinearGAM(terms).fit(X, y)
    grids = [model.generate_X_grid(term=i) for i in range(14)]
    point = [model.partial_dependence(term=i, X=grids[i]) for i in range(14)]
    rng = np.random.default_rng(seed)
    draws = [[] for _ in range(14)]
    for b in range(bootstraps):
        idx = rng.choice(len(y), size=len(y), replace=True)
        fitted = LinearGAM(terms).fit(X[idx], y[idx])
        for i in range(14):
            draws[i].append(fitted.partial_dependence(term=i, X=grids[i]))
        if (b + 1) % 10 == 0 or b + 1 == bootstraps:
            print(f'  bootstrap {b + 1}/{bootstraps}', flush=True)
    intervals = [(np.percentile(a, 2.5, axis=0), np.percentile(a, 97.5, axis=0)) for a in draws]
    return grids, point, intervals


def plot_selected(target, grids, point, intervals, out):
    variables = [v for v in PREDICTORS if v not in SELECTED[target]]
    n = len(variables)
    ncols = 3
    nrows = (n + ncols - 1) // ncols
    fig, axs = plt.subplots(nrows, ncols, figsize=(18, 4.8 * nrows))
    axs = np.atleast_1d(axs).flatten()
    indices = [PREDICTORS.index(v) for v in variables]
    lo = min(min(np.min(point[i]), np.min(intervals[i][0]), np.min(intervals[i][1])) for i in indices)
    hi = max(max(np.max(point[i]), np.max(intervals[i][0]), np.max(intervals[i][1])) for i in indices)
    low, high = (lo * 1.1 if lo < 0 else lo * 0.9), (hi * 1.1 if hi > 0 else hi * 0.9)
    if target == 'IQR2':
        low = -10
    if high <= low:
        high = low + 1
    for k, (ax, i) in enumerate(zip(axs, indices)):
        grid = grids[i]
        ax.plot(grid[:, i], point[i], color='blue', lw=1.8)
        ax.plot(grid[:, i], intervals[i][0], color='blue', ls='--', lw=1.2)
        ax.plot(grid[:, i], intervals[i][1], color='blue', ls='--', lw=1.2)
        ax.text(.03, .97, LABELS[i], transform=ax.transAxes, fontsize=15, va='top')
        ax.set_xlim(-1, 1)
        ax.set_ylim(low, high)
        ax.xaxis.set_major_locator(MultipleLocator(.25))
        ax.xaxis.set_major_formatter(FormatStrFormatter('%.2f'))
        ax.tick_params(direction='in', length=4, pad=6,
                       labelbottom=(k == 0), labelleft=(k == 0))
        if k == 0:
            ax.set_ylabel(f'Predicted {target} response', fontsize=14)
    for ax in axs[n:]:
        ax.axis("off")
    fig.tight_layout(rect=[0, .06, .96, .98])
    fig.text(.985, .025, {'IQR1':'a','IQR2':'b','IQR3':'c'}[target],
             fontsize=24, weight='bold', ha='right', va='bottom')
    fig.savefig(out, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f'Saved {out}')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input', type=Path, default=ROOT / 'data' / 'Catchments ID.xlsx')
    p.add_argument('--output-dir', type=Path, default=OUTPUT_DIR)
    p.add_argument('--bootstraps', type=int, default=100,
                   help='Published notebook uses 100; use 2 for a quick smoke test')
    p.add_argument('--seed', type=int, default=2026)
    p.add_argument('--target', choices=['IQR1','IQR2','IQR3','all'], default='all')
    args = p.parse_args()
    if args.bootstraps < 2:
        p.error('--bootstraps must be >= 2')
    df = pd.read_excel(args.input)
    X, numeric = prepare(df)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for target in (['IQR1','IQR2','IQR3'] if args.target == 'all' else [args.target]):
        print(f'Fitting {target}: {len(df)} catchments, {args.bootstraps} bootstraps', flush=True)
        grids, point, intervals = fit_curves(X, numeric[target].to_numpy(dtype=float),
                                             args.bootstraps, args.seed)
        plot_selected(target, grids, point, intervals,
                      args.output_dir / f'supplementary_figure_04_{target}.png')

if __name__ == '__main__':
    main()
