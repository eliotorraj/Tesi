# Rimozione di Git LFS — 15 settembre 2026

## Che cosa cambia

I dati pesanti vengono conservati fuori da Git e trasferiti manualmente con Drive.
La pulizia riguarda tutti i rami e il tag. I nomi dei rami restano invariati.
Non viene eseguito un merge tra il ramo corrente e main.

Sono stati rimossi dalla cronologia 102 percorsi: tutti quelli
contenenti riferimenti LFS, comprese le versioni precedenti, e i file Git oltre
100 MiB. Le regole LFS sono state tolte da .gitattributes.
L'elenco completo è in percorsi_esclusi.txt e in .gitignore.

Il codice, il protocollo, il corpus storico sotto archivio/ e tutti gli altri
file non selezionati conservano il loro contenuto originale.
Clonare il repository non ripristina i dati esterni richiesti dal programma.

## Copie di sicurezza

Sul PC della pulizia, volude D: Tesi-mqt/.lfs-maintenance/20260915-removal/ contiene:

- original-git/: copia di Git e degli oggetti LFS disponibili.
- analysis.git/: cronologia originale, inclusi i riferimenti delle pull request.
- dati-per-drive.tar.gz: gli otto file pesanti del ramo corrente, nei percorsi originali.
- working-files-before.json: dimensioni e SHA-256 dei file nelle due cartelle di lavoro.
- inventory.json, verification.json, procedure e registri delle operazioni.

L'archivio per Drive conserva circa 1,08 GB di dati, compressi in circa 110 MB.
Ogni file è stato verificato rileggendo l'archivio e confrontando lo SHA-256.
I file originali restano nelle cartelle di lavoro.

L'inventario identifica 77 oggetti LFS distinti: 29
disponibili su questo PC e 48 mancanti localmente.
Tutte le copie disponibili sono state verificate tramite SHA-256.
Le dimensioni dei puntatori non misurano la quota effettiva su GitHub.

## Verifiche

Sono stati confrontati tutti i 67 commit riscritti.
Sono ammesse solo le cancellazioni previste e la rimozione delle regole LFS.
Autori, date e messaggi sono conservati. Gli identificativi dei commit cambiano.
Non restano puntatori LFS né file Git oltre 100 MiB nella cronologia riscritta.
La struttura Git è stata controllata con git fsck --full.
Un successivo commit aggiunge questo resoconto e le esclusioni da Git.
Non sono stati eseguiti nuovi esperimenti né modificati risultati sperimentali.

## Trasferimento sull'altro PC

1. Salvare eventuali modifiche non pubblicate.
2. Clonare di nuovo il repository dopo la pubblicazione della cronologia pulita.
3. Selezionare il ramo desiderato.
4. Trasferire dati-per-drive.tar.gz ed estrarlo nella radice del progetto.
5. Conservare i percorsi originali. I file restano esclusi da Git.

Non fare merge o push dalla vecchia copia senza riallinearla: si rischia di
reintrodurre la cronologia con LFS.
L'archivio comprende solo gli otto file rimossi dal ramo corrente. I modelli
gia esclusi da Git e gli altri dati locali vanno trasferiti separatamente.

## GitHub Support

La riscrittura non libera automaticamente la quota LFS sul server.
Support deve valutare la cancellazione degli oggetti memorizzati.
I quattro riferimenti refs/pull/1/head fino a refs/pull/4/head sono gestiti da
GitHub: non sono sovrascrivibili con un normale push e vanno segnalati.
La richiesta pronta è in richiesta_supporto.md. Non è stata inviata.

Documentazione: https://docs.github.com/en/repositories/working-with-files/managing-large-files/removing-files-from-git-large-file-storage
