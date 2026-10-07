'Child process for one compilation; does not launch campaigns.'
import bootstrap
from pathlib import Path
import sys, time, traceback
import settings as s

def main(path):
    job=s.read(path);folder=Path(path).parent;start=time.perf_counter()
    # Terminate the child if its Linux supervisor exits.
    if sys.platform.startswith("linux"):
        import ctypes, os, signal
        parent=os.getppid();ctypes.CDLL(None).prctl(1,signal.SIGTERM)
        if os.getppid()!=parent:return 1
    try:
        if job["kind"]=="qiskit":
            from qiskit_dataset.generation import execute_attempt
            result=execute_attempt(job["task"])
            qasm=result.pop("_compiled_qasm2",None)
            if qasm is not None:(folder/"compiled.qasm").write_text(qasm)
        elif job["kind"]=="mqt":
            from qiskit import QuantumCircuit, qasm2
            from mqt.predictor.ml import predict_device_for_figure_of_merit
            from mqt.predictor.rl import rl_compile
            from mqt.bench.targets import get_device
            from scripts.mqt_predictor_protocol import validate_compiled_circuit
            from score import expected_fidelity
            from stable_baselines3.common.utils import set_random_seed
            set_random_seed(job["seed"])
            circuit=QuantumCircuit.from_qasm_file(job["source"])
            t=time.perf_counter();device=get_device(job["device"]) if job.get("device") else predict_device_for_figure_of_merit(circuit,figure_of_merit="expected_fidelity")
            device=device.description if hasattr(device,"description") else str(device)
            choice=time.perf_counter()-t;t=time.perf_counter()
            from mqt.predictor.rl.predictor import Predictor
            target=get_device(device)
            predictor=Predictor(figure_of_merit="expected_fidelity",device=target,max_steps=64)
            compiled,passes=rl_compile(circuit,device=target,figure_of_merit="expected_fidelity",predictor_singleton=predictor)
            duration=time.perf_counter()-t
            if not passes or str(passes[-1])!="terminate":raise ValueError('RL did not terminate')
            target=get_device(device);validation=validate_compiled_circuit(compiled,target)
            if not validation["is_executable_on_target"]:raise ValueError('MQT circuit does not conform to the Target')
            qasm2.dump(compiled,folder/"compiled.qasm")
            result={"status":"success","selected_device":device,"passes":list(map(str,passes)),"validation":validation,
                    "choice_seconds":choice,"compilation_seconds":duration,**expected_fidelity(compiled,target)}
        else:raise ValueError('Unknown job type')
    except Exception as exc:
        result={"status":"failure","score":None,"error":type(exc).__name__,"message":str(exc),"traceback":traceback.format_exc()}
    result["process_seconds"]=time.perf_counter()-start
    s.save(folder/"result.json",result)
    return 0
if __name__=="__main__":raise SystemExit(main(sys.argv[1]))
