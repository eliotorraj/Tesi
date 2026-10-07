'Checks for the new descriptive threshold, without running the Test.'
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dati import aggregate
from pannelli import threshold_counts
from confronto import discrete


class ThresholdTests(unittest.TestCase):
    def test_cutoff_is_inclusive_and_denominator_keeps_failures_and_pending(self):
        rows=[
            dict(circuit_id='a',source_sha256='a',status='success',score=0.8),
            dict(circuit_id='b',source_sha256='b',status='success',score=0.799999),
            dict(circuit_id='c',source_sha256='c',status='failure',score=None),
            dict(circuit_id='d',source_sha256='d',status='success',score=0.0),
        ]
        circuits,_=aggregate(rows,['a','b','c','d','e'],'random')
        counts=threshold_counts({'circuits':circuits})
        self.assertEqual(counts,dict(total=5,high=1,low=2,no_score=1,pending=1))
        self.assertEqual(sum(counts[k] for k in ('high','low','no_score','pending')),counts['total'])

    def test_fractional_replica_mean_is_not_rounded_to_an_integer(self):
        self.assertEqual(discrete(12.0),'12')
        self.assertEqual(discrete(0),'0')
        self.assertEqual(discrete(1.5),'1,50')
        self.assertEqual(discrete(None),'--')


if __name__=='__main__':
    unittest.main()

