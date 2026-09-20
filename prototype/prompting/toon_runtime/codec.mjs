import { readFileSync } from 'node:fs';
import { encode, decode } from '@toon-format/toon';
const pkg = JSON.parse(readFileSync(new URL('./node_modules/@toon-format/toon/package.json', import.meta.url), 'utf8'));
if (pkg.version !== '4.1.1') throw new Error('Expected @toon-format/toon 4.1.1');
const job = JSON.parse(readFileSync(0, 'utf8'));
if (job.operation === 'decode') {
  process.stdout.write(JSON.stringify(decode(job.text, { strict: true, indentSize: 2 })));
} else if (job.operation === 'encode') {
  const text = encode(job.value, { indentSize: 2, delimiter: job.delimiter ?? ',' });
  process.stdout.write(JSON.stringify({text, decoded: decode(text, {strict: true, indentSize: 2})}));
} else throw new Error('Unknown TOON operation');
