"""Auditable research pipeline. Run through personality.run_workbench for resource limits."""
import argparse
import hashlib
import json
import time
import platform
import sklearn
from pathlib import Path
import numpy as np
from sklearn.base import clone
from sklearn.calibration import calibration_curve
from sklearn.ensemble import ExtraTreesClassifier, GradientBoostingClassifier, StackingClassifier
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, precision_recall_curve, roc_curve, f1_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict, cross_val_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler, PolynomialFeatures
from .core import FEATURES, WINDOWS, Target
from .data import ROOT, DATA, digest, read_data
from .train import split_people, metrics, bootstrap

SEED = 20261110  # Preserve the previously disclosed partition; do not manufacture a new holdout.

def models():
    linear = make_pipeline(SimpleImputer(strategy='median', add_indicator=True), StandardScaler(), LogisticRegression(C=.3, max_iter=2000))
    interactions = make_pipeline(SimpleImputer(strategy='median'), StandardScaler(), PolynomialFeatures(2, interaction_only=True, include_bias=False), StandardScaler(), LogisticRegression(C=.1, max_iter=2000))
    trees = make_pipeline(SimpleImputer(strategy='median'), ExtraTreesClassifier(n_estimators=160, min_samples_leaf=12, max_features=.8, random_state=SEED, n_jobs=1))
    boost = make_pipeline(SimpleImputer(strategy='median'), GradientBoostingClassifier(n_estimators=100, learning_rate=.035, max_depth=2, min_samples_leaf=15, random_state=SEED))
    stack = StackingClassifier(estimators=[('linear',clone(linear)),('interactions',clone(interactions)),('trees',clone(trees)),('boost',clone(boost))], final_estimator=LogisticRegression(C=1,max_iter=2000), stack_method='predict_proba', passthrough=False, cv=StratifiedKFold(3,shuffle=True,random_state=SEED+3),n_jobs=1)
    return {'linear':linear,'interactions':interactions,'extra_trees':trees,'boosted_trees':boost,'stacked_ensemble':stack}

def target_matrix(frame, target):
    """Keep recency ordinal: categories are time intervals, never numeric doses."""
    recent=(frame[list(target.substances)].to_numpy() >= WINDOWS[target.window])
    return recent, (recent.sum(axis=1)>=target.minimum).astype(int)

def calibration_input(p):
    p=np.clip(np.asarray(p),1e-6,1-1e-6)
    return np.log(p/(1-p)).reshape(-1,1)

