"""Explicit past-use targets and portable inference. No questionnaire conversion."""
from dataclasses import dataclass, asdict
import math

DRUGS = {'alcohol':'Alcohol','amphetamines':'Amphetamines','amyl':'Amyl nitrite','benzodiazepines':'Benzodiazepines','caffeine':'Caffeine','cannabis':'Cannabis','chocolate':'Chocolate','cocaine':'Cocaine','crack':'Crack','ecstasy':'Ecstasy','heroin':'Heroin','ketamine':'Ketamine','legal_highs':'Legal highs','lsd':'LSD','methadone':'Methadone','mushrooms':'Mushrooms','nicotine':'Nicotine','vsa':'Volatile substances'}
WINDOWS = {'decade':2, 'year':3, 'month':4, 'week':5, 'day':6}
FEATURES = ['neuroticism','extraversion','openness','agreeableness','conscientiousness','impulsivity','sensation_seeking']
MEASUREMENT = 'uci373_quantified'

@dataclass(frozen=True)
class Target:
    substances: tuple = ('amphetamines','cocaine','crack','ketamine')
    window: str = 'month'
    minimum: int = 2

    def __post_init__(self):
        if not self.substances or len(set(self.substances)) != len(self.substances) or any(s not in DRUGS for s in self.substances):
            raise ValueError('Choose distinct substances from the dataset.')
        if self.window not in WINDOWS:
            raise ValueError('Unknown recency window.')
        if type(self.minimum) is not int or not 1 <= self.minimum <= len(self.substances):
            raise ValueError('Minimum must be between one and the number of substances.')

    @property
    def description(self):
        return f'Reported use of at least {self.minimum} of {", ".join(DRUGS[s] for s in self.substances)} within the past {self.window}'

    def evaluate(self, responses):
        values = []
        for s in self.substances:
            v = responses.get(s)
            if type(v) is not int or not 0 <= v <= 6:
                raise ValueError(f'Missing or invalid recency for {s}.')
            values.append(v)
        count = sum(v >= WINDOWS[self.window] for v in values)
        return {'matches': count >= self.minimum, 'count':count, 'description':self.description}

    def to_dict(self):
        return {**asdict(self), 'description':self.description}


def tree_value(tree, row):
    node=0
    while tree['left'][node]!=-1:
        node=tree['left'][node] if row[tree['feature'][node]] <= tree['threshold'][node] else tree['right'][node]
    return tree['value'][node]

def sigmoid(z):
    return 1/(1+math.exp(-max(-700,min(700,z))))

def estimate(est,row):
    kind=est['kind']
    if kind=='logistic':
        return sigmoid(est['intercept']+sum(c*(x-m)/s for c,x,m,s in zip(est['coefficients'],row,est['means'],est['scales'])))
    # sklearn tree prediction converts input to float32.
    import struct
    rounded=[struct.unpack('f',struct.pack('f',x))[0] for x in row]
    if kind=='forest': return sum(tree_value(t,rounded) for t in est['trees'])/len(est['trees'])
    if kind=='boosting': return sigmoid(est['initial']+est['rate']*sum(tree_value(t,rounded) for t in est['trees']))
    if kind=='ensemble': return sum(estimate(e,row) for e in est['members'])/len(est['members'])
    raise ValueError('Unsupported model format.')

def infer(model, values, measurement):
    if measurement != MEASUREMENT:
        raise ValueError('IPIP and NEO scores are not interchangeable. Use a dataset example; no validated questionnaire conversion is available.')
    if set(values) != set(model['features']):
        raise ValueError('Expected exactly the named model features.')
    for name,x in values.items():
        if type(x) not in (int,float) or not math.isfinite(x):
            raise ValueError(f'{name} must be a finite number.')
        low, high = model['ranges'][name]
        if not low <= x <= high:
            raise ValueError(f'{name} is outside the training range.')
    probability=estimate(model['estimator'],[values[k] for k in model['features']])
    return {'score':probability,'matches':probability >= model['threshold'], 'threshold':model['threshold'], 'meaning':'Model estimate of the defined past-use label in this survey sample, not future risk.'}
