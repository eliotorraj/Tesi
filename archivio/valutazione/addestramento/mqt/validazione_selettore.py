'Check the selector without requiring nonexistent winning classes.'
from pathlib import Path

def validate_labels(classes, allowed, observed=None):
    values=list(map(str,classes))
    errors=[]
    if not values or len(values)!=len(set(values)) or not set(values).issubset(set(allowed)):
        errors.append('ML classes are empty, duplicated or outside the allowed device set')
    if observed is not None and set(values)!=set(map(str,observed)):
        errors.append('ML classes differ from the labels observed in the Training set')
    return errors

def validate_ml_classifier(path: Path, observed=None):
    from mqt_model_artifacts import FROZEN_DEVICES, EXPECTED_FEATURE_COUNT
    details={"path":str(path),"kind":"ml"}
    errors=[]
    try:
        import joblib
        import numpy as np
        model=joblib.load(path)
        classes=list(map(str,model.classes_))
        width=getattr(model,"n_features_in_",None)
        details.update(classes=classes,feature_count=int(width) if width is not None else None,
                       classifier_type=type(model).__module__+"."+type(model).__qualname__)
        errors.extend(validate_labels(classes,FROZEN_DEVICES,observed))
        if width!=EXPECTED_FEATURE_COUNT:
            errors.append('Invalid ML feature count')
        if not errors:
            probs=np.asarray(model.predict_proba(np.zeros((1,EXPECTED_FEATURE_COUNT))),dtype=float)
            if (probs.shape!=(1,len(classes)) or not np.isfinite(probs).all()
                or (probs<0).any() or (probs>1).any() or not np.allclose(probs.sum(axis=1),1)):
                errors.append('Invalid ML probabilities')
    except Exception as exc:
        errors.append('Cannot load classifier: '+type(exc).__name__+": "+str(exc))
    return details,errors
