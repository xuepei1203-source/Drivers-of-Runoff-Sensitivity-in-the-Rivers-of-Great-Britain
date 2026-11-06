from pathlib import Path
import numpy as np
import pandas as pd
from pygam import LinearGAM,s,f
from functools import reduce
from operator import add
ROOT=Path(__file__).resolve().parents[1]
FEATURES=['mean_daily_PET','temperature','dwood_perc','ewood_perc','shrub_perc','drainage_density','Depth_available_for_roots','mean_daily_precipitation','Area','number_of_precipitation_days','grass_perc','urban_perc','Mean_terrain_slope','conductivity_hypres']
LABELS=['Mean Daily PET','Temperature','Deciduous Woodland %','Evergreen Woodland %','Shrub %','Drainage Density','Depth Available for Roots','Mean Daily Precipitation','Area','Number of Precipitation Days','Grass %','Urban %','Mean Terrain Slope','Saturated Hydraulic Conductivity']
TARGETS={'IQR1':'IQR_runoff','IQR2':'IQR_runoff_ratio','IQR3':'IQRRR_MedianRR'}
def load_annual(path):
 df=pd.read_excel(path);df.columns=df.columns.str.strip()
 aliases={'IQR_runoff':'IQR1','IQR_runoff_ratio':'IQR2','IQRRR_MedianRR':'IQR3','conductivity_hypres':'saturated hydraulic conductivity'}
 for dest,src in aliases.items():
  if dest not in df and src in df:df[dest]=df[src]
 return df
def prepare(df,target):
 required=FEATURES+['Re ID',target]
 missing=[x for x in required if x not in df]
 if missing:raise ValueError(f'Missing columns: {missing}')
 valid=df['Re ID'].notna().to_numpy()
 x=df[FEATURES].apply(pd.to_numeric,errors='coerce').to_numpy(float)
 y=pd.to_numeric(df[target],errors='coerce').to_numpy(float)
 valid &= np.isfinite(x).all(axis=1)&np.isfinite(y)
 codes=pd.Categorical(df.loc[valid,'Re ID']).codes.astype(float)
 return np.column_stack((x[valid],codes)),y[valid],valid
def fit(x,y):
 return LinearGAM(reduce(add,[s(i) for i in range(14)])+f(14)).fit(x,y)
