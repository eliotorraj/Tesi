"""Narrazione e tabelle del confronto finale, derivate dagli esiti conservati."""
from pathlib import Path
from dati import METHODS, number
from impaginazione import esc, fmt, table
from pannelli import PANEL_LABELS, threshold_counts, metric_grid, reliability_grid, threshold_grid, ecdf_grid, figure_page, method_order

HERE=Path(__file__).resolve().parent


def label(method, runs):
    value=PANEL_LABELS[method]
    if runs.get(method,{}).get('source',{}).get('exploratory'):
        value+=' (espl.)'
    return esc(value)


def discrete(value):
    # Una media non intera di repliche resta una media: non viene troncata.
    if number(value) and float(value).is_integer():
        return fmt(value,0)
    return fmt(value,2)


def headers(methods, runs):
    values={'llm_rag':r'\shortstack{LLM +\\RAG}',
            'llm_senza_rag':r'\shortstack{LLM no\\RAG}',
            'mqt_predictor':r'\shortstack{MQT\\Predictor}',
            'random':'Random', 'llm_recupero_random':r'\shortstack{LLM +\\Random\\RAG\\(espl.)}'}
    if runs.get('mqt_predictor',{}).get('source',{}).get('exploratory'):
        values['mqt_predictor']=r'\shortstack{MQT\\Predictor\\(espl.)}'
    return [values[m] for m in methods]


def matrix(rows, runs, methods=None):
    methods=methods or [m for m in method_order(runs) if m in runs]
    # Nomi completi e stessa posizione per le colonne di ogni riepilogo.
    spec=r'>{\raggedright\arraybackslash}p{5.0cm}' + r'>{\centering\arraybackslash}p{1.9cm}'*len(methods) if len(methods)==5 else r'>{\raggedright\arraybackslash}p{5.8cm}' + r'>{\centering\arraybackslash}p{2.2cm}'*len(methods)
    return table(['Misura']+headers(methods,runs),rows,spec=spec,size='small')


def mqt_details(runs):
    run=runs.get('mqt_predictor',{})
    if not run:
        return 'I risultati MQT non sono ancora disponibili in questa versione.\n'
    detail=''
    md=run.get('report_model_metadata',{})
    classifier=md.get('classifier',{})
    if classifier:
        detail+=('Il selettore è una Random Forest con '+str(classifier['n_estimators'])+
                 ' alberi, pesi delle classi bilanciati, seme '+str(classifier['random_state'])+
                 ' e '+str(classifier['n_jobs'])+' processi. ')
        if classifier.get('hyperparameter_search') is False:
            detail+='Questi parametri sono stati fissati senza una ricerca degli iperparametri sulla validation. '
        detail+='\n\n'
    source=run.get('source',{})
    if source.get('exploratory'):
        d=source['details']
        detail+=(r'\textbf{La prova MQT qui riportata è esplorativa.} '
            f"Il selettore usa {d['training_samples']} dei {d['expected_training_samples']} campioni train previsti; "
            f"{d['excluded_samples']} sono esclusi. La raccolta contiene "
            f"{d['successful_compilations']} compilazioni riuscite su {d['required_compilations']} coppie previste. ")
        if md.get('learned_classes'):
            detail+=f"Le classi apprese sono {len(md['learned_classes'])}: Falcon 127, Heron 133, Heron 156 e Quantinuum H2-56. Falcon 27 non compare fra i vincitori del Training set, pur avendo la propria politica RL. "
        detail+=('La raccolta comprende tentativi a 100 secondi e recuperi a 300 secondi. '
            'Il Test mantiene invece il limite di 100 secondi e il comportamento RL originale. '
            'Questa prova usa un contratto separato e non completa la valutazione conforme al contratto originale. '
            'Il confronto con MQT va letto entro questo limite; quelli fra gli altri tre sistemi mantengono il piano originale.\n')
    return detail


