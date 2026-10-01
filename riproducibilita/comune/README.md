# Componenti condivisi del kit

| Modulo | Responsabilità |
| --- | --- |
| `settings.py` | Risolve percorsi, configurazione, output e contratti. |
| `corpus.py` | Verifica e congela i circuiti. |
| `processi.py` | Isola i lavori e conserva timeout, errori e riprese. |
| `llm.py` | Controlla identità del server, esegue decisioni e raccoglie misure. |
| `relazioni.py` | Genera documenti e tabelle dai risultati salvati. |
| `esporta.py` | Costruisce un prototipo autonomo con train e configurazione selezionata. |
| `controlli.py` | Verifica l'installazione del kit. |

`framework/` contiene i moduli dell'assistente usati dal kit; `scripts/` il supporto MQT; `template_export/` i componenti per i prototipi generati. Non sono collegamenti al prototipo distribuito o all'archivio. Il trasporto è `native` per server Linux e `windows` per il server del fisso raggiunto da WSL. Vedere la [mappa del flusso](../documentazione/mappa.md).
