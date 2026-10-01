# Registro delle verifiche di sviluppo

Primo controllo: la preparazione a 10 esempi si è fermata prima di qualsiasi
inferenza. Il costruttore del prompt applicava ancora il limite E1-E5 dello
schema intermedio. È stato esteso anche quel passaggio con un parametro
esplicito, lasciando il valore predefinito a 5.

Secondo controllo: 7 verifiche superate, 1 confronto TOON da correggere.
Il controllo confrontava tuple Python con liste JSON; ora confronta la
vista JSON normalizzata, come fa già il codificatore. Nessun dato perso.

Verifica finale: tutte le 38 prove automatiche superate (8 nuove).
I due avvii --verifica sono pronti. Prompt, schema, vista e audit a k=5
coincidono con il riferimento precedente. Nessuna chiamata LLM o
valutazione di circuiti Test reali; sono state eseguite compilazioni
di Bell previste dalle regressioni esistenti. Grafo non aggiornato.
