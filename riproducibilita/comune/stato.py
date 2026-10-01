"""Indica i passaggi presenti su disco; non avvia né promuove una prova."""
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
    print("Esperimento:", name)
    print("Risultati:", s.OUTPUT)
    files = [
        ("Corpus e Target preparati", s.WORK / "ingressi_sigillati.json"),
        ("Dataset train/validation sigillato", s.WORK / "data/seal.json"),
        ("Griglia LLM congelata", s.VALIDATION / "contratto.json"),
        ("LLM e temperatura selezionati", s.VALIDATION / "selezione.json"),
        ("Prove tecniche MQT superate", s.MQT / "prove_tecniche/superate.json"),
        ("Piano Test congelato", s.TEST / "contratto.json"),
    ]
    for title, path in files:
        print(("[presente] " if path.exists() else "[da fare] ") + title)
    print("Gli indicatori mostrano file presenti; i comandi delle fasi ne verificano integrità e contenuto.")
    if not (s.WORK / "ingressi_sigillati.json").exists():
        print("Prossimo passo:", base, "prepara")
        return
    try:
        manifest = s.require_prepared()
    except (ValueError, OSError, KeyError) as exc:
        print("Integrità da risolvere:", exc)
        return
    if not (s.WORK / "data/seal.json").exists():
        print("Prossimo passo:", base, "dataset")
    elif not (s.VALIDATION / "contratto.json").exists():
        print("Prossimo passo:", base, "validation congela")
    elif not (s.VALIDATION / "selezione.json").exists():
        print("Avviare e controllare un server per ciascun candidato attivo, poi:")
        for model in s.model_registry():
            print(" ", base, "validation esegui --modello", model)
        print("Dopo tutti i candidati:", base, "validation seleziona")
    else:
        winner = s.read(s.VALIDATION / "selezione.json")["winner"]
        print(f"Selezione: {winner['model']}, temperatura {winner['temperature']}")
        if "mqt" in s.CONFIG["test_methods"] and not (s.MQT / "prove_tecniche/superate.json").exists():
            print("Prima del Test completare RL, selettore e test tecnico-mqt; vedere mqt/README.md.")
        if set(s.CONFIG["test_methods"]) & {"llm_wl", "llm_wl_sintesi"}:
            print("Per WL serve anche la selezione del recupero:", base, "validation wl")
        if not (s.TEST / "contratto.json").exists():
            print("Quando i prerequisiti sono pronti:", base, "test congela")
        else:
            expected = sum(row["split"] == "test" for row in manifest["circuits"])
            for method in s.CONFIG["test_methods"]:
                results = list((s.TEST / method / "circuiti").glob("*/esito.json"))
                success = sum(s.read(path).get("status") == "success" for path in results)
                print(f"  {method}: {len(results)}/{expected} esiti registrati, {success} successi")
                if len(results) < expected: print("   ", base, "test esegui --metodo", method)
            print("Riepilogo dei risultati disponibili:", base, "test analizza")
            print("Esportazione su richiesta:", base, "esporta /percorso/nuovo-prototipo")
