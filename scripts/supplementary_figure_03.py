"""Supplementary Figure 3: independent and nested catchments."""
import argparse
from pathlib import Path
import pandas as pd,geopandas as gpd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib.colorbar import ColorbarBase
from matplotlib.patches import Patch
from common import ROOT
def main():
 p=argparse.ArgumentParser();p.add_argument('--data',default=str(ROOT/'data'/'Catchments ID.xlsx'));p.add_argument('--basins',default=str(ROOT/'geodata'/'merged_output.shp'));p.add_argument('--boundary',default=str(ROOT/'geodata'/'infuse_gb_2011.shp'));p.add_argument('--output',default=str(ROOT/'figures'/'supplementary_figure_03.png'));a=p.parse_args()
 df=pd.read_excel(a.data);basins=gpd.read_file(a.basins).to_crs(27700);uk=gpd.read_file(a.boundary).to_crs(27700)
 basins['join_id']=basins['ID'].astype(str).str.replace(r'\.0$','',regex=True);df['join_id']=df['station ID'].astype(str).str.replace(r'\.0$','',regex=True)
 merged=basins.merge(df[['join_id','Re ID']],on='join_id',how='left');merged['Re ID']=pd.to_numeric(merged['Re ID'],errors='coerce').fillna(0)
 fig,ax=plt.subplots(figsize=(10,10));norm=Normalize(vmin=1,vmax=77);merged[merged['Re ID']>0].plot(ax=ax,column='Re ID',cmap='viridis',norm=norm,edgecolor='black',linewidth=.2);merged[merged['Re ID']==0].plot(ax=ax,color='#e41a1c',edgecolor='black',linewidth=.2);uk.boundary.plot(ax=ax,edgecolor='black',linewidth=.8);ax.axis('off')
 cbax=fig.add_axes([.2,.08,.6,.02]);cb=ColorbarBase(cbax,cmap=plt.get_cmap('viridis'),norm=norm,orientation='horizontal');cb.set_ticks([1,77]);cb.set_label('Nested catchments');fig.legend(handles=[Patch(facecolor='#e41a1c',edgecolor='black',label='Independent catchments')],loc='lower left',bbox_to_anchor=(.2,.12),bbox_transform=fig.transFigure,fontsize=12,frameon=False)
 out=Path(a.output);out.parent.mkdir(exist_ok=True,parents=True);fig.savefig(out,dpi=300,bbox_inches='tight');plt.close(fig)
if __name__=='__main__':main()
