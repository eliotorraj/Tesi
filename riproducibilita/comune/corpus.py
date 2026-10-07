'Freeze user-selected inputs without using historical outcomes.'
from collections import Counter, defaultdict
from pathlib import Path
import json, shutil
import settings as s

def prepare():
    from scripts.mqt_predictor_protocol import semantic_circuit_sha256, package_version_mismatches
    from qiskit_dataset.core import _extract_features
    from qiskit_dataset.catalog import load_catalog
    from qiskit_dataset.generation import build_target_record
    errors=package_version_mismatches()
    if errors:raise ValueError('Environment differs from uv.lock: '+str(errors))
    catalog=load_catalog(s.CATALOG_TEMPLATE)
    original=s.read(s.KIT/"circuiti/manifest_originale.json")["circuits"]
    original={(r["file_name"],r["source_sha256"]):r for r in original}
    source_rows=[]; hashes=defaultdict(list); semantics=defaultdict(set)
    for split in ("train","validation","test"):
        paths=sorted((s.CORPUS/split).glob("*.qasm"))
        if not paths:raise ValueError('No circuits in split '+split)
        for path in paths:
            # No family-name constraint: the user selects the corpus.
            features,meta=_extract_features(path)
            row=dict(circuit_id=path.stem,file_name=path.name,split=split,
                     source_sha256=s.sha(path),semantic_sha256=semantic_circuit_sha256(path),
                     source_ref=f"circuits/{split}/{path.name}",benchmark_family="user_supplied",
                     generator="original_qasm",leakage_group=path.stem,
                     features={"extractor":"mqt.predictor.ml.helper.create_feature_vector","dimension":49,"values":features},**meta)
            previous=original.get((path.name,row["source_sha256"]),{})
            for key in ("benchmark_family","generator","leakage_group"):
                if key in previous:row[key]=previous[key]
            hashes[row["source_sha256"]].append(row);semantics[row["semantic_sha256"]].add(split)
            source_rows.append(row)
    if len({x["circuit_id"] for x in source_rows})!=len(source_rows):
        raise ValueError('Duplicate circuit names across splits: use distinct names')
    if any(len({r["split"] for r in g})>1 for g in hashes.values()) or any(len(g)>1 for g in semantics.values()):
        raise ValueError('Identical contents or instruction sequences found in different splits')
    for rows in hashes.values():
        canonical=min(x["file_name"] for x in rows)
        for row in rows:row.update(canonical_circuit_id=Path(canonical).stem,
            is_exact_duplicate=len(rows)>1,is_duplicate_alias=row["file_name"]!=canonical,duplicate_group_size=len(rows))
    # Write the contract before copying; incompatible resumes overwrite nothing.
    contract={"config":s.CONFIG,"catalog_sha256":s.sha(s.CATALOG_TEMPLATE),"code":s.code_identity()}
    s.same_or_save(s.WORK/"contratto.json",contract)
    targets={d:build_target_record(d,2) for d in catalog.supported_device_ids}
    for d,t in targets.items():
        if t["target_sha256"]!=catalog.target_sha256[d]:raise ValueError('Target differs from the catalog: '+d)
    raw=s.read(s.CATALOG_TEMPLATE);raw["experiment_id"]=s.EXPERIMENT_ID
    raw["catalog_id"]=s.EXPERIMENT_ID+"-qiskit"
    s.same_or_save(s.CATALOG_PATH,raw)
    manifest={"schema_version":"2.0.0","experiment_id":s.EXPERIMENT_ID,"protocol_version":"2.0.0",
              "counts":dict(Counter(x["split"] for x in source_rows)),"circuits":source_rows,"targets":targets,
              "split_policy":{"type":"user_assigned_directories","limitations":'Hash and instruction-sequence checks do not prove family disjointness or general quantum equivalence.'}}
    for row in source_rows:
        source=s.CORPUS/row["split"]/row["file_name"];dest=s.WORK/row["source_ref"]
        dest.parent.mkdir(parents=True,exist_ok=True)
        if dest.exists():
            if s.sha(dest)!=row["source_sha256"]:raise ValueError('Copy differs: '+str(dest))
        else:shutil.copy2(source,dest)
    s.same_or_save(s.WORK/"manifest.json",manifest)
    s.same_or_save(s.WORK/"ingressi_sigillati.json",{name:s.sha(s.WORK/name) for name in ("manifest.json","catalogo.json")})
    return {"experiment_id":s.EXPERIMENT_ID,"counts":manifest["counts"],"unique_train":len({x["source_sha256"] for x in source_rows if x["split"]=="train"})}
