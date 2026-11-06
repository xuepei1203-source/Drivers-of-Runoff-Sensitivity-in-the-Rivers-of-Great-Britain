"""Figure 6 (+10%) and Supplementary Figure 6 (+20%), 14 variables each."""
import argparse
from pathlib import Path
import numpy as np,pandas as pd,geopandas as gpd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
from matplotlib import cm,gridspec
from common import ROOT
VARS=['mean_daily_PET','temperature','mean_daily_precipitation','number_of_precipitation_days','Area','Depth_available_for_roots','drainage_density','Mean_terrain_slope','conductivity_hypres','dwood_perc','ewood_perc','grass_perc','shrub_perc','urban_perc']
LABELS=['Mean Daily PET','Temperature','Mean Daily Precipitation','Number of Precipitation Days','Area','Depth Available for Roots','Drainage Density','Mean Terrain Slope','Saturated Hydraulic\nConductivity','Deciduous Woodland %','Evergreen Woodland %','Grass %','Shrub %','Urban %']
def clean_id(s):
    """Normalize station identifiers without changing their substantive values."""
    if isinstance(s, pd.DataFrame):
        raise ValueError("Station ID selection returned multiple columns; check duplicate column names")
    return s.astype('string').str.strip().str.replace(r'\.0$', '', regex=True)


def load_perturbations(path, pct):
    df = pd.read_excel(path)
    df.columns = df.columns.astype(str).str.strip().str.replace(' ', '_', regex=False)

    # Both 'station ID' and 'station_ID' may be present in the source Excel.
    # Check the duplicated values before retaining one column.
    duplicate_names = df.columns[df.columns.duplicated()].unique().tolist()
    for name in duplicate_names:
        block = df.loc[:, df.columns == name]
        baseline = block.iloc[:, 0]
        for j in range(1, block.shape[1]):
            candidate = block.iloc[:, j]
            if name.lower() == 'station_id':
                equal = clean_id(baseline).fillna('<missing>').equals(
                    clean_id(candidate).fillna('<missing>'))
            else:
                equal = baseline.equals(candidate)
            if not equal:
                raise ValueError(
                    f"{path.name}: duplicate normalized column {name!r} "
                    "has conflicting values. Please inspect the Excel workbook.")
    if duplicate_names:
        print(f"{path.name}: identical duplicate columns removed: {duplicate_names}", flush=True)
        df = df.loc[:, ~df.columns.duplicated()].copy()

    id_candidates = [c for c in df.columns if c.lower() == 'station_id']
    if not id_candidates:
        raise KeyError(f"{path.name}: station ID field not found")
    df['Station_ID'] = clean_id(df[id_candidates[0]])
    if df['Station_ID'].isna().any() or df['Station_ID'].eq('').any():
        raise ValueError(f"{path.name}: some station IDs are missing")
    if df['Station_ID'].duplicated().any():
        raise ValueError(f"{path.name}: duplicate station IDs; merging would duplicate polygons")
    print(f"Loaded {path.name}: {len(df)} stations", flush=True)
    return df


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--basins', default=str(ROOT/'geodata'/'merged_output.shp'))
    p.add_argument('--boundary', default=str(ROOT/'geodata'/'infuse_gb_2011.shp'))
    p.add_argument('--results', default=str(ROOT/'results'))
    p.add_argument('--output', default=str(ROOT/'figures'))
    a = p.parse_args()
    out = Path(a.output)
    out.mkdir(exist_ok=True, parents=True)
    uk = gpd.read_file(a.boundary).to_crs(27700)
    basins = gpd.read_file(a.basins).to_crs(27700)
    basins.columns = basins.columns.astype(str).str.strip().str.replace(' ', '_', regex=False)
    basins = basins[basins['ID'].notna()].copy()
    basins['Station_ID'] = clean_id(basins['ID'])
    frames = {}
    for pct in (10, 20):
        frames[pct] = load_perturbations(Path(a.results)/f'{pct}_deltas.xlsx', pct)
        matched = basins['Station_ID'].isin(frames[pct]['Station_ID']).sum()
        print(f'{pct}%: matched {matched}/{len(basins)} basin polygons', flush=True)
        if matched == 0:
            raise ValueError(f'{pct}%: no station IDs match the basin shapefile')
    for idx,metric in enumerate(('IQR1','IQR2','IQR3')):
        cols={pct:[f'{v}_delta_{pct}pct_{metric}' for v in VARS] for pct in (10,20)}
        for pct in (10,20):
            missing=set(cols[pct])-set(frames[pct].columns)
            if missing:raise KeyError(f'Missing {pct}% {metric} columns: {sorted(missing)}')
        values=pd.concat([pd.to_numeric(frames[pct][c],errors='coerce') for pct in (10,20) for c in cols[pct]],ignore_index=True).replace([np.inf,-np.inf],np.nan).dropna()
        lo,hi=values.quantile([.02,.98]);norm=TwoSlopeNorm(vmin=min(float(lo),-1e-12),vcenter=0,vmax=max(float(hi),1e-12));cmap=plt.get_cmap('RdBu_r');sm=cm.ScalarMappable(norm=norm,cmap=cmap)
        for pct in (10,20):
            merged=basins.merge(frames[pct],on='Station_ID',how='left');fig=plt.figure(figsize=(20,22));gs=gridspec.GridSpec(3,5,figure=fig,wspace=0,hspace=.12)
            for j,(label,var) in enumerate(zip(LABELS,VARS)):
                ax=fig.add_subplot(gs[j]);merged.plot(ax=ax,column=f'{var}_delta_{pct}pct_{metric}',cmap=cmap,norm=norm,edgecolor='black',linewidth=.2,missing_kwds={'color':'lightgrey'});uk.boundary.plot(ax=ax,edgecolor='black',linewidth=.2);ax.set_title(label,fontsize=20,pad=6);ax.axis('off');ax.margins(0)
            fig.add_subplot(gs[14]).axis('off');fig.text(.9,.05,'abc'[idx],fontsize=24,weight='bold');fig.subplots_adjust(left=0,right=1,top=.995,bottom=.07);cbax=fig.add_axes([.2,.015,.6,.02]);cb=fig.colorbar(sm,cax=cbax,orientation='horizontal');cb.ax.tick_params(labelsize=20);cb.set_label('Δ'+metric,fontsize=20)
            name=('figure_06' if pct==10 else 'supplementary_figure_06')+f'_{metric}.png';fig.savefig(out/name,dpi=300,bbox_inches='tight',pad_inches=0);plt.close(fig);print('Saved',out/name)
if __name__=='__main__':main()
