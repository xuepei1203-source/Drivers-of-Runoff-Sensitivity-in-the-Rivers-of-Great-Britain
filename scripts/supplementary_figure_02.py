"""Supplementary Figure 2: original fifteen environmental-variable maps."""
import argparse
from pathlib import Path
import pandas as pd,geopandas as gpd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib import cm,gridspec
from common import ROOT
COLS=['mean_daily_PET','temperature','mean_daily_precipitation','number_of_precipitation_days','Area','Depth_available_for_roots','drainage_density','Mean_terrain_slope','conductivity_hypres','dwood_perc','ewood_perc','grass_perc','shrub_perc','crop_perc','urban_perc']
LABELS=['Mean Daily PET','Temperature','Mean Daily Precipitation','Number of Precipitation Days','Area','Depth Available for Roots','Drainage Density','Mean Terrain Slope','Saturated Hydraulic\nConductivity','Deciduous Woodland %','Evergreen Woodland %','Grass %','Shrub %','Crop %','Urban %']
def main():
 p=argparse.ArgumentParser();p.add_argument('--data',default=str(ROOT/'data'/'Catchments ID.xlsx'));p.add_argument('--basins',default=str(ROOT/'geodata'/'merged_output.shp'));p.add_argument('--boundary',default=str(ROOT/'geodata'/'infuse_gb_2011.shp'));p.add_argument('--output',default=str(ROOT/'figures'/'supplementary_figure_02.png'));a=p.parse_args()
 df=pd.read_excel(a.data);basins=gpd.read_file(a.basins).to_crs(27700);uk=gpd.read_file(a.boundary).to_crs(27700)
 if 'conductivity_hypres' not in df and 'saturated hydraulic conductivity' in df:df['conductivity_hypres']=df['saturated hydraulic conductivity']
 if 'station ID' not in df:raise KeyError('station ID required')
 basins['join_id']=basins['ID'].astype(str).str.replace(r'\.0$','',regex=True);df['join_id']=df['station ID'].astype(str).str.replace(r'\.0$','',regex=True)
 missing=[c for c in COLS if c not in df];
 if missing:raise KeyError(f'Missing columns: {missing}')
 merged=basins.merge(df[['join_id']+COLS],on='join_id',how='left')
 for c in COLS:merged[c]=pd.to_numeric(merged[c],errors='coerce').fillna(0)
 norm=Normalize(vmin=merged[COLS].min().min(),vmax=merged[COLS].max().max());fig=plt.figure(figsize=(20,22));gs=gridspec.GridSpec(3,5,figure=fig,wspace=0,hspace=.12)
 for i,(title,col) in enumerate(zip(LABELS,COLS)):
  ax=fig.add_subplot(gs[i]);merged.plot(ax=ax,column=col,cmap='viridis',edgecolor='black',linewidth=.2);uk.boundary.plot(ax=ax,edgecolor='black',linewidth=.2);ax.set_title(title,fontsize=20,y=1,pad=6);ax.axis('off');ax.margins(0)
 fig.subplots_adjust(left=0,right=1,top=.995,bottom=.07);cbax=fig.add_axes([.2,.015,.6,.02]);fig.colorbar(cm.ScalarMappable(norm=norm,cmap='viridis'),cax=cbax,orientation='horizontal').ax.tick_params(labelsize=20)
 out=Path(a.output);out.parent.mkdir(exist_ok=True,parents=True);fig.savefig(out,dpi=300,bbox_inches='tight',pad_inches=0);plt.close(fig)
if __name__=='__main__':main()
