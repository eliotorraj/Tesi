"""Importa la selezione QASMBench fissata. Nessuna inferenza o compilazione."""
import argparse, hashlib, json, urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
AREA = Path(__file__).resolve().parent
REPO = AREA.parents[2]
REVISION = "357b942396d5c2b7cbc1c229c585a6ef5ccaebac"
SELECTED = {
 "small": """deutsch_n2 iswap_n2 quantumwalks_n2 grover_n2 dnn_n2 qaoa_n3
toffoli_n3 fredkin_n3 wstate_n3 basis_change_n3 qrng_n4 cat_state_n4 adder_n10
adder_n4 hs4_n4 bell_n4 qft_n4 variational_n4 vqe_n4 sat_n7 basis_trotter_n4
lpn_n5 qec_en_n5 pea_n5 simon_n6 qaoa_n6 hhl_n7 dnn_n8 qpe_n9 ising_n10""".split(),
 "medium": """sat_n11 multiply_n13 bv_n14 multiplier_n15 dnn_n16 qec9xz_n17
qft_n18 bigadder_n18 gcm_n13 qram_n20 cat_state_n22 ghz_state_n23
swap_test_n25 ising_n26 wstate_n27""".split(),
 "large": "adder_n28 qft_n63 ising_n98 qugan_n111 bv_n140".split(),
}
def source_ref(group,name):
    filename = "gcm_h6" if name == "gcm_n13" else name
    return f"{group}/{name}/{filename}.qasm"
def sha(data): return hashlib.sha256(data).hexdigest()
def download(relative):
    url=f"https://raw.githubusercontent.com/pnnl/QASMBench/{REVISION}/{relative}"
    with urllib.request.urlopen(url,timeout=60) as response: data=response.read()
    path=AREA/"circuiti"/relative
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():
        if path.read_bytes()!=data: raise ValueError(f"File diverso, non sovrascritto: {path}")
    else: path.write_bytes(data)
def inspect():
    from qiskit import QuantumCircuit
    records,hashes=[],set()
    source=REPO/"archivio/esperimento_v2/artifacts/experiments/qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/manifests/source_circuits_v2.json"
    previous=json.loads(source.read_text())["circuits"]
    for group,names in SELECTED.items():
        for name in names:
            relative=source_ref(group,name)
            path=AREA/"circuiti"/relative
            circuit=QuantumCircuit.from_qasm_file(str(path))
            flat=circuit.decompose(reps=10)
            measured=set()
            for item in flat.data:
                if item.operation.name in ("reset","if_else","while_loop","for_loop") or getattr(item.operation,"condition",None) is not None:
                    raise ValueError(f"{name}: operazioni dinamiche")
                if item.operation.name=="measure": measured.update(item.qubits)
                elif item.operation.name!="barrier" and measured.intersection(item.qubits):
                    raise ValueError(f"{name}: misure intermedie")
            value=sha(path.read_bytes())
            if value in hashes: raise ValueError(f"Duplicato: {name}")
            hashes.add(value)
            overlaps=[r["circuit_id"] for r in previous if r["source_sha256"]==value]
            if overlaps: raise ValueError(f"Sovrapposizione MQT: {name}: {overlaps}")
            low,high={"small":(2,10),"medium":(11,27),"large":(28,156)}[group]
            if not low<=circuit.num_qubits<=high: raise ValueError(f"Fascia errata: {name}")
            records.append(dict(circuit_id="qasmbench_"+name,size_group=group,
                source_ref=relative,source_sha256=value,split="external_test",
                qubits=circuit.num_qubits,depth=circuit.depth(),operations=circuit.size(),
                upstream_url=f"https://github.com/pnnl/QASMBench/blob/{REVISION}/{relative}",
                byte_identical_mqt_matches=overlaps))
    return dict(schema_version=1,repository="https://github.com/pnnl/QASMBench",revision=REVISION,
        counts={k:len(v) for k,v in SELECTED.items()},circuits=records,
        independence="Fonte esterna; nessun duplicato byte-identico nel corpus MQT. Non prova disgiunzione semantica o assenza dal preaddestramento LLM.",
        selection="Selezione ragionata prima degli score: famiglie diverse, circuiti statici, entro 156 qubit, nessuna variante transpiled; non campionamento casuale.",
        support_files={p:sha((AREA/"circuiti"/p).read_bytes()) for p in ("LICENSE","NOTICE","qelib1.inc","README.md")})
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--scarica",action="store_true")
    args=ap.parse_args()
    if args.scarica:
        paths=["LICENSE","NOTICE","qelib1.inc","README.md"]
        paths += [source_ref(g,n) for g,names in SELECTED.items() for n in names]
        with ThreadPoolExecutor(max_workers=8) as executor: list(executor.map(download,paths))
    manifest=inspect()
    out=AREA/"manifest.json"
    serialized=json.dumps(manifest,ensure_ascii=False,indent=2)+"\n"
    if out.exists() and out.read_text()!=serialized: raise ValueError("Manifest diverso; non sovrascritto")
    if not out.exists(): out.write_text(serialized,encoding="utf-8")
    print(json.dumps({"counts":manifest["counts"],"circuits":len(manifest["circuits"])}))
if __name__=="__main__": main()
