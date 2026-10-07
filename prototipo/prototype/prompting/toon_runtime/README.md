# Client TOON codec

`codec.mjs` connects Python to `@toon-format/toon` 4.1.1. `package.json` and `package-lock.json` pin the package; `node-lock.json` records the runtime reference.

Linux setup runs `npm ci --ignore-scripts`; `app.py check` verifies encoding and decoding. Node.js 22 must be available to the client. `PROTOTIPO_NODE` can select a Linux Node.js executable. Follow the [prototype guide](../../../docs/guida_passo_passo.md). TOON preserves the defined feature content and does not truncate oversized prompts.