def summary_tables(runs, comparison, plan):
    methods=[m for m in method_order(runs) if m in runs]
    summaries={m:r['summary'] for m,r in runs.items()}
    def count(key):return [s[key] for s in (summaries[m] for m in methods)]
    def stat(key,which='mean',digits=3):
        return [fmt(summaries[m]['metrics'].get(key,{}).get(which),digits) for m in methods]
    body=r'\clearpage\section{Risultati}'+'\n'+r'\subsection{Riuscita e qualità: i dati di insieme}'+'\n'
    body+=('Le tabelle raccolgono prima i risultati principali. Ogni circuito ha lo stesso peso. '
           'Lo score medio considera soltanto le compilazioni riuscite: quando cambiano i successi, '
           'cambia anche l’insieme su cui è calcolato. Un fallimento non riceve uno score uguale a zero. '
           'Per un confronto diretto della qualità useremo quindi i circuiti riusciti per entrambi i sistemi.\n\n')
    rows=[['Circuiti previsti']+count('expected_circuits'),['Circuiti conclusi']+count('completed_circuits'),
          ['Compilazioni riuscite']+count('successes'),['Fallimenti']+count('failures'),['Circuiti pendenti']+count('pending'),
          ['Score medio sui successi']+stat('score',digits=6),
          ['Score mediano sui successi']+stat('score','median',6)]
    body+=matrix(rows,runs)
    thresholds={m:threshold_counts(runs[m]) for m in methods}
    body+=('La soglia 0,8 offre una seconda lettura: quanti dei circuiti previsti ottengono '
           'una compilazione valida con score almeno pari a questo valore. Il denominatore comprende '
           'anche i fallimenti; i casi senza score restano distinti dai successi sotto soglia. '
           'È una descrizione aggiunta per questo report, non una soglia scelta prima del Test.\n')
    body+=matrix([
        [r'Circuiti con score $\geq 0{,}8$']+[f"{thresholds[m]['high']}/{thresholds[m]['total']}" for m in methods],
        ['Percentuale sul Test']+[fmt(100*thresholds[m]['high']/thresholds[m]['total'],1)+r'\%' if thresholds[m]['total'] else '--' for m in methods]
    ],runs)
    failures=[label(m,runs)+': '+str(summaries[m]['failures']) for m in methods if summaries[m]['failures']]
    if failures:
        body+='I fallimenti osservati sono '+', '.join(failures)+'. '
        if all(set(summaries[m]['failure_causes']) <= {'process_timeout'} for m in methods):
            body+='In tutti questi casi il processo ha superato il limite di tempo. '
    body+='I dettagli e le misure mancanti rimangono visibili nell’appendice.\n'

    body+=r'\clearpage\subsection{Tempi e costo delle risposte}'+'\n'
    body+=('Il tempo totale misura il percorso dal circuito all’esito, compresi scelta, risposte, '
           'correzioni e compilazione. Il tempo interno riguarda soltanto il lavoro del compilatore. '
           'Il tempo del processo comprende anche avvio e controlli. I timeout entrano nel tempo totale '
           'e nel tempo del processo quando misurati, ma non ricevono una durata interna inventata.\n')
    rows=[]
    for key,title in [('total_seconds','Tempo totale'),('compilation_seconds','Compilazione interna'),
                      ('compilation_process_seconds','Processo di compilazione'),('choice_seconds','Preparazione e scelta')]:
        rows.extend([[title+' medio (s)']+stat(key,digits=2),
                     [title+' mediano (s)']+stat(key,'median',2),
                     ['Circuiti con misura']+[f"{summaries[m]['metrics'][key]['n']}/{summaries[m]['completed_circuits']}" for m in methods]])
    body+=matrix(rows,runs)
    llms=[m for m in methods if m.startswith('llm')]
    if llms:
        body+=('I token sommano ingresso e uscita di tutte le chiamate, comprese le correzioni. '
               'Una correzione è una richiesta aggiuntiva al modello, non una nuova compilazione. '
               'Questi costi non si applicano a MQT e Random.\n')
        rows=[]
        for key,title in [('input_tokens','Token in ingresso'),('output_tokens','Token in uscita'),
                          ('total_tokens','Token complessivi'),('llm_calls','Chiamate'),('retries','Correzioni')]:
            rows.append([title+' (somma)']+[discrete(summaries[m]['metrics'][key]['sum_known']) for m in llms])
        rows.append(['Circuiti con correzioni']+[summaries[m]['episodes_with_retry'] for m in llms])
        rows.append(['Accettati con fatti non verificati']+[summaries[m]['accepted_with_unverified_facts'] for m in llms])
        rows.append(['Tempo medio delle risposte (s)']+[fmt(summaries[m]['metrics']['llm_response_seconds']['mean']) for m in llms])
        rows.append(['Circuiti con misura dei token']+[f"{summaries[m]['metrics']['total_tokens']['n']}/{summaries[m]['completed_circuits']}" for m in llms])
        body+=matrix(rows,runs,llms)
        body+='Le medie non intere dei conteggi, quando riportate, restano medie; i conteggi effettivi sono scritti come interi.\n'

    body+=r'\clearpage\subsection{Confronti sugli stessi circuiti}'+'\n'
    body+=('Per confrontare LLM + RAG con ciascun concorrente consideriamo solo i circuiti con '
           'score disponibile per entrambi. La differenza è lo score RAG meno lo score dell’altro sistema. '
           'Un valore positivo indica una qualità stimata maggiore per RAG. '
           'Questa analisi non sostituisce il conteggio dei fallimenti.\n')
    pairs=comparison['pairs'];others=[m for m in method_order(runs) if m in pairs]
    spec=r'>{\raggedright\arraybackslash}p{5.0cm}'+r'>{\centering\arraybackslash}p{2.4cm}'*len(others)
    rows=[
        ['Circuiti riusciti in comune']+[pairs[m]['n'] for m in others],
        ['Score medio LLM + RAG']+[fmt(pairs[m]['mean_left'],6) for m in others],
        ['Score medio del sistema in colonna']+[fmt(pairs[m]['mean_right'],6) for m in others],
        ['Differenza media (RAG meno altro)']+[fmt(pairs[m]['mean_difference'],6) for m in others],
        ['Limite inferiore, intervallo 95\\%']+[fmt(pairs[m]['paired_bootstrap_95'][0],6) if pairs[m]['paired_bootstrap_95'] else '--' for m in others],
        ['Limite superiore, intervallo 95\\%']+[fmt(pairs[m]['paired_bootstrap_95'][1],6) if pairs[m]['paired_bootstrap_95'] else '--' for m in others],
        ['RAG ha score maggiore']+[pairs[m]['wins'] for m in others],
        ['Score uguale']+[pairs[m]['ties'] for m in others],
        ['RAG ha score minore']+[pairs[m]['losses'] for m in others]]
    if others:
        body+=table(['Confronto con LLM + RAG']+headers(others,runs),rows,spec=spec,size='small')
    body+=(f"L’intervallo descrive la variazione fra i circuiti osservati: usa {plan['analysis']['bootstrap_draws']} "
           f"ricampionamenti delle coppie, con seme {plan['analysis']['bootstrap_seed']}, "
           'e i percentili 2,5 e 97,5. Non è una prova confermativa di superiorità '
           'e non misura la variabilità di nuove esecuzioni.\n\n')
    common=len(comparison['all_common_successes'])
    body+=f"I successi comuni a tutti i sistemi presenti sono {common}. Le medie su questo stesso insieme sono:\n"
    body+=matrix([['Score medio sui successi comuni']+[fmt(comparison['all_common_means'].get(m),6) for m in methods]],runs)
    body+=('I grafici che seguono mantengono sempre lo stesso ordine: LLM + RAG in alto a sinistra, '
           'LLM no RAG in alto a destra, MQT in basso a sinistra e Random in basso a destra. '
           'Nei grafici per circuito, la posizione orizzontale segue l’ordine alfabetico dei nomi in appendice. '
           'Gli assi usano la stessa scala nei quattro pannelli e una misura assente non diventa zero.\n')
    if 'llm_recupero_random' in runs:
        body=body.replace('MQT in basso a sinistra e Random in basso a destra.',
            'MQT nella seconda riga a sinistra, Random nella seconda riga a destra e LLM + Random RAG centrato nella terza riga.')
        body=body.replace('nei quattro pannelli','nei cinque pannelli')
        body+='Il confronto con gli esempi casuali è esplorativo: la variante è stata aggiunta dopo la lettura del Test, con un solo seme di recupero.\n'
    return body


