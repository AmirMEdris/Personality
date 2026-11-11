"""Infer with a checkpoint you trained locally. Never load an untrusted checkpoint."""
import argparse
import json
from pathlib import Path
import numpy as np
from .data import digest
from .workbench import calibration_input

def predict(directory, payload):
    import joblib
    path=directory/'checkpoint.joblib'
    if digest(path)!=(directory/'checkpoint.sha256').read_text().strip():raise ValueError('Checkpoint integrity mismatch.')
    if payload.get('measurement')!='uci_quantified_neo':raise ValueError('Requires original UCI quantified NEO features, not IPIP answers.')
    bundle=joblib.load(path)
    values=payload['features']
    if set(values)!=set(bundle['features']):raise ValueError('Feature names must match exactly.')
    x=np.array([[values[f] for f in bundle['features']]],dtype=float)
    if not np.isfinite(x).all():raise ValueError('Finite feature values required.')
    bounds=np.asarray(bundle['ranges'])
    if ((x[0]<bounds[:,0])|(x[0]>bounds[:,1])).any():raise ValueError('Outside training feature range; abstaining.')
    raw=bundle['model'].predict_proba(x)[:,1]
    score=float(bundle['calibrator'].predict_proba(calibration_input(raw))[0,1])
    return {'score':score,'threshold':bundle['threshold'],'match':score>=bundle['threshold'],'meaning':'Historical survey model score; not a validated personal probability.'}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=Path,required=True);p.add_argument('--input',type=Path,required=True);a=p.parse_args()
    print(json.dumps(predict(a.run,json.loads(a.input.read_text())),indent=2))
if __name__=='__main__':main()
