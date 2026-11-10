import unittest,numpy as np
from sklearn.datasets import make_classification
from personality.train import split_people,candidates,export
from personality.core import estimate
class TrainingTests(unittest.TestCase):
    def test_people_disjoint(self):
        y=np.array([0]*90+[1]*30);parts=split_people(y)
        self.assertEqual(len(set(np.concatenate(parts))),120)
        self.assertFalse(set(parts[0])&set(parts[1]));self.assertFalse(set(parts[0])&set(parts[2]));self.assertFalse(set(parts[1])&set(parts[2]))
        for a,b in zip(parts,split_people(y)):np.testing.assert_array_equal(a,b)
    def test_all_export_formats_match_sklearn(self):
        X,y=make_classification(n_samples=100,n_features=7,n_informative=4,random_state=12)
        for name,m in candidates().items():
            with self.subTest(model=name):
                m.fit(X,y);portable=export(m)
                np.testing.assert_allclose([estimate(portable,row) for row in X[:20]],m.predict_proba(X[:20])[:,1],rtol=1e-7,atol=1e-8)
if __name__=='__main__':unittest.main()
