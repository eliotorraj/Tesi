"""Giornale append-only: la memoria deriva soltanto da passaggi conclusi."""
from __future__ import annotations
from comune import *
from memoria import make_observation


def expected_observation(base, folder, row, position, records, contract):
    result = read(folder / "esito.json")
    if (result.get("circuit_id") != row["circuit_id"]
            or result.get("source_sha256") != row["source_sha256"]):
        raise ValueError("Esito di un altro circuito.")
    strategy = contract["strategy"]
    if result.get("method") != method_for(strategy) or result.get("k") != 1:
        raise ValueError("Esito estraneo al sistema k=1.")
    if strategy == "fixed" and records:
        raise ValueError("Il RAG fisso non può usare memoria incrementale.")
    if result.get("status") == "success" and not valid_score(result):
        raise ValueError("Successo con score non valido.")
    if not valid_score(result):
        return None, "unsuccessful_or_missing_score"
    if sha(folder / "input.qasm") != row["source_sha256"]:
        raise ValueError("Ingresso compilato diverso dalla sorgente.")
    if not (folder / "compilazione/compiled.qasm").is_file():
        raise ValueError("Circuito compilato mancante.")
    prompt = read(folder / "prompt.json")
    retrieval = read(folder / "retrieval.json")
    if (retrieval.get("k") != 1 or len(retrieval.get("records", [])) != 1
            or len(prompt.get("retrieved_labeled_examples", [])) != 1):
        raise ValueError("Recupero diverso da k=1.")
    if strategy == "fixed" and (retrieval.get("memory_size") != 0
            or any(r["origin"] != "initial" for r in retrieval["records"])):
        raise ValueError("Il RAG fisso ha recuperato memoria incrementale.")
    if hashlib.sha256(prompt["live_request"]["circuit"]["qasm2"].encode()).hexdigest() != hashlib.sha256((folder / "input.qasm").read_text().encode()).hexdigest():
        raise ValueError("Prompt e ingresso non concordano.")
    known = set(contract["initial_source_hashes"]) | {r["source_sha256"] for r in records}
    observation, reason = make_observation(
        row, position, result, prompt, read(folder / "decision.json"),
        read(folder / "compilazione/result.json"), known_hashes=known,
        experiment_id=contract["experiment_id"], order=contract["order"],
        target_hashes=contract["targets"], result_sha256=sha(folder / "esito.json"))
    return (None, "fixed_dataset") if strategy == "fixed" else (observation, reason)


def finish_step(base, contract, position, row, records, previous):
    folder = step_folder(base, position, row)
    for name in ("begin.json", "retrieval.json"):
        path = folder / name
        if path.exists():
            before = read(path).get("memory_before_sha256")
            if before is not None and before != memory_digest(records):
                raise ValueError("La decisione ha usato una memoria diversa dal prefisso concluso.")
    observation, reason = expected_observation(base, folder, row, position, records, contract)
    pointer = None
    if observation is not None:
        path = base / "memoria_incrementale/records" / f"{position:03d}.json"
        if path.exists():
            if read(path) != observation:
                raise ValueError("Osservazione pendente incompatibile; non viene sostituita.")
        else:
            save(path, observation)
        pointer = {"path": str(path.relative_to(base)), "sha256": sha(path)}
    after = records + ([observation] if observation else [])
    commit = {
        "schema_version": 1, "position": position, "circuit_id": row["circuit_id"],
        "contract_sha256": sha(base / "contratto.json"), "previous_commit_sha256": previous,
        "memory_before_sha256": memory_digest(records), "memory_after_sha256": memory_digest(after),
        "memory_before_count": len(records), "memory_after_count": len(after),
        "observation": pointer, "admission": reason, "files": path_hashes(base, folder),
    }
    # Il circuito compilato deve essere durevole prima del commit che lo identifica.
    for relative in commit["files"]:
        with (base / relative).open("rb") as handle:
            os.fsync(handle.fileno())
    save(folder / "commit.json", commit)
    return after, sha(folder / "commit.json")


def replay(base, contract):
    records, commits, previous, gap = [], [], None, False
    expected_folders = set()
    for position, row in enumerate(contract["rows"], 1):
        folder = step_folder(base, position, row)
        expected_folders.add(folder.name)
        path = folder / "commit.json"
        if not path.exists():
            gap = True
            continue
        if gap:
            raise ValueError("Passaggio futuro concluso prima di un passaggio precedente.")
        commit = read(path)
        if (commit["position"] != position or commit["circuit_id"] != row["circuit_id"]
                or commit["contract_sha256"] != sha(base / "contratto.json")
                or commit["previous_commit_sha256"] != previous
                or commit["memory_before_sha256"] != memory_digest(records)
                or commit["memory_before_count"] != len(records)):
            raise ValueError("Catena dei passaggi non valida.")
        for relative, expected in commit["files"].items():
            validate_relative_file(base, relative, expected)
        if commit["files"] != path_hashes(base, folder):
            raise ValueError("File aggiunti o rimossi da un passaggio concluso.")
        observation, reason = expected_observation(base, folder, row, position, records, contract)
        if reason != commit["admission"]:
            raise ValueError("Regola di ammissione non rispettata.")
        pointer = commit["observation"]
        if observation is None:
            if pointer is not None:
                raise ValueError("Un fallimento non può alimentare il Dataset.")
        else:
            if pointer is None:
                raise ValueError("Osservazione attesa ma mancante.")
            p = validate_relative_file(base, pointer["path"], pointer["sha256"])
            if read(p) != observation:
                raise ValueError("Osservazione diversa dall'esito verificato.")
            records.append(observation)
        if (commit["memory_after_sha256"] != memory_digest(records)
                or commit["memory_after_count"] != len(records)):
            raise ValueError("Memoria finale del passaggio incoerente.")
        commits.append(commit)
        previous = sha(path)
    for path in (base / "circuiti").glob("*"):
        if path.is_dir() and path.name not in expected_folders:
            raise ValueError("Cartella di un circuito fuori contratto.")
    # Un solo passaggio può essere pendente; non caricare mai file di memoria non pubblicati.
    for position, row in enumerate(contract["rows"], 1):
        if position > len(commits) + 1 and step_folder(base, position, row).exists():
            raise ValueError("Artefatti di passaggi futuri fuori sequenza.")
    return records, commits, previous


def recover_interruption(folder, row, position, strategy):
    from runner import llm_metrics
    result = {"circuit_id": row["circuit_id"], "source_sha256": row["source_sha256"],
              "position": position, "method": method_for(strategy), "k": 1, "strategy": strategy, "status": "interrupted",
              "score": None, "split": "test", "finished_at": now(),
              "error": "previous_process_stopped_without_final_result", "total_seconds": None}
    result.update(llm_metrics(folder))
    save(folder / "esito.json", result)


def export_memory(base, records):
    """Esportazione derivata finale; il giornale resta la fonte della ripresa."""
    path = base / "memoria_incrementale/dataset.jsonl"
    text = "".join(json.dumps(r, ensure_ascii=False, sort_keys=True, allow_nan=False) + "\n" for r in records)
    if path.exists():
        if path.read_text() != text:
            raise ValueError("Esportazione finale già presente e diversa.")
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name("." + uuid4().hex + ".tmp")
        with tmp.open("x", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(tmp, path)
        finally:
            tmp.unlink()
