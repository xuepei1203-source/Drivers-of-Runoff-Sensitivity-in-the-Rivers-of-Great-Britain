"""Supplementary Figure 1: catchment/station locations and precipitation classes.

Run from the project root in Jupyter:
    %run scripts/supplementary_figure_01.py
"""
import argparse
from pathlib import Path

import geopandas as gpd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import matplotlib.patheffects as pe
import pandas as pd

try:
    from common import ROOT
except ImportError:
    ROOT = Path(__file__).resolve().parents[1]


def checked_file(path, label):
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"{label} not found: {path}")
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', default=str(ROOT / 'data' / 'Catchments ID.xlsx'))
    parser.add_argument('--stations', default=str(ROOT / 'data' / 'stations.xlsx'))
    parser.add_argument('--basins', default=str(ROOT / 'geodata' / 'merged_output.shp'))
    parser.add_argument('--boundary', default=str(ROOT / 'geodata' / 'infuse_gb_2011.shp'))
    parser.add_argument('--countries', default=str(ROOT / 'geodata' / 'CTRY_DEC_2022_UK_BUC.shp'))
    parser.add_argument('--output', default=str(ROOT / 'figures' / 'supplementary_figure_01.png'))
    args = parser.parse_args()

    data_path = checked_file(args.data, 'Catchment data')
    stations_path = checked_file(args.stations, 'Station precipitation data')
    basin_path = checked_file(args.basins, 'Catchment polygons')
    boundary_path = checked_file(args.boundary, 'GB boundary')
    countries_path = checked_file(args.countries, 'Country boundaries')

    df = pd.read_excel(data_path)
    stations = pd.read_excel(stations_path)
    required_df = {'station ID', 'gauge_lon', 'gauge_lat'}
    required_stations = {'station ID', 'precipitation'}
    if not required_df.issubset(df.columns):
        raise ValueError(f"Missing catchment columns: {sorted(required_df - set(df.columns))}")
    if not required_stations.issubset(stations.columns):
        raise ValueError(f"Missing station columns: {sorted(required_stations - set(stations.columns))}")

    # Preserve original precipitation tertile classification.
    stations = stations[['station ID', 'precipitation']].copy()
    stations['precipitation'] = pd.to_numeric(stations['precipitation'], errors='coerce')
    q33, q67 = stations['precipitation'].quantile([1/3, 2/3])
    if pd.isna(q33) or pd.isna(q67):
        raise ValueError('No valid precipitation values found in stations.xlsx')

    # Avoid suffixes if the catchment workbook also has a precipitation column.
    df = df.drop(columns=['precipitation'], errors='ignore')
    df = df.merge(stations, on='station ID', how='left', validate='many_to_one')
    df['gauge_lon'] = pd.to_numeric(df['gauge_lon'], errors='coerce')
    df['gauge_lat'] = pd.to_numeric(df['gauge_lat'], errors='coerce')
    df = df.dropna(subset=['gauge_lon', 'gauge_lat'])
    if df.empty:
        raise ValueError('No station coordinates available after cleaning')

    pts = gpd.GeoDataFrame(
        df, geometry=gpd.points_from_xy(df['gauge_lon'], df['gauge_lat']), crs='EPSG:4326'
    ).to_crs('EPSG:27700')
    basins = gpd.read_file(basin_path).to_crs('EPSG:27700').reset_index(drop=True)
    uk = gpd.read_file(boundary_path).to_crs('EPSG:27700')
    countries = gpd.read_file(countries_path).to_crs('EPSG:27700')

    basins['basin_id_tmp'] = basins.index
    joined = gpd.sjoin(
        pts[['precipitation', 'geometry']],
        basins[['basin_id_tmp', 'geometry']],
        how='left', predicate='within'
    )
    basin_precip = joined.groupby('basin_id_tmp')['precipitation'].mean()
    basins['precipitation'] = basins.index.map(basin_precip)

    def classify(value):
        if pd.isna(value):
            return None
        if value <= q33:
            return 'Drier catchments'
        if value >= q67:
            return 'Wetter catchments'
        return 'Moderate catchments'

    basins['rainfall_class'] = basins['precipitation'].map(classify)
    colors = {
        'Drier catchments': '#d9f0a3',
        'Moderate catchments': '#78c679',
        'Wetter catchments': '#238443',
    }
    fig, axes = plt.subplots(1, 2, figsize=(14, 14))

    dissolved = None
    if 'CTRY22NM' in countries.columns:
        countries['CountryName'] = countries['CTRY22NM'].map(
            lambda value: next(
                (name for name in ['England', 'Wales', 'Scotland']
                 if name.lower() in str(value).lower()), None
            )
        )
        countries = countries[countries['CountryName'].notna()]
        if not countries.empty:
            dissolved = countries.dissolve(by='CountryName')
    else:
        print('Note: CTRY22NM field not found; country labels omitted.')

    for ax in axes:
        uk.boundary.plot(ax=ax, color='black', linewidth=1.6, zorder=5)
        if dissolved is not None:
            dissolved.boundary.plot(ax=ax, color='black', linewidth=1.6, zorder=8)
            for name, geom in dissolved.geometry.items():
                point = geom.representative_point()
                ax.text(
                    point.x, point.y, name, fontsize=13, fontweight='bold',
                    ha='center', va='center',
                    path_effects=[pe.withStroke(linewidth=3, foreground='white')],
                    zorder=110
                )
        ax.axis('off')

    basins.plot(ax=axes[0], color='lightblue', edgecolor='black',
                linewidth=0.5, alpha=0.7, zorder=3)
    pts.plot(ax=axes[0], color='blue', markersize=10, zorder=90)
    uk.boundary.plot(ax=axes[0], color='black', linewidth=1.6, zorder=100)
    axes[0].legend(handles=[
        Patch(color='lightblue', label='Catchments'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='blue',
               label='Stations', markersize=8),
    ], loc='lower left', fontsize=10)
    axes[0].set_title('(a)', fontsize=14, fontweight='bold')

    basins.plot(ax=axes[1], color='white', edgecolor='lightgrey',
                linewidth=0.25, zorder=1)
    for label, color in colors.items():
        subset = basins[basins['rainfall_class'] == label]
        if not subset.empty:
            subset.plot(ax=axes[1], color=color, edgecolor='black',
                        linewidth=0.35, zorder=3)
    uk.boundary.plot(ax=axes[1], color='black', linewidth=1.6, zorder=100)
    axes[1].set_title('(b)', fontsize=14, fontweight='bold')
    axes[1].legend(handles=[
        Patch(color=colors['Drier catchments'], label=f'Drier (≤ {q33:.1f} mm)'),
        Patch(color=colors['Moderate catchments'], label=f'Moderate ({q33:.1f}–{q67:.1f} mm)'),
        Patch(color=colors['Wetter catchments'], label=f'Wetter (≥ {q67:.1f} mm)'),
    ], loc='lower right', fontsize=10)

    # Original 50 km scale bar and north arrow, in British National Grid coordinates.
    bounds = uk.total_bounds
    x, y = bounds[2] - 150000, bounds[1] + 40000
    axes[0].plot([x, x + 50000], [y, y], color='black', linewidth=3, zorder=120)
    axes[0].text(x + 25000, y - 15000, '50 km', ha='center', fontsize=10, zorder=120)
    nx, ny = bounds[0] + 100000, bounds[3] - 100000
    axes[0].annotate('', xy=(nx, ny), xytext=(nx, ny - 30000),
                     arrowprops=dict(facecolor='black', width=5, headwidth=15), zorder=120)
    axes[0].text(nx, ny + 10000, 'N', ha='center', fontweight='bold', zorder=120)

    out = Path(args.output)
    out.parent.mkdir(exist_ok=True, parents=True)
    fig.tight_layout()
    fig.savefig(out, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f'Saved: {out}')
    print(f'Precipitation terciles: {q33:.2f} mm, {q67:.2f} mm')
    print(f'Stations: {len(pts)}; catchments with precipitation: {basins.precipitation.notna().sum()}/{len(basins)}')


if __name__ == '__main__':
    main()
