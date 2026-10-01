# Codec TOON per il client

`codec.mjs` collega Python al pacchetto ufficiale `@toon-format/toon` 4.1.1. `package.json` e `package-lock.json` fissano la dipendenza; `node-lock.json` conserva i riferimenti del runtime. `node_modules/` viene installata localmente e non è nel clone.

Sono richiesti Node.js 22 e npm. Il setup Linux esegue `npm ci --ignore-scripts` e `app.py check` verifica un ciclo di codifica/decodifica. Node deve essere raggiungibile nel terminale del client, anche quando Qwen gira su un altro sistema operativo. In alternativa `PROTOTIPO_NODE` può indicare un eseguibile Node 22 Linux.

Seguire la [guida del prototipo](../../../docs/guida_passo_passo.md). La codifica conserva tutte le caratteristiche previste; non è un modo per tagliare il prompt quando la RAM o il contesto sono insufficienti.
