import json
import sys
import tempfile
import unittest
from pathlib import Path
import numpy as np
import joblib
from sklearn.ensemble import RandomForestClassifier

REPO=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(REPO/"archivio/valutazione/addestramento/mqt"))
sys.path.insert(0,str(REPO/"archivio/esperimento_v2/scripts"))
sys.path.insert(0,str(REPO/"archivio/valutazione/test_mqt_esplorativo/strumenti"))
from validazione_selettore import validate_labels,validate_ml_classifier
from mqt_model_artifacts import FROZEN_DEVICES
from common import AREA

class ClassiTest(unittest.TestCase):
    def test_four_observed_classes_load(self):
        labels=list(FROZEN_DEVICES)[1:]
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"model.joblib"
            model=RandomForestClassifier(n_estimators=2,random_state=0).fit(np.zeros((4,49)),labels)
            joblib.dump(model,path)
            details,errors=validate_ml_classifier(path,observed=labels)
            self.assertEqual(errors,[])
            self.assertEqual(set(details["classes"]),set(labels))

    def test_single_observed_class_is_valid(self):
        self.assertEqual(validate_labels([FROZEN_DEVICES[0]],FROZEN_DEVICES,[FROZEN_DEVICES[0]]),[])

    def test_empty_unknown_duplicate_and_unlearned_rejected(self):
        for classes in ([],["unknown"],[FROZEN_DEVICES[0]]*2):
            self.assertTrue(validate_labels(classes,FROZEN_DEVICES))
        self.assertTrue(validate_labels([FROZEN_DEVICES[0]],FROZEN_DEVICES,FROZEN_DEVICES))

    def test_wrong_feature_count_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"model.joblib"
            joblib.dump(RandomForestClassifier(n_estimators=2).fit([[0],[1]],[FROZEN_DEVICES[0]]*2),path)
            self.assertTrue(validate_ml_classifier(path)[1])

    def test_invalid_probabilities_rejected(self):
        from types import SimpleNamespace
        from unittest.mock import patch
        labels=[FROZEN_DEVICES[0]]
        for values in ([[float("nan")]], [[-1.0]], [[0.2]], [[1.0,0.0]]):
            model=SimpleNamespace(classes_=labels,n_features_in_=49,predict_proba=lambda x:values)
            with patch("joblib.load",return_value=model):
                self.assertTrue(validate_ml_classifier(Path("unused"))[1])

    def test_worker_passes_target_to_rl_for_ml_and_forced_device(self):
        from unittest.mock import patch
        import worker
        import mqt.predictor.ml.predictor as ml_module
        original=ml_module.get_path_trained_model
        def capture(circuit,device,figure_of_merit):
            self.assertTrue(hasattr(device,"build_coupling_map"))
            self.assertEqual(figure_of_merit,"expected_fidelity")
            raise RuntimeError("target-accepted")
        try:
            for forced in (None,FROZEN_DEVICES[0]):
                with tempfile.TemporaryDirectory() as tmp:
                    job=Path(tmp)/"job.json"
                    job.write_text(json.dumps({"method":"mqt_predictor",
                        "source":str(REPO/"prototipo/examples/bell.qasm"),"rl_device":forced}))
                    with patch("mqt.predictor.rl.rl_compile",side_effect=capture):
                        self.assertEqual(worker.main(job),1)
                    result=json.loads((Path(tmp)/"result.json").read_text())
                    self.assertEqual(result["message"],"target-accepted")
        finally:
            ml_module.get_path_trained_model=original

    def test_plan_criteria_identical_and_area_separate(self):
        original=json.loads((REPO/"archivio/valutazione/test/piano.json").read_text())
        exploratory=json.loads((AREA/"piano.json").read_text())
        for key,value in original.items():
            if key!="test_id":
                self.assertEqual(exploratory[key],value,key)
        self.assertNotEqual(AREA,REPO/"archivio/valutazione/test")
        self.assertEqual((AREA/"strumenti/score.py").read_bytes(),
                         (REPO/"archivio/valutazione/test/strumenti/score.py").read_bytes())

if __name__=="__main__": unittest.main()