def chart_pages(output,runs):
    s={m:r['summary'] for m,r in runs.items()}
    def page(*args):
        return figure_page(*args, five='llm_recupero_random' in runs)
    body=''
    reliability_grid(output,runs)
    text=('La riuscita mostra se il sistema arriva a un circuito compilato valido. '
          'Le barre distinguono successi, fallimenti e casi ancora pendenti. '
          'Il confronto riguarda tutti i circuiti previsti, quindi rende visibili anche i casi '
          'che non entrano nelle medie dello score.')
    if all(m in s for m in METHODS):
        text+=f" I due LLM completano {s['llm_rag']['successes']} e {s['llm_senza_rag']['successes']} compilazioni; MQT ne completa {s['mqt_predictor']['successes']} e Random {s['random']['successes']}."
    if 'llm_recupero_random' in s:
        text+=f" LLM + Random RAG completa {s['llm_recupero_random']['successes']} compilazioni."
    body+=page('esiti','Quanti circuiti arrivano a una compilazione valida',text,
                      'Riuscita sui circuiti previsti. MQT indica la prova esplorativa quando così specificato nel pannello.')
    threshold_grid(output,runs)
    counts={m:threshold_counts(r) for m,r in runs.items()}
    text=('Ogni torta rappresenta l’intero Test, con '+str(next(iter(counts.values()))['total'])+
          ' circuiti. Il blu indica uno score almeno pari a 0,8; l’arancione uno score inferiore; '
          'il grigio un caso senza score. Un caso pendente, se presente, è indicato separatamente. '
          'In questo modo qualità e copertura si leggono con lo stesso denominatore. ')
    text+='; '.join(PANEL_LABELS[m]+f": {c['high']}/{c['total']}" for m,c in counts.items())+'.'
    body+=page('soglia_score_080','Quanti circuiti raggiungono uno score di almeno 0,8',text,
                      'Percentuali sui circuiti previsti, senza assegnare uno score ai fallimenti. La soglia è descrittiva.')
    charts=[
        ('score','Qualità delle compilazioni','Score',
         'Ogni punto mostra lo score di un circuito riuscito. La separazione in quattro pannelli permette di osservare '
         'la distribuzione dei valori senza sovrapporre i sistemi. Le posizioni prive di un punto corrispondono a uno '
         'score non disponibile; non indicano qualità nulla. Per stabilire quante volte RAG migliora una scelta '
         'valgono i confronti appaiati delle tabelle precedenti.',
         'Score sui successi; scala comune da 0 a 1.'),
        ('total_seconds','Tempo necessario per arrivare all’esito','Tempo totale (s)',
         'Il tempo totale è il costo di esecuzione osservato per ciascun circuito e comprende anche i fallimenti. '
         'I casi vicini al limite di tempo rendono visibili le attese più onerose. Media e mediana aiutano a distinguere '
         'il costo complessivo da quello tipico di un circuito.',
         'Tempi totali misurati in secondi, inclusi i casi falliti.'),
        ('compilation_seconds','Tempo impiegato dal compilatore','Compilazione interna (s)',
         'Qui isoliamo il tempo interno del compilatore, lasciando fuori la scelta del dispositivo e la risposta LLM. '
         'Per un processo interrotto dal limite esterno può mancare questa misura. I punti assenti di MQT e Random '
         'non devono quindi essere letti come compilazioni istantanee, né confrontati come se tutti i sistemi '
         'avessero completato gli stessi casi.',
         'Durata interna sulle sole misure disponibili; i timeout senza misura restano assenti.'),
        ('compilation_process_seconds','Durata del processo di compilazione','Processo di compilazione (s)',
         'Il processo comprende l’avvio, il lavoro del compilatore e i controlli finali. A differenza della misura '
         'interna, questa durata rende visibili anche i timeout registrati dall’esterno. La differenza rispetto '
         'al grafico precedente aiuta a capire quanto pesano i casi che non producono una compilazione valida.',
         'Durata del processo in secondi, compresi i timeout misurati.'),
        ('total_tokens','Quantità di testo elaborata dagli LLM','Token totali',
         'Il conteggio somma i token di ingresso e uscita di tutte le chiamate relative allo stesso circuito. '
         'Gli esempi del RAG aumentano il testo in ingresso; le richieste di correzione aggiungono ulteriori chiamate. '
         'I token descrivono il volume di testo elaborato, non un costo monetario. Per MQT e Random questa misura '
         'non si applica.',
         'Token complessivi per circuito; le celle non applicabili restano nella posizione prevista.'),
        ('llm_response_seconds','Attesa delle risposte degli LLM','Tempo delle risposte (s)',
         'Per ciascun circuito sommiamo il tempo trascorso fra invio e ricezione completa di tutte le risposte LLM. '
         'Il grafico separa così questa attesa dalla compilazione e dal recupero degli esempi. La presenza del RAG '
         'si accompagna a risposte mediamente più lente in questa esecuzione, ma il Test non permette di attribuire '
         'tutta la differenza a una singola causa.',
         'Tempo cumulativo delle risposte in secondi; nessuna misura LLM per MQT e Random.'),
        ('retries','Richieste di correzione prima della compilazione','Correzioni',
         'Una correzione è una chiamata oltre la prima nello stesso caso. Serve a ottenere una risposta accettabile '
         'e non ripete la compilazione quantistica. I picchi mostrano dove aumentano le chiamate e, di conseguenza, '
         'anche token e attesa. La riuscita della compilazione non certifica comunque la spiegazione libera del modello.',
         'Numero di correzioni per circuito; zero significa che è bastata la prima risposta.')
    ]
    if 'llm_rag' in s and 'llm_senza_rag' in s:
        a=s['llm_rag']['metrics']['total_seconds']['mean'];b=s['llm_senza_rag']['metrics']['total_seconds']['mean']
        if number(a) and number(b) and b:
            charts[1]=(charts[1][0],charts[1][1],charts[1][2],
                       charts[1][3]+f" RAG richiede in media {fmt(a)} s contro {fmt(b)} s senza esempi: circa {fmt(a/b)} volte tanto.",
                       charts[1][4])
    for metric,title,ylabel,prose,caption in charts:
        if metric in ('total_tokens','llm_response_seconds','retries') and not any(m.startswith('llm') for m in runs):
            continue
        metric_grid(output,runs,metric,ylabel)
        if 'llm_recupero_random' in runs:
            prose=prose.replace('quattro pannelli','cinque pannelli')
        body+=page(metric,title,prose,caption)
    ecdf_grid(output,runs)
    body+=page('distribuzione_score','Come si distribuiscono gli score',
         'La curva indica la quota di compilazioni riuscite con score non superiore al valore letto sull’asse orizzontale. '
         'Un aumento vicino a 1 segnala molti risultati di qualità stimata elevata. Ogni pannello considera soltanto '
         'i successi del proprio sistema: i denominatori sono scritti sugli assi e possono essere diversi. '
         'Questa figura descrive la forma delle distribuzioni; non sostituisce il confronto sugli stessi circuiti.',
         'Distribuzioni cumulative sui successi, con scale comuni.')
    return body


