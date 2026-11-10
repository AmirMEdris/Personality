"""Download only the public UCI data; never load legacy pickles."""
import argparse, hashlib, io, json, pathlib, urllib.request, zipfile
import numpy as np
import pandas as pd
from .core import DRUGS, FEATURES

URL = 'https://archive.ics.uci.edu/static/public/373/drug+consumption+quantified.zip'
COLUMNS = ['id','age','gender','education','country','ethnicity',*FEATURES,*list(DRUGS)[:17],'semeron','vsa']
ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT/'data'/'drug_consumption.data'

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read_data(path=DATA):
    frame = pd.read_csv(path, header=None)
    if frame.shape[1] != 32:
        raise ValueError('Expected 32 UCI columns, including respondent ID.')
    frame.columns = COLUMNS
    if frame.isna().any().any() or frame.id.duplicated().any():
        raise ValueError('Missing data or duplicate respondent IDs.')
    for column in [*DRUGS,'semeron']:
        if not frame[column].astype(str).str.fullmatch(r'CL[0-6]').all():
            raise ValueError(f'Invalid recency in {column}.')
        frame[column] = frame[column].str[2].astype(int)
    if not np.isfinite(frame[['id','age','gender','education','country','ethnicity',*FEATURES]].to_numpy(dtype=float)).all():
        raise ValueError('Invalid numeric feature.')
    return frame.sort_values('id').reset_index(drop=True)

def download():
    DATA.parent.mkdir(parents=True,exist_ok=True)
    if DATA.exists():
        read_data()
        print(f'Using existing dataset: {digest(DATA)}')
        return
    with urllib.request.urlopen(URL,timeout=45) as response:
        archive = response.read(2_000_000)
    with zipfile.ZipFile(io.BytesIO(archive)) as z:
        entries = [n for n in z.namelist() if pathlib.PurePosixPath(n).name=='drug_consumption.data']
        if len(entries)!=1:
            raise ValueError('Expected one drug_consumption.data file.')
        content=z.read(entries[0])
    temporary=DATA.with_suffix('.tmp')
    temporary.write_bytes(content)
    try:
        frame=read_data(temporary)
        if len(frame)!=1885:
            raise ValueError('Unexpected respondent count; review source change.')
        expected_path=ROOT/'config'/'data-sha256.txt'
        expected=expected_path.read_text().strip() if expected_path.exists() else None
        if expected and digest(temporary)!=expected:
            raise ValueError('Dataset checksum changed. Review source before training.')
        temporary.replace(DATA)
    finally:
        temporary.unlink(missing_ok=True)
    (DATA.parent/'source.json').write_text(json.dumps({'url':URL,'sha256':digest(DATA),'rows':len(frame),'license':'CC BY 4.0','citation':'Fehrman, E., Egan, V., & Mirkes, E. (2015). Drug Consumption (Quantified). DOI: 10.24432/C5TC7S'},indent=2))
    print(f'Downloaded {len(frame)} respondents; SHA256 {digest(DATA)}')

if __name__=='__main__':
    argparse.ArgumentParser(description=__doc__).parse_args()
    download()
