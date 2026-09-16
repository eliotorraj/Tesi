# Pubblicazione GitHub — stato del 15 settembre 2026

**Documento storico.** Conserva le istruzioni e le osservazioni della consegna
originaria. I comandi di aggiunta, commit e push sotto riportati descrivono quel
momento: non sono una procedura da rieseguire alla cieca sullo stato corrente.
La riorganizzazione della documentazione ha cambiato alcuni percorsi.
Per l'orientamento attuale partire dal [README generale](../../README.md).

## Istruzioni della consegna originaria

Il codice nuovo è nella cartella di lavoro sul ramo
`codex/experiment-v2-mqt-2.4.0`. Per pubblicare insieme la procedura LLM,
le correzioni e la documentazione, usare Ubuntu:

```bash
cd /home/elio/Tesi-mqt-2.4-v2
git status --short
git add llm_selection tests/test_llm_selection.py tests/test_compact_prompt.py \
  docs/protocollo_sperimentale.md qiskit_dataset/experiment_v2.py \
  scripts/14_evaluate_methods_v2.py scripts/15_release_test_v2.py
git diff --cached --stat
git diff --cached --check
git commit -m "Clarify and compact LLM prompts with evidence validation and train checks"
git push origin codex/experiment-v2-mqt-2.4.0
```

I file della procedura LLM erano ancora da aggiungere a Git: per questo
il comando include tutta la cartella e le integrazioni già presenti.
Controllare il riepilogo prima del commit.

Le modifiche personali già presenti in `AGENTS.md` e `.gitignore` non sono
incluse nel comando. La modifica attuale di `.gitignore` riguarda proprio
`AGENTS.md`: aggiungere un file già tracciato a questo elenco non smette
automaticamente di tracciarlo.

Il push aggiorna il ramo di sviluppo. Per portare il codice su `main`,
aprire una richiesta di integrazione da
[questa pagina di confronto](https://github.com/eliotorraj/Tesi/compare/main...codex/experiment-v2-mqt-2.4.0).
Gli artefatti grandi sotto `artifacts/experiments/` restano esclusi da Git.
Il riepilogo leggero sotto `llm_selection/reports/` viene invece pubblicato.

Per conservare integralmente gli esperimenti occorre anche una copia della
cartella degli artefatti. Il commit del codice non include prompt completi,
flussi delle risposte, registri del server o pesi.

## Rimozione dei vecchi modelli RL già pubblicata

Il 15 settembre 2026 sono stati pubblicati due commit normali:

| Ramo | Commit | Operazione |
| --- | --- | --- |
| main | `bf77df56c69f34294d60e5f2ed87cd4931ca5d20` | Rimuove 48 archivi RL e ne esclude il nuovo caricamento |
| mqt-predictor-2.4.0 | `1b6ab73edd366154036ae59f6b62374c7ab74fd3` | Stessa rimozione |

I percorsi riguardano solo `artifacts/models/rl/*.zip` e i vecchi checkpoint
sotto `artifacts/checkpoints/rl/`. Gli altri rami remoti attivi non li contenevano.
Le copie locali, i dati scientifici e gli artefatti dell'esperimento corrente
sono conservati. Il modello supervisionato presente sul vecchio ramo è rimasto.

I 48 percorsi rinviavano a 44 oggetti LFS distinti, per **55.308.918.141 byte**,
circa 55,3 GB decimali. La somma per percorso era maggiore perché alcuni file
rinviavano allo stesso oggetto.

**Questa rimozione non recupera automaticamente 55,3 GB di quota GitHub LFS.**
Gli oggetti nella cronologia continuano a occupare spazio remoto. La
[documentazione GitHub](https://docs.github.com/en/repositories/working-with-files/managing-large-files/removing-files-from-git-large-file-storage)
indica di rivolgersi al supporto per eliminare gli oggetti quando si vuole
conservare il repository. La cancellazione e ricreazione del repository
è un'operazione diversa, con perdita di informazioni associate, e non è stata
eseguita. Non sono stati effettuati riscritture della cronologia o push forzati.

Per il supporto sono disponibili elenco degli oggetti, dimensioni, rami e prove
del push sotto `$LLM_OUTPUT/analyses/prompt_v2/`:
`remote_models_before.json`, `git_cleanup_prepared.json` e
`git_cleanup_push.json`.
