"""Figure 6: all fourteen predictors perturbed by 10% or 20% with clipping."""
import argparse
from pathlib import Path
import numpy as np,pandas as pd
from common import ROOT,FEATURES,TARGETS,load_annual,prepare,fit
def main():
 p=argparse.ArgumentParser();p.add_argument('--data',default=str(ROOT/'data'/'Catchments ID.xlsx'));p.add_argument('--output',default=str(ROOT/'results'));a=p.parse_args()
 if not Path(a.data).is_file():
  raise FileNotFoundError(f'Annual input workbook not found: {a.data}')
 df=load_annual(a.data);out=Path(a.output);out.mkdir(parents=True,exist_ok=True)
 print(f'Input: {a.data}; rows: {len(df)}; predictors: {len(FEATURES)}',flush=True)
 for pct in (10,20):
  result=df.copy();diagnostics=[]
  for metric,target in TARGETS.items():
   x,y,valid=prepare(df,target);gam=fit(x,y);base=gam.predict(x)
   for j,var in enumerate(FEATURES):
    low,high=np.nanmin(x[:,j]),np.nanmax(x[:,j]);before=x[:,j]*(1+pct/100);after=np.clip(before,low,high)
    xp=x.copy();xp[:,j]=after;delta=gam.predict(xp)-base;full=np.full(len(df),np.nan);full[valid]=delta
    result[f'{var}_delta_{pct}pct_{metric}']=full
    diagnostics.append({'target':metric,'variable':var,'perturbation':f'+{pct}%','original_min':low,'original_max':high,'before_clip_min':before.min(),'before_clip_max':before.max(),'after_clip_min':after.min(),'after_clip_max':after.max(),'n_exceed_before_clip':int(((before<low)|(before>high)).sum()),'n_exceed_after_clip':int(((after<low)|(after>high)).sum())})
  if 'station ID' in result:result['station_ID']=result['station ID']
  result.to_excel(out/f'{pct}_deltas.xlsx',index=False);pd.DataFrame(diagnostics).to_excel(out/f'{pct}_deltas_clipping_diagnostics.xlsx',index=False)
  print('Saved',out/f'{pct}_deltas.xlsx')
if __name__=='__main__':main()
