# Impostazioni dell'editor

`settings.json` apre i grandi file JSONL globali come normali file di testo.
È una preferenza di Visual Studio Code; non cambia gli esperimenti o i dati.

## Compilazione della tesi

`tasks.json` aggiunge **Tesi: compila PDF**. Eseguire il comando da VS Code
aperto in WSL. Usa la ricetta `tesi/latexmkrc`, ignora configurazioni personali
incompatibili e produce `tesi/build/main.pdf`.
