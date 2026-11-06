"""Supplementary Figure 7: static-covariate P10 to P90 GAM predictions."""
import argparse
from pathlib import Path
import numpy as np
from common import ROOT,FEATURES,TARGETS,load_annual,prepare,fit
STATIC=['Area','drainage_density','Depth_available_for_roots','Mean_terrain_slope','conductivity_hypres']
def main():
 p=argparse.ArgumentParser();p.add_argument('--data',default=str(ROOT/'data'/'Catchments ID.xlsx'));p.add_argument('--output',default=str(ROOT/'results'/'static_P10_P90_deltas.xlsx'));a=p.parse_args()
 df=load_annual(a.data);res=df.copy()
 for metric,target in TARGETS.items():
  x,y,valid=prepare(df,target);gam=fit(x,y);base=gam.predict(x);full=np.full(len(df),np.nan);full[valid]=base;res[f'base_prediction_{metric}']=full
  for var in STATIC:
   j=FEATURES.index(var);p10,p90=np.quantile(x[:,j],[.1,.9]);x10=x.copy();x90=x.copy();x10[:,j]=p10;x90[:,j]=p90
   a10=gam.predict(x10);a90=gam.predict(x90)
   res[f'{var}_P10_value_{metric}']=p10;res[f'{var}_P90_value_{metric}']=p90
   for name,values in [('prediction_P10',a10),('prediction_P90',a90),('P90_minus_P10',a90-a10),('P10_minus_base',a10-base),('P90_minus_base',a90-base)]:
    arr=np.full(len(df),np.nan);arr[valid]=values;res[f'{var}_{name}_{metric}']=arr
 out=Path(a.output);out.parent.mkdir(exist_ok=True,parents=True);res.to_excel(out,index=False);print('Saved',out)
if __name__=='__main__':main()
