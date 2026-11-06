"""Supplementary Figure 5: seasonal GAM curves for variables omitted from Figure 3.

Source: original 250930draft8.ipynb, cells 9–10. Requires the original
seasonalanalysis2_normalized.xlsx workbook (not the annual Catchments ID.xlsx).
The Re ID factor follows the notebook's pyGAM specification.
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

def find_project_root():
    """Locate the repository from a script or a Jupyter working directory."""
    candidates = []
    if "__file__" in globals():
        candidates.append(Path(__file__).resolve().parent)
    candidates.append(Path.cwd())
    for start in candidates:
        for directory in (start, *start.parents):
            if (directory / "data" / "seasonalanalysis2_normalized.xlsx").is_file():
                return directory
    raise FileNotFoundError(
        "Cannot locate the project data folder. Run from the repository root "
        "or place this script inside its scripts/ directory."
    )


ROOT = find_project_root()
FEATURES = ['mean_daily_PET','temperature','mean_daily_precipitation',
 'number_of_precipitation_days','Area','Depth_available_for_roots',
 'drainage_density','Mean_terrain_slope','conductivity_hypres',
 'dwood_perc','ewood_perc','grass_perc','shrub_perc','urban_perc']
NAMES = ['Mean Daily PET','Temperature','Mean Daily Precipitation',
 'Number of Precipitation Days','Area','Depth Available for Roots',
 'Drainage Density','Mean Terrain Slope','Saturated Hydraulic Conductivity',
 'Deciduous Woodland %','Evergreen Woodland %','Grass %','Shrub %','Urban %']
SELECTED = {
 'IQR1':['mean_daily_PET','temperature','mean_daily_precipitation','Mean_terrain_slope','ewood_perc'],
 'IQR2':['temperature','mean_daily_precipitation','Mean_terrain_slope','conductivity_hypres','ewood_perc','grass_perc','shrub_perc'],
 'IQR3':['mean_daily_PET','temperature','mean_daily_precipitation','conductivity_hypres','ewood_perc','grass_perc']
}
TARGETS = {
 'IQR1':['IQR_runoffW','IQR_runoffP','IQR_runoffS','IQR_runoffA'],
 'IQR2':['IQR_runoff_ratioW','IQR_runoff_ratioP','IQR_runoff_ratioS','IQR_runoff_ratioA'],
 'IQR3':['IQRRR_MedianRRW','IQRRR_MedianRRP','IQRRR_MedianRRS','IQRRR_MedianRRA']
}
SEASONS = ['Winter','Spring','Summer','Autumn']
COLORS = ['blue','green','red','orange']

def run(data: Path, output: Path, target: str):
    df = pd.read_excel(data)
    # The source workbook may use a descriptive public conductivity column.
    if 'conductivity_hypres' not in df and 'saturated hydraulic conductivity' in df:
        df = df.rename(columns={'saturated hydraulic conductivity':'conductivity_hypres'})
    required = FEATURES + ['Re ID'] + TARGETS[target]
    missing = [c for c in required if c not in df]
    if missing:
        raise ValueError('Missing columns in seasonal workbook: '+', '.join(missing))
    # Exclude rows with missing/non-finite predictors or missing Re ID.
    # The original workbook may contain a few incomplete catchments.
    X_df = df[FEATURES].apply(pd.to_numeric, errors='coerce')
    re_id_valid = df['Re ID'].notna().to_numpy()
    predictors_valid = np.isfinite(X_df.to_numpy(dtype=float)).all(axis=1)
    common_valid = predictors_valid & re_id_valid
    print(f'{target}: {len(df)} original rows; '
          f'{int(common_valid.sum())} rows with valid predictors and Re ID; '
          f'{int((~common_valid).sum())} excluded', flush=True)
    if not common_valid.any():
        raise ValueError('No rows have finite predictors and a valid Re ID')
    df = df.loc[common_valid].copy()
    X = X_df.loc[common_valid].to_numpy(dtype=float)
    if X.min() < -1.00001 or X.max() > 1.00001:
        raise ValueError('Expected pre-normalized predictors in [-1, 1]')
    groups = df['Re ID'].astype('category').cat.codes.to_numpy()
    X = np.column_stack([X, groups])
    terms = reduce(add, [s(i) for i in range(14)]) + f(14)
    fits = {}
    for season, col in zip(SEASONS, TARGETS[target]):
        y = pd.to_numeric(df[col], errors='coerce').to_numpy(dtype=float)
        valid = np.isfinite(y)
        if valid.sum() < 50:
            raise ValueError(f'Insufficient valid data for {season}: {valid.sum()}')
        print(f'Fitting {target} {season}: {valid.sum()} catchments', flush=True)
        fits[season] = LinearGAM(terms).fit(X[valid], y[valid])
    variables = [v for v in FEATURES if v not in SELECTED[target]]
    ncols = 3
    nrows = (len(variables)+2)//3
    fig, axes = plt.subplots(nrows,ncols,figsize=(18,4.8*nrows))
    axes = np.atleast_1d(axes).ravel()
    curves = {}
    for var in variables:
        idx = FEATURES.index(var)
        curves[var] = []
        for season in SEASONS:
            gam = fits[season]
            grid = gam.generate_X_grid(term=idx)
            pdp = gam.partial_dependence(term=idx,X=grid)
            curves[var].append((grid[:,idx],pdp))
    lo = min(float(np.min(y)) for v in curves.values() for _,y in v)
    hi = max(float(np.max(y)) for v in curves.values() for _,y in v)
    pad = max((hi-lo)*0.04,1e-8)
    for k,var in enumerate(variables):
        ax=axes[k]
        for season,color,(x,y) in zip(SEASONS,COLORS,curves[var]):
            ax.plot(x,y,color=color,lw=1.8,label=season)
        ax.text(.03,.97,NAMES[FEATURES.index(var)],transform=ax.transAxes,va='top',fontsize=15)
        ax.set_xlim(-1,1)
        ax.set_ylim(lo-pad,hi+pad)
        ax.xaxis.set_major_locator(MultipleLocator(.25))
        ax.xaxis.set_major_formatter(FormatStrFormatter('%.2f'))
        ax.tick_params(direction='in',length=4,pad=6,labelbottom=(k==0),labelleft=(k==0))
        if k==0:
            ax.set_ylabel(f'Predicted {target} response',fontsize=14)
    for ax in axes[len(variables):]:
        ax.axis('off')
    handles,labels=axes[0].get_legend_handles_labels()
    if target=='IQR1':
        fig.legend(handles,labels,loc='lower right',bbox_to_anchor=(.90,.025),ncol=2,frameon=False)
    fig.tight_layout(rect=[0,.08,.96,.98])
    fig.text(.985,.02,{'IQR1':'a','IQR2':'b','IQR3':'c'}[target],
             fontsize=24,weight='bold',ha='right')
    output.mkdir(parents=True,exist_ok=True)
    dest=output/f'supplementary_figure_05_{target}.png'
    fig.savefig(dest,dpi=300,bbox_inches='tight')
    plt.close(fig)
    print(f'Saved {dest}',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--data',type=Path,default=ROOT/'data'/'seasonalanalysis2_normalized.xlsx')
    p.add_argument('--output',type=Path,default=ROOT/'figures')
    p.add_argument('--target',choices=['IQR1','IQR2','IQR3','all'],default='all')
    a=p.parse_args()
    if not a.data.exists():
        p.error(f'Seasonal workbook not found: {a.data}. Please supply seasonalanalysis2_normalized.xlsx')
    for t in (TARGETS if a.target=='all' else [a.target]):
        run(a.data,a.output,t)
