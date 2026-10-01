"""Punto di ingresso della riproduzione: configurare, preparare, valutare, esportare."""
import argparse
import json
import os
from pathlib import Path
import sys


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    selection=parser.add_mutually_exclusive_group()
    selection.add_argument('--config',type=Path,help='Configurazione JSON; ingressi relativi alla cartella riproducibilita')
    selection.add_argument('--esperimento',help='Nome creato con configura.py nuovo')
    parser.add_argument('--output',type=Path,help='Radice degli artefatti; predefinita: riproducibilita')
    commands=parser.add_subparsers(dest='command',required=True)
    commands.add_parser('prepara',
        help='Controlla e salva gli ingressi e le impostazioni di riferimento della prova',
        description='Controlla versioni, circuiti e Target; salva copie dei QASM, manifest, catalogo e impronte sotto esecuzioni/NOME nella radice risultati. La scrittura del contratto blocca le modifiche della configurazione nominata. Dataset, addestramento e valutazione si eseguono con le fasi successive.',
        epilog='Esempio: python esperimento.py --esperimento mia-prova prepara. Per cambiare condizioni dopo la preparazione: python configura.py duplica mia-prova nuova-prova.')
    commands.add_parser('hardware',help='Mostra i Target sintetici e le loro impronte')
    commands.add_parser('verifica',help='Controlla installazione e sorgenti; nessuna inferenza')
    commands.add_parser('stato',help='Mostra artefatti presenti e prossimo passaggio, senza eseguire prove')
    server=commands.add_parser('server',help='Avvia o controlla il server LLM con le impostazioni dell’esperimento')
    from comune.opzioni_server import add_arguments
    add_arguments(server)
    d=commands.add_parser('dataset',help='Genera la matrice Qiskit e il Dataset RAG dal solo train')
    d.add_argument('--split',action='append',choices=['train','validation'])
    d.add_argument('--aggrega',action='store_true',help='Rilegge i tentativi già conservati')
    m=commands.add_parser('mqt',help='Addestra RL o genera il Training set e addestra il selettore')
    m.add_argument('fase',choices=['rl','selettore','verifica'])
    m.add_argument('opzioni',nargs=argparse.REMAINDER,help='Opzioni del trainer; vedi mqt/README.md')
    v=commands.add_parser('validation',help='Confronta i candidati senza utilizzare Test')
    v.add_argument('fase',choices=['congela','esegui','seleziona','report','wl'])
    v.add_argument('--modello')
    t=commands.add_parser('test',help='Congela il piano e misura i metodi selezionati')
    t.add_argument('fase',choices=['congela','esegui','analizza','oracle','tecnico-mqt'])
    t.add_argument('--metodo')
    e=commands.add_parser('esporta',help='Crea un nuovo prototipo autonomo dal Dataset e dal modello selezionato')
    e.add_argument('destinazione',type=Path)
    a=parser.parse_args()
    if a.esperimento:
        from comune.configuratore import config_path, load
        load(a.esperimento)
        os.environ['RIPRO_CONFIG']=str(config_path(a.esperimento))
    elif a.config:os.environ['RIPRO_CONFIG']=str(a.config.resolve())
    if a.output:os.environ['RIPRO_OUTPUT']=str(a.output.resolve())
    sys.dont_write_bytecode=True
    import bootstrap
    import settings as s
    if a.command=='prepara':
        from corpus import prepare
        from comune.configuratore import preparation_guard
        with preparation_guard(s.CONFIG_PATH,s.CONFIG,s.WORK):
            result=prepare()
    elif a.command=='stato':
        from stato import show
        show()
        return
    elif a.command=='server':
        from modelli_llm.server import main as serve
        raise SystemExit(serve(args=a))
    elif a.command=='hardware':
        from gestione import hardware
        result=hardware()
    elif a.command=='verifica':
        from controlli import installation
        result=installation()
    elif a.command=='dataset':
        from genera import aggregate,generate
        result=aggregate() if a.aggrega else generate(a.split or ('train','validation'))
    elif a.command=='mqt':
        from gestione import assets,training
        result=assets() if a.fase=='verifica' else training(a.fase,a.opzioni)
    elif a.command=='validation':
        import seleziona
        if a.fase=='esegui' and not a.modello:parser.error('validation esegui richiede --modello')
        if a.fase=='wl':
            from wl import select
            result=select()
        elif a.fase=='report':
            from relazioni import validation_report
            result=validation_report()
        else:result={'congela':seleziona.freeze,'seleziona':seleziona.select,'esegui':lambda:seleziona.run(a.modello)}[a.fase]()
    elif a.command=='test':
        import esegui
        if a.fase=='esegui' and not a.metodo:parser.error('test esegui richiede --metodo')
        if a.fase=='analizza':
            from analizza import report
            result=report()
        elif a.fase=='oracle':
            from oracle import run
            result=run()
        elif a.fase=='tecnico-mqt':
            from gestione import technical
            result=technical()
        else:result={'congela':esegui.freeze,'esegui':lambda:esegui.run(a.metodo)}[a.fase]()
    else:
        from esporta import export
        result=export(a.destinazione)
    if result is not None:print(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False))

if __name__=='__main__':
    try:main()
    except (ValueError,OSError,KeyError) as exc:
        print(f'Errore: {exc}',file=sys.stderr)
        raise SystemExit(2)