def run(config, output):
    start=time.monotonic()
    if output.exists(): raise ValueError('Output already exists; use a new run directory to preserve provenance.')
    target=Target(tuple(config['substances']),config['window'],config['minimum'])
    df=read_data()
    if digest(DATA)!=(ROOT/'config/data-sha256.txt').read_text().strip(): raise ValueError('Source checksum mismatch.')
    recent,y=target_matrix(df,target)
    if min(np.bincount(y,minlength=2))<40: raise ValueError('At least 40 observations per class required; do not manufacture minority cases.')
    X=df[FEATURES].to_numpy()
    tr,va,te=split_people(y,SEED)
    # Commit protocol before looking at any candidate scores.
    output.mkdir(parents=True)
    protocol={'schema_version':2,'versions':{'python':platform.python_version(),'numpy':np.__version__,'sklearn':sklearn.__version__},'seed':SEED,'target':target.to_dict(),'source_sha256':digest(DATA),'features':FEATURES,'selection':'training-only 5-fold AP; sigmoid calibration on training OOF predictions; validation F1 threshold; single selected-model test audit','test_status':'Previously exposed internal benchmark; NOT an untouched external test','candidates':list(models()),'folds':5,'stack_inner_folds':3,'max_threads':1,'gpu':False,'splits':{name:{'n':len(ix),'positives':int(y[ix].sum()),'id_hash':hashlib.sha256(','.join(map(str,df.id.iloc[ix])).encode()).hexdigest()} for name,ix in [('train',tr),('validation',va),('test',te)]}}
    (output/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
    cv=StratifiedKFold(5,shuffle=True,random_state=SEED)
    pool=models(); scores={}
    for name, model in pool.items():
        t=time.monotonic()
        folds=cross_val_score(model,X[tr],y[tr],cv=cv,scoring='average_precision',n_jobs=1)
        scores[name]={'mean':float(folds.mean()),'std':float(folds.std()),'folds':folds.tolist(),'seconds':round(time.monotonic()-t,3)}
        print(name,round(folds.mean(),4),flush=True)
    winner=max(scores,key=lambda name:scores[name]['mean'])
    model=pool[winner]
    oof=cross_val_predict(model,X[tr],y[tr],cv=cv,method='predict_proba',n_jobs=1)[:,1]
    calibrator=LogisticRegression(C=1e3,max_iter=2000).fit(calibration_input(oof),y[tr])
    if calibrator.coef_[0,0]<=0: raise ValueError('Calibration reversed ranking; stop and inspect training predictions.')
    model.fit(X[tr],y[tr])
    predict=lambda values:calibrator.predict_proba(calibration_input(model.predict_proba(values)[:,1]))[:,1]
    pv=predict(X[va]); thresholds=np.linspace(.01,.99,99)
    threshold=float(max(thresholds,key=lambda t:(f1_score(y[va],pv>=t,zero_division=0),t)))
    selection={'winner':winner,'threshold':threshold,'cv':scores,'calibration':{'slope':float(calibrator.coef_[0,0]),'intercept':float(calibrator.intercept_[0])}}
    (output/'selection.json').write_text(json.dumps(selection,indent=2)+'\n')
    pt=predict(X[te])
    precision,recall,_=precision_recall_curve(y[te],pt); fpr,tpr,_=roc_curve(y[te],pt)
    observed,mean_score=calibration_curve(y[te],pt,n_bins=5,strategy='quantile')
    # Explanations on validation only, with no subsequent model changes.
    importance=permutation_importance(model,X[va],y[va],scoring='average_precision',n_repeats=10,random_state=SEED,n_jobs=1)
    prevalence=float(y[tr].mean())
    report={'protocol':protocol,'selection':selection,'rows':len(y),'positives':int(y.sum()),'runtime_seconds':round(time.monotonic()-start,3),'test':metrics(y[te],pt,threshold),'test_ci95':bootstrap(y[te],pt,threshold),'baseline':metrics(y[te],np.full(len(te),prevalence),.5),'validation':metrics(y[va],pv,threshold),'curves':{'precision_recall':{'x':recall.tolist(),'y':precision.tolist()},'roc':{'x':fpr.tolist(),'y':tpr.tolist()},'reliability':{'x':mean_score.tolist(),'y':observed.tolist()}},'thresholds':[{'threshold':float(t),**metrics(y[va],pv,float(t))} for t in thresholds],'importance':[{'feature':f,'mean':float(m),'std':float(s)} for f,m,s in zip(FEATURES,importance.importances_mean,importance.importances_std)],'training_outcomes':{'substances':list(target.substances),'counts':np.bincount(recent[tr].sum(axis=1),minlength=len(target.substances)+1).tolist(),'cooccurrence':(recent[tr].astype(int).T@recent[tr].astype(int)).tolist()},'limitations':['Previously exposed UCI benchmark: no fresh generalization claim.','NEO-derived features do not accept IPIP questionnaire inputs.','Sigmoid calibration is estimated internally, not validated for an app population.','Co-occurrence within a month does not mean simultaneous consumption.','Importance measures predictive dependence, not causal influence.','Source quantification preceded our split; this cannot be undone.']}
    (output/'report.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    # Trusted local checkpoint only; never serve or auto-load user-supplied pickle files.
    import joblib
    joblib.dump({'model':model,'calibrator':calibrator,'features':FEATURES,'measurement':'uci_quantified_neo','ranges':np.column_stack([X[tr].min(axis=0),X[tr].max(axis=0)]).tolist(),'threshold':threshold,'protocol':protocol},output/'checkpoint.joblib')
    (output/'checkpoint.sha256').write_text(digest(output/'checkpoint.joblib')+'\n')
    print(json.dumps({'winner':winner,'AP':report['test']['average_precision'],'seconds':report['runtime_seconds']}),flush=True)
    return report

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--config',type=Path,default=ROOT/'config/target.json');p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    run(json.loads(a.config.read_text()),a.output)
if __name__=='__main__':main()
