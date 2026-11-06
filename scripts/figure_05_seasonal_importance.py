"""Figure 5: seasonal GAM PDP-range importance."""
import argparse
from pathlib import Path
import numpy as np,pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from common import ROOT,FEATURES,LABELS,fit,prepare
TARGETS={'IQR1':['IQR_runoffW','IQR_runoffP','IQR_runoffS','IQR_runoffA'],'IQR2':['IQR_runoff_ratioW','IQR_runoff_ratioP','IQR_runoff_ratioS','IQR_runoff_ratioA'],'IQR3':['IQRRR_MedianRRW','IQRRR_MedianRRP','IQRRR_MedianRRS','IQRRR_MedianRRA']}
SEASONS=['Winter','Spring','Summer','Autumn'];COLORS=['blue','green','red','gold']
def main():
 p=argparse.ArgumentParser();p.add_argument('--data',default=str(ROOT/'data'/'seasonalanalysis2_normalized.xlsx'));p.add_argument('--output',default=str(ROOT/'figures'));a=p.parse_args()
 df=pd.read_excel(a.data);df.columns=df.columns.str.strip()
 if 'conductivity_hypres' not in df and 'saturated hydraulic conductivity' in df:df['conductivity_hypres']=df['saturated hydraulic conductivity']
 out=Path(a.output);out.mkdir(exist_ok=True,parents=True)
 for k,(metric,ys) in enumerate(TARGETS.items()):
  vals=[]
  for target in ys:
   x,y,_=prepare(df,target);gam=fit(x,y)
   vals.append([float(np.ptp(gam.partial_dependence(term=j,X=gam.generate_X_grid(term=j)))) for j in range(14)])
  fig,ax=plt.subplots(figsize=(14,8));xx=np.arange(14);w=.2
  for i,(season,color) in enumerate(zip(SEASONS,COLORS)):ax.bar(xx+i*w,vals[i],width=w,label=season,color=color)
  ax.set_xticks(xx+1.5*w);ax.set_xticklabels(LABELS,rotation=45,ha='right',fontsize=11);ax.set_ylabel('Influence Strength',fontsize=13);ax.legend()
  fig.text(.98,.02,'abc'[k],fontsize=18,fontweight='bold',ha='right');fig.tight_layout();fig.savefig(out/f'figure_05_{metric}.png',dpi=300);plt.close(fig)
if __name__=='__main__':main()