def conclusions(runs, comparison):
    body=r'\clearpage\section{Conclusioni}'+'\n'
    pairs=comparison['pairs']
    if 'llm_senza_rag' in pairs and 'random' in pairs:
        a,b=pairs['llm_senza_rag'],pairs['random']
        positive=a['wins']>a['n']/2 and b['wins']>b['n']/2
        body+=('L’esito è positivo per l’obiettivo di usare esempi di compilazione a supporto del modello linguistico. '
               if positive else 'I confronti appaiati permettono di valutare il contributo degli esempi al modello linguistico. ')
        body+=(f"LLM + RAG ottiene uno score maggiore in {a['wins']} dei {a['n']} confronti con LLM no RAG "
               f"e in {b['wins']} degli {b['n']} confronti con Random. ")
        if positive:
            body+='Gli esempi migliorano quindi la qualità stimata nella maggior parte dei confronti osservati. '
        body+='Questo risultato riguarda i circuiti confrontabili e va letto insieme ai fallimenti riportati separatamente.\n\n'
    s={m:r['summary'] for m,r in runs.items()}
    if 'mqt_predictor' in pairs:
        p=pairs['mqt_predictor'];a=s['llm_rag'];b=s['mqt_predictor']
        body+=(f"Sui {p['n']} successi comuni, RAG ha score medio {fmt(p['mean_left'],4)} "
               f"e MQT {fmt(p['mean_right'],4)}. "
               f"RAG produce però {a['successes']} compilazioni valide su {a['expected_circuits']} circuiti, "
               f"contro {b['successes']} di MQT. ")
        if a['successes']>b['successes']:
            body+='Offre dunque una maggiore copertura nel campione osservato. '
        body+='La riuscita su tutti i casi osservati, quando presente, è un’indicazione di affidabilità pratica, non una garanzia su qualsiasi circuito futuro.\n\n'
        ta=a['metrics']['total_seconds'];tb=b['metrics']['total_seconds']
        body+=(f"Anche il tempo medio totale è diverso: {fmt(ta['mean'])} s per RAG e {fmt(tb['mean'])} s per MQT. "
               f"La mediana è invece {fmt(ta['median'])} s per RAG e {fmt(tb['median'])} s per MQT. "
               'È quindi corretto descrivere il costo medio e l’effetto dei timeout, evitando di estendere '
               'la graduatoria a ogni circuito o a tutte le statistiche dei tempi. ')
        if runs['mqt_predictor']['source'].get('exploratory'):
            body+='Inoltre questi risultati MQT provengono dalla prova esplorativa con Training set incompleto descritta nella seconda sezione.'
        body+='\n\n'
    if 'llm_rag' in s and 'llm_senza_rag' in s:
        a=s['llm_rag']['metrics']['total_seconds']['mean'];b=s['llm_senza_rag']['metrics']['total_seconds']['mean']
        if number(a) and number(b) and b:
            body+=(f"Il miglioramento rispetto al modello senza esempi ha un costo: il tempo medio di RAG è {fmt(a/b)} "
                   'volte quello di LLM no RAG. Gli esempi, le correzioni e le compilazioni scelte contribuiscono '
                   'al percorso complessivo. Il Test mostra questo compromesso, senza isolare sperimentalmente '
                   'il peso causale di ciascuna componente.\n\n')
    body+=('LLM + RAG opera oggi entro un catalogo di sole dodici configurazioni Qiskit. '
           'Ampliare il catalogo e il Dataset potrebbe includere esempi e casi con compilazioni migliori. '
           'È una possibilità da verificare, non un miglioramento già dimostrato: aumenterebbero anche '
           'il costo della raccolta e la complessità della scelta.\n\n'
           'Un altro elemento da considerare è il criterio di qualità. La fedeltà attesa è una metrica '
           'integrata in MQT ed è anche l’obiettivo delle sue politiche di compilazione. Esiste quindi '
           'una coerenza fra addestramento e valutazione che aiuta a contestualizzare i risultati. '
           'La stessa metrica viene comunque applicata a tutti i sistemi e guida anche la valutazione '
           'degli esempi Qiskit: la sua origine, da sola, non dimostra una distorsione del confronto. '
           'Altre metriche o prove su hardware reale potrebbero produrre una graduatoria diversa.\n\n'
           'Il risultato è incoraggiante anche dal punto di vista della preparazione del sistema. '
           'Il RAG riusa un modello linguistico già disponibile e costruisce il proprio Dataset '
           'da compilazioni Qiskit, senza addestrare una politica RL per ogni dispositivo. '
           'MQT richiede invece le politiche RL e il Training set del selettore supervisionato. '
           'Questa differenza riduce gli oneri di addestramento specifici del nostro approccio, '
           'ma i tempi del Test non misurano il costo complessivo delle due preparazioni. '
           'Possiamo quindi sostenere la maggiore semplicità della preparazione, senza assegnarle '
           'un risparmio numerico non misurato. Nel perimetro descritto, il RAG rappresenta una '
           'soluzione promettente per combinare qualità delle scelte e riuscita della compilazione.\n')
    if 'llm_recupero_random' in runs:
        from estensione_random import conclusion
        body+=conclusion(runs['llm_recupero_random']['comparison_detail'])
    body+=r'\clearpage'+(HERE/'limiti.tex').read_text(encoding='utf-8-sig')
    return body


