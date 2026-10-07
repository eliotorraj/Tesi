# Shared toolkit components

| Module or directory | Purpose |
| --- | --- |
| `settings.py` | Resolve configuration, paths, output roots and contracts. |
| `configuratore.py`, `configuratore_cli.py`, `configuratore_info.py` | Create, revise and inspect named experiments. |
| `corpus.py` | Check and freeze circuit inputs. |
| `processi.py` | Isolate jobs and record timeouts, failures and resumes. |
| `llm.py`, `opzioni_server.py` | Validate server identity, execute decisions and resolve options. |
| `relazioni.py` | Generate reports and tables. |
| `esporta.py` | Package standalone prototypes. |
| `controlli.py`, `stato.py` | Check installation and summarize phases. |
| `framework/` | Toolkit-local assistant and prompt code. |
| `scripts/` | MQT support code. |
| `template_export/` | Runtime components for exported prototypes. |

These are local implementations. Linux servers use `native` transport; the original Windows server can be reached from WSL with explicit `windows` transport. See the [module map](../documentazione/mappa.md).

Named configurations do not change other experiments' global source fingerprints. Each run has its own contract; executable source changes remain subject to integrity checks.
