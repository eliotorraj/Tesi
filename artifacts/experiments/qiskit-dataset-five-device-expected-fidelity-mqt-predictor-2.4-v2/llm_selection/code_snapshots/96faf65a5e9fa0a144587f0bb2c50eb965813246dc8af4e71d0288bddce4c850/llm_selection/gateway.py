"""Collegamento locale Windows/WSL con richieste e flussi originali conservati."""
from __future__ import annotations
import json
import os
import subprocess
import time
from pathlib import Path
from .common import now, read_json, write_json, windows_path

CURL = "/mnt/c/Windows/System32/curl.exe"
BASE = "http://127.0.0.1:8089"

def request(endpoint, payload, directory, *, timeout=120):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    write_json(directory/"request.json", payload)
    started_at = now()
    started = time.perf_counter()
    command = [CURL, "--silent", "--show-error", "--fail-with-body", "--max-time", str(timeout),
               "--header", "Content-Type: application/json", "--data-binary",
               "@"+windows_path(directory/"request.json"), BASE+endpoint]
    result = subprocess.run(command, capture_output=True, timeout=timeout+15)
    (directory/"response.json").write_bytes(result.stdout)
    (directory/"stderr.txt").write_bytes(result.stderr)
    write_json(directory/"transport.json", {"started_at":started_at,"ended_at":now(),"elapsed_seconds":time.perf_counter()-started,"curl_exit_code":result.returncode})
    if result.returncode:
        raise RuntimeError(f"Local HTTP error {result.returncode}: {result.stdout[:1000]!r}")
    return json.loads(result.stdout)

def native_payload(chat_payload, audit_directory):
    """Applica il modello di chat nativo una volta, poi genera con lo schema."""
    excluded={"messages","chat_template_kwargs","reasoning_effort","reasoning_format","response_format","stream_options","max_tokens"}
    result={key:value for key,value in chat_payload.items() if key not in excluded}
    result.update(prompt=read_json(Path(audit_directory)/"template"/"response.json")["prompt"],
                  json_schema=chat_payload["response_format"]["schema"],n_predict=chat_payload["max_tokens"],return_tokens=True)
    return result

def generate(payload, directory, *, timeout):
    """Una chiamata sola. Nessun nuovo tentativo automatico del trasporto."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    write_json(directory/"request.json", payload)
    started_at = now()
    started = time.perf_counter()
    command = [CURL, "--silent", "--show-error", "--fail-with-body", "--no-buffer",
               "--max-time", str(timeout), "--header", "Content-Type: application/json",
               "--data-binary", "@"+windows_path(directory/"request.json"), BASE+"/completion"]
    content, reasoning, usage, timings, finish, first, first_any = "", "", None, None, None, None, None
    done, parse_errors, server_errors = False, [], []
    final_event = None
    with (directory/"stderr.txt").open("wb") as stderr, (directory/"stream.jsonl").open("w",encoding="utf-8") as output:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=stderr)
        try:
            for raw in iter(process.stdout.readline, b""):
                elapsed = time.perf_counter()-started
                line = raw.decode("utf-8",errors="replace").rstrip("\r\n")
                output.write(json.dumps({"elapsed_seconds":elapsed,"line":line},ensure_ascii=False)+"\n")
                output.flush()
                os.fsync(output.fileno())
                if not line.startswith("data: "):
                    continue
                data = line[6:]
                if data == "[DONE]":
                    done = True
                    continue
                try:
                    event = json.loads(data)
                except json.JSONDecodeError as error:
                    parse_errors.append(str(error))
                    continue
                if event.get("error"):
                    server_errors.append(event["error"])
                if "content" in event:
                    answer = event.get("content") or ""
                    if answer and first is None: first = elapsed
                    if answer and first_any is None: first_any = elapsed
                    content += answer
                    if event.get("stop") is True:
                        done = True
                        final_event = event
                        finish = event.get("stop_type")
                        usage = {"prompt_tokens":event.get("tokens_evaluated"),"completion_tokens":event.get("tokens_predicted"),"cached_tokens":event.get("tokens_cached")}
                        if event.get("truncated") is True: server_errors.append({"type":"context_truncated"})
                if event.get("usage"):
                    usage = event["usage"]
                if event.get("timings"):
                    timings = event["timings"]
                for choice in event.get("choices",[]):
                    delta = choice.get("delta",{})
                    answer = delta.get("content") or ""
                    thought = delta.get("reasoning_content") or delta.get("reasoning") or ""
                    if answer and first is None: first = elapsed
                    if (answer or thought) and first_any is None: first_any = elapsed
                    content += answer
                    reasoning += thought
                    if choice.get("finish_reason"): finish = choice["finish_reason"]
            code = process.wait(timeout=15)
        except BaseException:
            process.terminate()
            process.wait(timeout=15)
            write_json(directory/"interrupted.json",{"at":now(),"elapsed_seconds":time.perf_counter()-started})
            raise
    result = {"started_at":started_at,"ended_at":now(),"elapsed_seconds":time.perf_counter()-started,
              "ttft_content_seconds":first,"ttft_any_seconds":first_any,"content":content,"reasoning":reasoning,
              "usage":usage,"timings":timings,"finish_reason":finish,"stream_done":done,
              "curl_exit_code":code,"stream_parse_errors":parse_errors,"server_errors":server_errors,
              "transport_retries":0,"server_final":final_event}
    result["transport_success"] = code == 0 and done and not parse_errors and not server_errors
    write_json(directory/"response.json",result)
    return result

class LocalLlmGateway:
    """Adattatore del prototipo: una richiesta, stessi vincoli e registri delle prove."""
    def __init__(self, directory, configuration, context_limit, timeout):
        self.directory=Path(directory)
        self.configuration=configuration
        self.context_limit=context_limit
        self.timeout=timeout

    def generate(self, prompt):
        from uuid import uuid4
        from .configuration import payload
        directory=self.directory/str(uuid4())
        from prototype.prompting.minimal import audit as encoding_audit
        request_payload=payload(prompt.payload,self.configuration)
        encoding=encoding_audit(prompt.payload)
        write_json(directory/"encoding.json",encoding)
        write_json(directory/"prompt.json",prompt.payload)
        count=audit_tokens(request_payload,directory/"audit")
        if count+request_payload["max_tokens"]>self.context_limit:
            write_json(directory/"context_failure.json",{"input_tokens":count,"limit":self.context_limit,"llm_calls":0})
            raise ValueError("Full prompt exceeds context; no inference performed")
        result=generate(native_payload(request_payload,directory/"audit"),directory/"call",timeout=self.timeout)
        if not result["transport_success"]: raise RuntimeError("Local generation failed; see durable call record")
        canonical=result["content"]  # Citation resolution belongs to the request-bound validator.
        write_json(directory/"canonical_response.json",canonical)
        return canonical

def audit_tokens(payload, directory):
    formatted = request("/apply-template", {k:payload[k] for k in ("messages","chat_template_kwargs","reasoning_effort")}, Path(directory)/"template")
    tokens = request("/tokenize", {"content":formatted["prompt"],"add_special":False,"parse_special":True}, Path(directory)/"tokenizer")
    return len(tokens["tokens"])
