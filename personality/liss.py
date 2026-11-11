"""Metadata-derived adapter, verified on fixtures only. Does not acquire restricted data."""
import numpy as np
import pandas as pd

SUBSTANCES={'cannabis':('ap08a130','ap08a142'),'ecstasy':('ap08a131','ap08a143'),'cocaine':('ap08a132','ap08a144'),'heroin':('ap08a133','ap08a145')}
ITEMS=[f'cp08a{i:03}' for i in range(20,70)]

def recent_use(ever, frequency):
    """False for explicit never-use or explicit no recent use; missing stays unknown."""
    if pd.isna(ever):
        if not pd.isna(frequency): raise ValueError('Recent-use answer without lifetime routing answer.')
        return np.nan
    if ever not in (1,2): raise ValueError('Lifetime code must be 1/2 or missing.')
    if not pd.isna(frequency) and frequency not in (1,2,3,4,5):raise ValueError('Recent-use code must be 1..5 or missing.')
    if ever==2:
        if not pd.isna(frequency) and frequency!=5:raise ValueError('Contradictory never-use and recent-use answers.')
        return 0.
    return np.nan if pd.isna(frequency) else float(frequency<=4)

def count_target(values, minimum=2):
    """Resolve labels only when known lower/upper bounds establish the answer."""
    x=np.asarray(values,dtype=float)
    if x.ndim!=2 or minimum<1 or minimum>x.shape[1]:raise ValueError('Invalid target dimensions/minimum.')
    if not np.all(np.isnan(x)|(x==0)|(x==1)):raise ValueError('Expected binary or missing outcome indicators.')
    lower=np.nansum(x,axis=1);upper=lower+np.isnan(x).sum(axis=1)
    return np.where(lower>=minimum,1.,np.where(upper<minimum,0.,np.nan))

def prepare(personality, substances, selected=tuple(SUBSTANCES), minimum=2):
    if not selected or len(set(selected))!=len(selected) or not set(selected)<=set(SUBSTANCES):raise ValueError('Unknown or repeated substances.')
    for frame in (personality,substances):
        if frame.nomem_encr.isna().any() or frame.nomem_encr.duplicated().any():raise ValueError('Participant IDs must be present and unique.')
    cols=[c for name in selected for c in SUBSTANCES[name]]
    merged=personality[['nomem_encr',*ITEMS]].merge(substances[['nomem_encr',*cols]],on='nomem_encr',how='inner',validate='one_to_one')
    X=merged[ITEMS].apply(pd.to_numeric,errors='raise')
    if not ((X>=1)&(X<=5)|X.isna()).all().all():raise ValueError('IPIP responses must be 1..5 or missing.')
    outcomes=np.array([[recent_use(row[a],row[b]) for a,b in (SUBSTANCES[s] for s in selected)] for _,row in merged.iterrows()],dtype=float).reshape(len(merged),len(selected))
    y=count_target(outcomes,minimum)
    # Caller must retain IDs for participant/household isolation, never as model features.
    return merged.nomem_encr.to_numpy(),X,y,{'matched':len(merged),'unknown_target':int(np.isnan(y).sum()),'all_items_missing':int(X.isna().all(axis=1).sum()),'status':'Adapter only; real LISS data and release permission not verified.'}
