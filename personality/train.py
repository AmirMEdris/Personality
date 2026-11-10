"""Reproducible model tournament: training CV, validation threshold, held-out audit."""
import argparse, hashlib, json, platform
from pathlib import Path
import numpy as np
import sklearn
from sklearn.base import clone
from sklearn.calibration import calibration_curve
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score, brier_score_loss, precision_score, recall_score, f1_score, balanced_accuracy_score, accuracy_score, confusion_matrix
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from .core import Target, FEATURES, WINDOWS, infer, MEASUREMENT
from .data import read_data, digest, DATA, ROOT

SEED=20261110

def split_people(y, seed=SEED):
    indices=np.arange(len(y))
    train, other=train_test_split(indices,test_size=.4,stratify=y,random_state=seed)
    validation,test=train_test_split(other,test_size=.5,stratify=np.asarray(y)[other],random_state=seed+1)
    return train,validation,test

def candidates(seed=SEED):
    plain=make_pipeline(StandardScaler(),LogisticRegression(C=1,max_iter=2000,random_state=seed))
    balanced=make_pipeline(StandardScaler(),LogisticRegression(C=1,class_weight='balanced',max_iter=2000,random_state=seed))
    forest=RandomForestClassifier(n_estimators=200,max_depth=6,min_samples_leaf=8,class_weight='balanced_subsample',random_state=seed,n_jobs=1)
    boosting=GradientBoostingClassifier(n_estimators=120,learning_rate=.04,max_depth=2,min_samples_leaf=12,subsample=.85,random_state=seed)
    vote=VotingClassifier([('linear',clone(plain)),('forest',clone(forest)),('boosting',clone(boosting))],voting='soft')
    return {'logistic':plain,'balanced_logistic':balanced,'random_forest':forest,'gradient_boosting':boosting,'soft_voting_ensemble':vote}

def metrics(y,p,threshold):
    pred=np.asarray(p)>=threshold
    return {'average_precision':float(average_precision_score(y,p)), 'roc_auc':float(roc_auc_score(y,p)), 'brier':float(brier_score_loss(y,p)), 'precision':float(precision_score(y,pred,zero_division=0)), 'recall':float(recall_score(y,pred,zero_division=0)), 'f1':float(f1_score(y,pred,zero_division=0)), 'balanced_accuracy':float(balanced_accuracy_score(y,pred)), 'accuracy':float(accuracy_score(y,pred)), 'confusion_matrix':confusion_matrix(y,pred,labels=[0,1]).tolist()}

def bootstrap(y,p,threshold,seed=SEED,repeats=300):
    rng=np.random.default_rng(seed); rows=[]
    for _ in range(repeats):
        ix=rng.integers(0,len(y),len(y)); yy=np.asarray(y)[ix]
        if len(np.unique(yy))<2: continue
        rows.append(metrics(yy,np.asarray(p)[ix],threshold))
    return {k:[float(x) for x in np.quantile([r[k] for r in rows],[.025,.975])] for k in ['average_precision','recall','precision','f1','brier']}

def tree_json(tree, classification=False):
    t=tree.tree_
    values=t.value[:,0,:]
    if classification:
        values=values[:,1]/values.sum(axis=1)
    else: values=values[:,0]
    return {'left':t.children_left.tolist(),'right':t.children_right.tolist(),'feature':t.feature.tolist(),'threshold':t.threshold.tolist(),'value':values.tolist()}

def export(est):
    if hasattr(est,'named_steps'):
        scaler,logistic=est.steps[0][1],est.steps[1][1]
        return {'kind':'logistic','means':scaler.mean_.tolist(),'scales':scaler.scale_.tolist(),'coefficients':logistic.coef_[0].tolist(),'intercept':float(logistic.intercept_[0])}
    if isinstance(est,RandomForestClassifier):
        return {'kind':'forest','trees':[tree_json(t,True) for t in est.estimators_]}
    if isinstance(est,GradientBoostingClassifier):
        prior=est.init_.class_prior_[1]
        return {'kind':'boosting','initial':float(np.log(prior/(1-prior))),'rate':est.learning_rate,'trees':[tree_json(t[0]) for t in est.estimators_]}
    return {'kind':'ensemble','members':[export(e) for e in est.estimators_]}