def circuit_appendix(runs):
    body=r'\clearpage\appendix\section{Statistiche per circuito}'+'\n'
    body+=('Ogni tabella riporta il nome completo del circuito, nello stesso ordine alfabetico dei grafici. '
           'Le colonne mantengono i nomi dei sistemi. Le misure sono separate in tabelle dedicate per evitare '
           'colonne troppo fitte. Tutti i tempi sono in secondi; token, chiamate e correzioni sono conteggi. '
           'Il simbolo -- indica un valore mancante. Le misure LLM non si applicano a MQT e Random.\n\n'
           'Il piano corrente prevede un episodio per circuito. Qualora siano presenti repliche, le misure '
           'sono prima mediate per circuito, lo score sui soli successi; una media non intera resta tale. '
           'I file CSV conservano i valori completi e le coperture di ciascuna misura.\n')
    methods=[m for m in method_order(runs) if m in runs]
    maps={m:{c['circuit_id']:c for c in r['circuits']} for m,r in runs.items()}
    ids=sorted(set.union(*(set(v) for v in maps.values())))
    definitions=[
        ('status','Esito della compilazione','Riuscito indica una compilazione valida; fallito un esito terminale senza risultato. Pendenti e casi misti sono espliciti.'),
        ('score','Score','Score delle compilazioni riuscite, a sei decimali per la lettura. I valori a dieci decimali sono conservati nei CSV. Un fallimento non vale zero.'),
        ('total_seconds','Tempo totale (secondi)','Comprende il percorso dal circuito all’esito, incluse eventuali correzioni e fallimenti.'),
        ('compilation_seconds','Tempo interno del compilatore (secondi)','Una misura assente dopo un timeout resta -- e non viene sostituita con 100 secondi.'),
        ('compilation_process_seconds','Tempo del processo di compilazione (secondi)','Comprende avvio, compilazione e controlli, inclusi i timeout misurati.'),
        ('choice_seconds','Preparazione e scelta (secondi)','Tempo precedente alla compilazione, secondo la misura conservata dal sistema.'),
        ('input_tokens','Token in ingresso','Somma dei token in ingresso di tutte le chiamate del caso.'),
        ('output_tokens','Token in uscita','Somma dei token prodotti in tutte le chiamate del caso.'),
        ('total_tokens','Token complessivi','Ingresso più uscita, comprese le richieste di correzione.'),
        ('llm_response_seconds','Tempo delle risposte LLM (secondi)','Somma delle attese delle risposte complete.'),
        ('retries','Richieste di correzione','Chiamate aggiuntive oltre la prima, prima dell’unica compilazione prevista.'),
        ('llm_calls','Numero di chiamate LLM','Comprende la prima risposta e le eventuali correzioni.'),
        ('rag_seconds','Tempo di recupero degli esempi (secondi)','Tempo del recupero registrato. Per LLM no RAG il recupero è disattivato.')]
    for key,title,description in definitions:
        cols=methods if key in ('status','score','total_seconds','compilation_seconds','compilation_process_seconds','choice_seconds') else [m for m in methods if m.startswith('llm')]
        if not cols:continue
        body+=(r'\clearpage' if key!='status' else '')+r'\subsection{'+title+'}\n'+description+'\n'
        rows=[]
        for cid in ids:
            row=[r'\nolinkurl{'+cid+'}']
            for m in cols:
                c=maps[m].get(cid,{})
                if key=='status':
                    value={'success':'Riuscito','failure':'Fallito','pending':'Pendente','mixed':'Misto'}.get(c.get(key),'--')
                elif key in ('input_tokens','output_tokens','total_tokens','retries','llm_calls'):
                    value=discrete(c.get(key))
                else:
                    value=fmt(c.get(key),6 if key=='score' else 3)
                row.append(value)
            rows.append(row)
        spec=r'>{\raggedright\arraybackslash}p{6.0cm}'+r'>{\centering\arraybackslash}p{1.75cm}'*len(cols)
        body+=table(['Circuito']+headers(cols,runs),rows,spec=spec,long=True,size='small')
    body+=r'\clearpage\section{Fonti e criteri di lettura}'+'\n'
    body+=('Questo documento è ricavato dai registri delle esecuzioni già concluse. '
           'La rigenerazione controlla l’identità dei circuiti e i contratti, senza avviare '
           'modelli o nuove compilazioni quantistiche. I rapporti precedenti e gli esiti originali restano conservati.\n\n'
           'Il protocollo corrente è in '+r'\nolinkurl{prototipo/docs/protocollo_sperimentale.md}'+
           '. Le impostazioni LLM sono in '+r'\nolinkurl{prototipo/config.json}'+
           '. La prova MQT separata conserva il proprio piano, il contratto e i metadati del selettore '
           'nella cartella '+r'\nolinkurl{archivio/valutazione/test_mqt_esplorativo/}'+'.\n\n'
           'Accanto al documento, '+r'\texttt{provenienza.json}'+
           ' raccoglie versioni, impronte, parametri inviati e riferimenti alle fonti. '
           'La cartella '+r'\texttt{generatore/}'+
           ' conserva i sorgenti usati; le cartelle delle tabelle e dei grafici contengono i dati '
           'da cui derivano le immagini. Questi dettagli permettono di ricostruire l’analisi '
           'senza appesantire la lettura del testo principale.\n\n'
           'I confronti di qualità usano gli stessi circuiti riusciti per entrambi i metodi. '
           'I costi includono tutti gli esiti con misura disponibile. Le somme riguardano gli episodi '
           'osservati; le medie danno uguale peso ai circuiti. Una misura ignota resta mancante, '
           'non viene sostituita con zero. Il conteggio dei token considera il testo completo in ingresso '
           'anche quando il server riusa la cache.\n\n'
           'Per la descrizione dell’architettura MQT il riferimento locale è '
           r'\nolinkurl{archivio/esperimento_v2/knowledge/MQT-Predictor.pdf}'
           ', relativo al lavoro del 2025. Il precedente articolo del 2023 tratta invece '
           'la previsione delle opzioni di compilazione e non va confuso con la sequenza ML e RL qui usata.\n')
    return body


