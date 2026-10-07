'Read-only inventory of the specified selectors, without replacements.'
import json,sys,hashlib,warnings
from pathlib import Path
from uuid import uuid4
area=Path(__file__).resolve().parents[1]
records=[]
for path in (
    Path("/home/elio/Tesi/.venv/lib/python3.12/site-packages/mqt/predictor/ml/training_data/trained_model/trained_clf_expected_fidelity.joblib"),
    area.parent/"test_mqt_esplorativo/runtime/trained_clf_expected_fidelity.joblib",
):
    row={"path":str(path),"exists":path.is_file()}
    if path.is_file():
        row.update(size_bytes=path.stat().st_size,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            metadata_exists=path.with_suffix(".metadata.json").exists())
        try:
            import joblib
            with warnings.catch_warnings(record=True) as caught:
                model=joblib.load(path)
            row.update(classifier=type(model).__name__,features=getattr(model,"n_features_in_",None),
                classes=list(map(str,getattr(model,"classes_",[]))),
                warnings=[str(w.message) for w in caught])
        except Exception as exc:
            row.update(error=type(exc).__name__,message=str(exc))
    records.append(row)
text=json.dumps(records,indent=2,default=str)+"\n"
out=area/"verifiche/registri"/("selettori-"+uuid4().hex+".json")
out.write_text(text)
print(text)
