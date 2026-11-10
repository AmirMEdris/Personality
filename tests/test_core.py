import json,math,unittest
from pathlib import Path
from personality.core import Target,infer,MEASUREMENT,FEATURES
ROOT=Path(__file__).resolve().parents[1]
class CoreTests(unittest.TestCase):
    def test_count_not_average(self):
        t=Target();d=dict.fromkeys(t.substances,0);d['cocaine']=6
        self.assertFalse(t.evaluate(d)['matches'])
        d['ketamine']=4;self.assertTrue(t.evaluate(d)['matches'])
        d['cocaine']=3;self.assertFalse(t.evaluate(d)['matches'])
    def test_nested_windows(self):
        for window in ['decade','year','month','week','day']:
            self.assertTrue(Target(('cocaine',),window,1).evaluate({'cocaine':6})['matches'])
    def test_invalid_target(self):
        for args in [((), 'month',1),(('cocaine','cocaine'),'month',1),(('cocaine',),'month',True),(('cocaine',),'month',2),(('unknown',),'month',1)]:
            with self.assertRaises(ValueError):Target(*args)
        with self.assertRaises(ValueError):Target().evaluate({'cocaine':True})
    def test_measurement_and_features(self):
        model=json.loads((ROOT/'artifacts/model.json').read_text());example=json.loads((ROOT/'artifacts/examples.json').read_text())[0]['features']
        self.assertTrue(0<=infer(model,example,MEASUREMENT)['score']<=1)
        for measurement in ['ipip','neo_raw','']:
            with self.assertRaises(ValueError):infer(model,example,measurement)
        for value in [float('nan'),float('inf'),True,999,'1']:
            with self.assertRaises(ValueError):infer(model,{**example,'openness':value},MEASUREMENT)
        with self.assertRaises(ValueError):infer(model,{},MEASUREMENT)
        self.assertEqual(model['features'],FEATURES)
    def test_questionnaire_keys(self):
        survey=json.loads((ROOT/'web/survey.json').read_text());byname={s['trait']:s for s in survey}
        self.assertEqual(set(byname),set(FEATURES[:5]))
        self.assertEqual([q['direction'] for q in byname['neuroticism']['items']],[1,-1,1,-1,1,1,1,1,1,1])
        for s in survey:
            self.assertEqual(len(s['items']),10)
            self.assertTrue(all(q['direction'] in [-1,1] for q in s['items']))
if __name__=='__main__':unittest.main()
