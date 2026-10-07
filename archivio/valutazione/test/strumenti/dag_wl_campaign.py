'Two independent Test campaigns; require explicit validation selection.'
from __future__ import annotations
import argparse
from contextlib import contextmanager
from functools import partial
import json
from pathlib import Path
import sys
import time
import types
from uuid import uuid4
from common import AREA, ROOT, SOURCE, PLAN, read, save, sha, digest, now, code_files
sys.path.insert(0,str(ROOT))
from dag_wl_core import SUPPORTED_H, REPRESENTATION, prepare_index, prepare_wl
from dag_wl_validation import load_selection
from numero_esempi import ensure_contract, summarize
from runner import evaluate, interrupted_result, verify_server
from gates import preflight, frozen_contract

SUMMARY_NOTE = (
    "Additional deterministic summaries of the original uncompiled circuit DAGs follow. "
    "current_circuit describes the requested circuit; E1-E5 identify the same examples above. "
    "Ports q0, q1, etc. are local operand positions, not absolute qubit identities. "
    "Dependency layers are structural, not execution times. Barriers are included in layer counts. "
    "Transition lists show at most eight most frequent direct transitions, with counts and omissions. "
    "Interaction statistics use two-qubit operations only. "
    "These summaries do not measure compiled quality and do not add new allowed fact assertion types. "
    "Use the unchanged response schema and distinguish historical facts from hypotheses."
)

def summary_messages(prompt, feedback=(), *, max_examples=5):
    from prototype.prompting.facts import messages
    from prototype.prompting.toon import encode_view
    from prototype.prompting.minimal import citation_context
    values = prompt.get("dag_summaries")
    context = citation_context(prompt,max_examples=max_examples)
    if not values or [e["example_id"] for e in values["examples"]] != list(context.aliases):
        raise ValueError('Missing summaries or aliases differ from retrieved examples.')
    result = messages(prompt, feedback, max_examples=max_examples)
    fence = chr(96)*3
    result[0]["content"] += "\n"+SUMMARY_NOTE+"\n"+fence+"toon\n"+encode_view({"dag_summaries":values})+"\n"+fence+"\n"
    return result

@contextmanager
def prompt_variant(enabled):
    'Adapter in the dedicated process only: no shared source is modified.'
    import app
    original = app.decide
    if enabled:
        namespace = dict(original.__globals__)
        namespace["messages"] = summary_messages
        adapted = types.FunctionType(original.__code__, namespace, original.__name__,
                                     original.__defaults__, original.__closure__)
        adapted.__kwdefaults__ = original.__kwdefaults__
        app.decide = adapted
    try:
        yield
    finally:
        app.decide = original

