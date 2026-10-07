'Show phases present on disk without starting or promoting a run.'
import os
import shlex
import settings as s


def show():
    name = s.EXPERIMENT_ID
    named = s.CONFIG_PATH.parent.parent == s.KIT / "configurazioni/esperimenti"
    choose = "--esperimento " + shlex.quote(name) if named else "--config " + shlex.quote(str(s.CONFIG_PATH))
    base = ".venv/bin/python esperimento.py " + choose
    if "RIPRO_OUTPUT" in os.environ:
        base += " --output " + shlex.quote(str(s.OUTPUT))
    print('Experiment:', name)
    print('Results:', s.OUTPUT)
    files = [
        ('Corpus and Targets prepared', s.WORK / "ingressi_sigillati.json"),
        ('Train/validation Dataset sealed', s.WORK / "data/seal.json"),
        ('Frozen LLM grid', s.VALIDATION / "contratto.json"),
        ('Selected LLM and temperature', s.VALIDATION / "selezione.json"),
        ('MQT technical checks passed', s.MQT / "prove_tecniche/superate.json"),
        ('Frozen Test plan', s.TEST / "contratto.json"),
    ]
    for title, path in files:
        print(('[present] ' if path.exists() else '[pending] ') + title)
    print('Indicators show existing files; phase commands verify their integrity and content.')
    if not (s.WORK / "ingressi_sigillati.json").exists():
        print('Next step:', base, "prepara")
        return
    try:
        manifest = s.require_prepared()
    except (ValueError, OSError, KeyError) as exc:
        print('Integrity issues to resolve:', exc)
        return
    if not (s.WORK / "data/seal.json").exists():
        print('Next step:', base, "dataset")
    elif not (s.VALIDATION / "contratto.json").exists():
        print('Next step:', base, "validation congela")
    elif not (s.VALIDATION / "selezione.json").exists():
        print('Start and check a server for each active candidate, then:')
        for model in s.model_registry():
            print(" ", base, "validation esegui --modello", model)
        print('After all candidates:', base, "validation seleziona")
    else:
        winner = s.read(s.VALIDATION / "selezione.json")["winner"]
        print(f"Selection: {winner['model']}, temperature {winner['temperature']}")
        if "mqt" in s.CONFIG["test_methods"] and not (s.MQT / "prove_tecniche/superate.json").exists():
            print('Before Test, complete RL training, selector training and test tecnico-mqt; see mqt/README.md.')
        if set(s.CONFIG["test_methods"]) & {"llm_wl", "llm_wl_sintesi"}:
            print('WL also requires retrieval selection:', base, "validation wl")
        if not (s.TEST / "contratto.json").exists():
            print('When prerequisites are ready:', base, "test congela")
        else:
            expected = sum(row["split"] == "test" for row in manifest["circuits"])
            for method in s.CONFIG["test_methods"]:
                results = list((s.TEST / method / "circuiti").glob("*/esito.json"))
                success = sum(s.read(path).get("status") == "success" for path in results)
                print(f'  {method}: {len(results)}/{expected} outcomes recorded, {success} successes')
                if len(results) < expected: print("   ", base, "test esegui --metodo", method)
            print('Summary of available results:', base, "test analizza")
            print('Export on request:', base, 'esporta /path/to/new-prototype')
