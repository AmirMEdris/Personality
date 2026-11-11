import unittest
import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from personality.liss import recent_use,count_target,prepare,ITEMS
from personality.workbench import models,calibration_input

class WorkbenchTests(unittest.TestCase):
    def test_skip_and_missing_are_distinct(self):
        self.assertEqual(recent_use(2,np.nan),0)
        self.assertEqual(recent_use(1,4),1)
        self.assertEqual(recent_use(1,5),0)
        self.assertTrue(np.isnan(recent_use(1,np.nan)))
        with self.assertRaises(ValueError):recent_use(2,1)
        with self.assertRaises(ValueError):recent_use(np.nan,1)
    def test_partial_outcomes_use_bounds(self):
        result=count_target([[1,1,np.nan],[0,0,np.nan],[1,0,np.nan]],2)
        self.assertEqual(result[0],1);self.assertEqual(result[1],0);self.assertTrue(np.isnan(result[2]))
    def test_join_by_identity_not_position(self):
        p=pd.DataFrame({'nomem_encr':[20,10],**{k:[3,4] for k in ITEMS}})
        s=pd.DataFrame({'nomem_encr':[10,20],'ap08a130':[2,1],'ap08a142':[np.nan,4]})
        ids,x,y,quality=prepare(p,s,selected=('cannabis',),minimum=1)
        self.assertEqual(ids.tolist(),[20,10]);self.assertEqual(y.tolist(),[1,0]);self.assertEqual(x.shape,(2,50))
        with self.assertRaises(ValueError):prepare(pd.concat([p,p]),s,selected=('cannabis',),minimum=1)
    def test_stack_works_with_fold_local_missing_values(self):
        rng=np.random.default_rng(11);x=rng.normal(size=(90,7));y=(x[:,0]+x[:,1]>.2).astype(int);x[::9,3]=np.nan
        p=cross_val_predict(models()['stacked_ensemble'],x,y,cv=StratifiedKFold(3,shuffle=True,random_state=2),method='predict_proba')[:,1]
        self.assertTrue(np.isfinite(p).all());self.assertTrue(((p>=0)&(p<=1)).all())
        self.assertTrue(np.isfinite(calibration_input([0,1])).all())
if __name__=='__main__':unittest.main()