def cli(with_summary, argv=None):
    method = "llm_rag_dag_wl_sintesi" if with_summary else "llm_rag_dag_wl"
    campaign = AREA/("dag_wl_sintesi" if with_summary else "dag_wl_retrieval")
    ap = argparse.ArgumentParser(description=method+'; five examples, separate index and results')
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--verifica",action="store_true")
    group.add_argument("--tecnico",action="store_true",help='Synthetic Bell only, not the Test')
    group.add_argument("--esegui",action="store_true",help='90 cases, only with frozen WL selection')
    ap.add_argument("--config-wl",type=Path)
    ap.add_argument("--h-tecnico",type=int,choices=SUPPORTED_H,default=1)
    ap.add_argument("--url",default="http://127.0.0.1:8089")
    ap.add_argument("--model-path",type=Path)
    args = ap.parse_args(argv)
    if args.esegui and args.config_wl is None:
        ap.error('--esegui requires --config-wl: complete and discuss validation first.')
    if not args.url.startswith(("http://127.0.0.1:","http://localhost:")):
        ap.error('The server must be local.')
    selection = load_selection(args.config_wl) if args.config_wl else None
    h = selection["h"] if selection else args.h_tecnico
    check = preflight(method)
    check["wl_selection"] = selection["sha256"] if selection else None
    check["ready_for_test"] = check["ready"] and selection is not None
    save(campaign/"preparazione/verifiche"/(uuid4().hex+".json"),check)
    print(json.dumps(check,ensure_ascii=False,indent=2),flush=True)
    if not check["ready"]:
        return 1
    if args.verifica:
        return 0
    base = campaign/"prove_tecniche"/uuid4().hex if args.tecnico else campaign/"risultati"/method
    base.mkdir(parents=True,exist_ok=True)
    import portalocker
    from prototype.quantum_assistant.adapters.rag_dataset import load_corpus
    import app
    with portalocker.Lock(str(base/".lock"),timeout=0):
        try:
            server = verify_server(args)
            save(base/"sessioni"/(uuid4().hex+".json"),{"at":now(),"server":server})
        except Exception as exc:
            save(base/"sessioni"/(uuid4().hex+".json"),{"at":now(),"server_error":str(exc)})
            raise
        contract = {
            "kind":"technical" if args.tecnico else "exploratory_test_extension",
            "method":method,"h":h,"k":5,"representation":REPRESENTATION,
            "selection":selection,"prompt_variant":"dag-summary-v1" if with_summary else "unchanged-facts-v4",
            "summary_note":SUMMARY_NOTE if with_summary else None,
            "inputs":frozen_contract(),
            "note":'Extension on the already exposed Test; same retrieval in both variants.',
        }
        contract_sha = ensure_contract(base/"contratto_congelato.json",contract)
        corpus = load_corpus()
        index_start = time.perf_counter()
        index, index_sha = prepare_index(corpus,base/"indice")
        save(base/"preparazione"/(uuid4().hex+".json"),{
            "at":now(),"index_sha256":index_sha,"index_preparation_seconds":time.perf_counter()-index_start,
            "note":'Separate cost; index verified/loaded once per session and reused.',
        })
        if not (base/"esecuzione.json").exists():
            save(base/"esecuzione.json",{"at":now(),"method":method,"expected_circuits":1 if args.tecnico else 90,
                 "contract_sha256":contract_sha,"server":server,"code":code_files(),
                 "index_sha256":index_sha,"memory_measurement":"not collected"})
        else:
            old=read(base/"esecuzione.json")
            if old["contract_sha256"]!=contract_sha or old["index_sha256"]!=index_sha:
                raise ValueError('Incompatible resume.')
        prepare = partial(prepare_wl,corpus=corpus,index=index,h=h,with_summary=with_summary,index_sha256=index_sha)
        if args.tecnico:
            source=ROOT/"examples/bell.qasm"
            rows=[{"circuit_id":"bell_tecnico","source_sha256":sha(source),"technical_source":str(source)}]
        else:
            rows=sorted((r for r in read(SOURCE)["circuits"] if r["split"]=="test"),key=lambda r:r["circuit_id"])
            if len(rows)!=90:
                raise ValueError('Expected 90 Test circuits.')
        with prompt_variant(with_summary):
            for i,row in enumerate(rows,1):
                folder=base/"circuiti"/row["circuit_id"]
                if (folder/"esito.json").exists():
                    continue
                if (folder/"begin.json").exists():
                    interrupted_result(row,folder,method)
                else:
                    try:
                        evaluate(row,folder,method,args.url,args.tecnico,prepare_fn=prepare)
                    except app.LlmTransportError as exc:
                        print('Transport interrupted, records preserved: '+str(exc),file=sys.stderr)
                        return 1
                print(f"{method}: {i}/{len(rows)} {row['circuit_id']}",flush=True)
        paths=sorted((base/"circuiti").glob("*/esito.json"))
        result=summarize(base,paths,len(rows))
        result.update(method=method,h=h,k=5,contract_sha256=contract_sha,
                      selection_sha256=selection["sha256"] if selection else None,
                      graph_summary_in_prompt=with_summary,index_sha256=index_sha,
                      note='Compare index times separately from per-circuit times.',
                      sources={str(p.relative_to(base)):sha(p) for p in paths})
        output=base/"analisi"/(uuid4().hex+".json")
        save(output,result)
        print('Summary: '+str(output))
    return 0