def train(config,output):
    target=Target(tuple(config['substances']),config['window'],config['minimum'])
    df=read_data()
    expected=(ROOT/'config'/'data-sha256.txt').read_text().strip()
    if digest(DATA)!=expected: raise ValueError('Dataset differs from the pinned checksum.')
    X=df[FEATURES].to_numpy(); y=((df[list(target.substances)]>=WINDOWS[target.window]).sum(axis=1)>=target.minimum).astype(int).to_numpy()
    if min(np.bincount(y,minlength=2))<30: raise ValueError('Target needs at least 30 people in each class for this evaluation protocol.')
    tr,va,te=split_people(y)
    cv=StratifiedKFold(n_splits=5,shuffle=True,random_state=SEED)
    models=candidates(); scores={}
    for name,est in models.items():
        values=cross_val_score(est,X[tr],y[tr],cv=cv,scoring='average_precision',n_jobs=1)
        scores[name]={'mean':float(values.mean()),'std':float(values.std()),'folds':values.tolist()}
        print(f'{name}: training CV average precision {values.mean():.4f}',flush=True)
    winner=max(scores,key=lambda n:scores[n]['mean'])
    # Selection uses training data only. Validation chooses one operating threshold.
    selected=models[winner].fit(X[tr],y[tr])
    pv=selected.predict_proba(X[va])[:,1]
    grid=np.linspace(.02,.98,97)
    threshold=float(max(grid,key=lambda t:(f1_score(y[va],pv>=t,zero_division=0),t)))
    pt=selected.predict_proba(X[te])[:,1]
    report={'schema_version':1,'seed':SEED,'data_sha256':digest(DATA),'versions':{'python':platform.python_version(),'numpy':np.__version__,'sklearn':sklearn.__version__},'target':target.to_dict(),'features':FEATURES,'rows':len(df),'positive_count':int(y.sum()),'prevalence':float(y.mean()),'splits':{name:{'count':len(ix),'positive_count':int(y[ix].sum()),'ids_sha256':hashlib.sha256(','.join(map(str,df.id.iloc[ix])).encode()).hexdigest()} for name,ix in [('train',tr),('validation',va),('test',te)]},'cv_average_precision':scores,'selected':winner,'threshold':threshold,'selection_rule':'Highest mean training-only 5-fold average precision; highest validation F1 threshold, ties favor higher threshold. No test-driven selection.','validation':metrics(y[va],pv,threshold),'test':metrics(y[te],pt,threshold),'test_ci95':bootstrap(y[te],pt,threshold),'test_baselines':{'always_negative':metrics(y[te],np.zeros(len(te)),.5),'training_prevalence':metrics(y[te],np.full(len(te),y[tr].mean()),.5)},'limitations':['Cross-sectional self-report sample; no future-risk or clinical validation.','Small positive class: bootstrap intervals reflect test-sample uncertainty, not model-selection uncertainty.','Dataset features were quantified by its authors before release; fold-local scaling does not undo that source preprocessing.','Repeated target exploration makes this an internal benchmark, not a pristine external validation.','No validated IPIP-to-NEO mapping. No individual questionnaire inference.','Class weighting may affect probability calibration; scores are not calibrated population probabilities.']}
    fractions,means=calibration_curve(y[te],pt,n_bins=5,strategy='quantile')
    report['reliability']={'mean_score':means.tolist(),'observed_fraction':fractions.tolist()}
    # Audit all predeclared candidates at 0.5 without changing the selected model.
    report['candidate_test_audit']={}
    for name,est in models.items():
        if name!=winner: est.fit(X[tr],y[tr])
        report['candidate_test_audit'][name]=metrics(y[te],est.predict_proba(X[te])[:,1],.5)
    model={'schema_version':1,'name':winner,'measurement':MEASUREMENT,'features':FEATURES,'target':target.to_dict(),'threshold':threshold,'ranges':{name:[float(X[tr,i].min()),float(X[tr,i].max())] for i,name in enumerate(FEATURES)},'estimator':export(selected)}
    # Portable JSON inference must agree with sklearn before any model is released.
    for row,expected_p in zip(X[te],pt):
        values=dict(zip(FEATURES,map(float,row)))
        if all(model['ranges'][k][0]<=v<=model['ranges'][k][1] for k,v in values.items()):
            actual=infer(model,values,MEASUREMENT)['score']
            if abs(actual-expected_p)>1e-7: raise AssertionError('Portable inference mismatch.')
    examples=[]
    for label in (0,1):
        valid=[i for i in te if y[i]==label and all(model['ranges'][k][0]<=float(X[i,j])<=model['ranges'][k][1] for j,k in enumerate(FEATURES))]
        for i in valid[:3]:
            examples.append({'label':f'Survey example {len(examples)+1}','features':dict(zip(FEATURES,map(float,X[i]))),'reported_match':bool(y[i])})
    output.mkdir(parents=True,exist_ok=True)
    for name,value in [('report',report),('model',model),('examples',examples)]:
        (output/f'{name}.json').write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
    print(f'Selected {winner}; threshold {threshold:.2f}; held-out AP {report["test"]["average_precision"]:.4f}',flush=True)
    return report

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',type=Path,default=ROOT/'config'/'target.json')
    parser.add_argument('--output',type=Path,default=ROOT/'artifacts')
    args=parser.parse_args();train(json.loads(args.config.read_text()),args.output)
