"""Un tentativo isolato; nessun accesso a risultati precedenti o sistemi decisionali."""
from pathlib import Path
import ctypes
import os
import signal
import sys
import time
import traceback
sys.dont_write_bytecode=True
from archivio.valutazione.oracle_qasmbench.oracle_core import read,publish,publish_bytes,sha,digest,now,terminal

class Deadline(TimeoutError):
    pass

def main(folder):
    folder=Path(folder).resolve()
    run=folder.parent.parent
    begin=read(folder/"inizio.json")
    job=begin["job"]
    # A killed supervisor must not leave its worker running.
    libc=ctypes.CDLL(None,use_errno=True)
    if libc.prctl(1,signal.SIGKILL,0,0,0)!=0:
        raise OSError(ctypes.get_errno(),"prctl PR_SET_PDEATHSIG")
    if os.getppid()!=begin["supervisor_pid"]:
        raise RuntimeError("Supervisore non più attivo.")
    # Imports are outside the 100 s, as in the original Dataset executor.
    from qiskit import QuantumCircuit,transpile,qasm2
    from mqt.bench.targets import get_device
    from scripts.mqt_predictor_protocol import target_payload
    from prototype.quantum_assistant.adapters.compilation import _validate_compiled_circuit
    from score import expected_fidelity

    start=time.monotonic()
    timings={}
    phase="source_loading"
    progress={"completed_pass_count":0,"last_completed_pass":None}
    result=terminal(job,"failure","Tentativo non completato")
    publish(folder/"ready.json",{"started_monotonic":start,"timeout_seconds":job["timeout_seconds"],"at":now()})
    def alarm(*_):
        raise Deadline("Limite di 100 secondi del tentativo.")
    signal.signal(signal.SIGALRM,alarm)
    signal.setitimer(signal.ITIMER_REAL,job["timeout_seconds"])
    def stage(name):
        nonlocal phase
        phase=name
        publish(folder/(name+".json"),{"at":now(),"elapsed":time.monotonic()-start})
        return time.monotonic()
    try:
        tick=stage("source_loading")
        source=(run/job["source"]).resolve()
        if not source.is_relative_to(run/"sorgenti") or sha(source)!=job["source_sha256"]:
            raise ValueError("Sorgente dell'oracle alterato.")
        circuit=QuantumCircuit.from_qasm_file(str(source))
        timings[phase]=time.monotonic()-tick
        tick=stage("target_loading")
        target=get_device(job["device"])
        if digest(target_payload(target))!=job["target_sha256"] or circuit.num_qubits>target.num_qubits:
            raise ValueError("Target diverso o incompatibile.")
        timings[phase]=time.monotonic()-tick
        tick=stage("transpilation")
        def callback(**info):
            p=info.get("pass_")
            progress["completed_pass_count"]+=1
            progress["last_completed_pass"]={"name":p.name() if p else None,
                "class":type(p).__module__+"."+type(p).__name__ if p else None,"elapsed":time.monotonic()-tick}
        opts={"optimization_level":job["configuration"]["optimization_level"],**job["fixed_options"]}
        for key in ("layout_method","routing_method"):
            if job["configuration"][key] is not None:opts[key]=job["configuration"][key]
        compiled=transpile(circuit,target=target,seed_transpiler=job["seed"],callback=callback,**opts)
        timings[phase]=time.monotonic()-tick
        tick=stage("target_validation")
        validation=_validate_compiled_circuit(compiled,target)
        if not validation["is_executable_on_target"]:raise ValueError("Circuito non eseguibile: "+str(validation))
        timings[phase]=time.monotonic()-tick
        tick=stage("scoring")
        metrics=expected_fidelity(compiled,target)
        timings[phase]=time.monotonic()-tick
        tick=stage("serialization")
        qasm=qasm2.dumps(compiled).encode()
        publish_bytes(folder/"compiled.qasm",qasm)
        timings[phase]=time.monotonic()-tick
        result={**result,"status":"success","reason":None,**metrics,"validation":validation,
                "compiled_sha256":sha(folder/"compiled.qasm"),"depth":compiled.depth(),"size":compiled.size(),
                "operation_counts":dict(compiled.count_ops()),
                "two_qubit_gates":sum(len(i.qubits)==2 and i.operation.name!="barrier" for i in compiled.data)}
    except Exception as exc:
        signal.setitimer(signal.ITIMER_REAL,0)
        result={**result,"status":"timeout" if isinstance(exc,Deadline) else "failure","score":None,
                "reason":type(exc).__name__,"message":str(exc),"traceback":traceback.format_exc()}
    finally:
        signal.setitimer(signal.ITIMER_REAL,0)
    total=time.monotonic()-start
    if total>job["timeout_seconds"] and result["status"]=="success":
        result={**result,"status":"timeout","score":None,"reason":"late_result","late_metrics_preserved":metrics}
    result.update(at=now(),phase=phase,timings={**timings,"total":total},transpiler_progress=progress,
                  ended_monotonic=time.monotonic(),memory_measurement="not collected")
    publish(folder/"worker_result.json",result)
    return 0 if result["status"]=="success" else 1

if __name__=="__main__":
    raise SystemExit(main(sys.argv[1]))