def comparison_body(output,runs,comparison,plan):
    (output/'grafici').mkdir(parents=True,exist_ok=True)
    five='llm_recupero_random' in runs
    body=(HERE/('introduzione_cinque.tex' if five else 'introduzione.tex')).read_text(encoding='utf-8-sig')
    if comparison['missing_methods']:
        body+='\nRisultati non ancora disponibili: '+', '.join(PANEL_LABELS[m] for m in comparison['missing_methods'])+'. Il confronto è parziale.\n'
    body+=r'\clearpage'+'\n'+(HERE/('procedura_cinque.tex' if five else 'procedura.tex')).read_text(encoding='utf-8-sig').replace('%%MQT_DETAILS%%',mqt_details(runs).replace('gli altri tre sistemi','i tre sistemi del piano originale'))
    body+=summary_tables(runs,comparison,plan)
    body+=chart_pages(output,runs)
    body+=conclusions(runs,comparison)
    body+=circuit_appendix(runs)
    if five:
        body=body.replace('Il migliore fra i quattro sistemi osservati','Il migliore fra i cinque sistemi osservati')
        body+=('\nLa campagna con esempi casuali e il suo contratto separato sono in '
               r'\nolinkurl{archivio/valutazione/test/recupero_random/seed_20260927/}'
               '. Le fasce di qubit e le differenze sono ricavate dal manifest e dagli esiti conservati.\n')
    return body

