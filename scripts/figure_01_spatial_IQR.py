"""Reproduce Figure 1 of Xue et al. (2026) from published IQR data.

Requires catchment polygons and a GB outline, which are not included in this
repository. See geodata/README.md. The figure's plotting settings are adapted
from cell 6 of the author's supplied Jupyter notebook.
"""
from pathlib import Path
import argparse

import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.colors import Normalize
from matplotlib.gridspec import GridSpec
from matplotlib.ticker import MaxNLocator
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def make_figure(data_file: Path, basin_file: Path, boundary_file: Path, output_file: Path) -> None:
    for path in (data_file, basin_file, boundary_file):
        if not path.exists():
            raise FileNotFoundError(f"Missing input: {path}. See README.md and geodata/README.md")

    stations = pd.read_excel(data_file)
    required = {'station ID', 'IQR1', 'IQR2', 'IQR3'}
    missing = required.difference(stations.columns)
    if missing:
        raise ValueError(f"Missing Excel columns: {sorted(missing)}")
    if stations['station ID'].duplicated().any():
        raise ValueError("The station ID column must have unique values")

    basins = gpd.read_file(basin_file)
    boundary = gpd.read_file(boundary_file)
    if 'ID' not in basins.columns:
        raise ValueError("Basin polygons must have an 'ID' field matching Excel 'station ID'")
    if basins.crs is None or boundary.crs is None:
        raise ValueError("Both shapefiles must declare their coordinate reference systems")
    basins = basins.to_crs(epsg=27700)
    boundary = boundary.to_crs(epsg=27700)

    # Align station IDs without silently replacing missing values with zero.
    basin_ids = pd.to_numeric(basins['ID'], errors='coerce')
    station_ids = pd.to_numeric(stations['station ID'], errors='coerce')
    if basin_ids.isna().any() or station_ids.isna().any():
        raise ValueError("Station IDs must be numeric in both files")
    basins = basins.assign(_station_id=basin_ids)
    stations = stations.assign(_station_id=station_ids)
    mapped = basins.merge(stations[['_station_id', 'IQR1', 'IQR2', 'IQR3']], on='_station_id', how='left', validate='many_to_one')
    matched = mapped[['IQR1', 'IQR2', 'IQR3']].notna().all(axis=1).sum()
    print(f"Matched basin polygons: {matched} / {len(mapped)}")
    if matched == 0:
        raise ValueError("No matching basin IDs found. Check the polygon ID field.")

    plt.rcParams.update({'font.family': 'sans-serif', 'font.sans-serif': ['Arial', 'DejaVu Sans'], 'font.size': 11, 'axes.titlesize': 12})
    fig = plt.figure(figsize=(18, 11))
    gs = GridSpec(1, 3, figure=fig, wspace=0.03)
    fields = [('IQR1', '(m³/s)', 'a'), ('IQR2', '(%)', 'b'), ('IQR3', '(dimensionless)', 'c')]
    for i, (field, unit, label) in enumerate(fields):
        ax = fig.add_subplot(gs[i])
        values = mapped[field].dropna().to_numpy()
        if len(values) == 0:
            raise ValueError(f"No nonmissing values for {field}")
        vmin, vmax = np.nanpercentile(values, [1, 99])
        if np.isclose(vmin, vmax):
            vmax = vmin + 1e-6
        norm = Normalize(vmin=vmin, vmax=vmax)
        mapped.plot(ax=ax, column=field, cmap='viridis', norm=norm, edgecolor='none', linewidth=0, missing_kwds={'color': 'lightgrey'})
        boundary.plot(ax=ax, edgecolor='black', facecolor='none', linewidth=0.5)
        ax.text(0.02, 0.98, label, transform=ax.transAxes, fontsize=16, fontweight='bold', va='top')
        ax.set_axis_off()
        ax.set_aspect('equal')
        cax = inset_axes(ax, width='92%', height='3.5%', loc='lower center', borderpad=0.7)
        sm = cm.ScalarMappable(norm=norm, cmap='viridis')
        sm.set_array([])
        cbar = fig.colorbar(sm, cax=cax, orientation='horizontal')
        cbar.locator = MaxNLocator(nbins=4)
        cbar.update_ticks()
        cbar.set_label(unit, fontsize=13)
        cbar.ax.tick_params(labelsize=11, pad=2)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"Saved: {output_file}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate Figure 1: annual IQR maps')
    parser.add_argument('--data', type=Path, default=ROOT / 'data' / 'Catchments ID.xlsx')
    parser.add_argument('--basins', type=Path, default=ROOT / 'geodata' / 'merged_output.shp')
    parser.add_argument('--boundary', type=Path, default=ROOT / 'geodata' / 'infuse_gb_2011.shp')
    parser.add_argument('--output', type=Path, default=ROOT / 'figures' / 'figure_01_spatial_IQR.png')
    args = parser.parse_args()
    make_figure(args.data, args.basins, args.boundary, args.output)
