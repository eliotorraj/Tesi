"""Relazioni riproducibili dai registri: JSON/CSV, figure e sorgenti LaTeX."""
from pathlib import Path
import csv
import io
import settings as s


def escape(value):
    mapping={'\\':r'\textbackslash{}','&':r'\&','%':r'\%','$':r'\$','#':r'\#','_':r'\_','{':r'\{','}':r'\}'}
    return ''.join(mapping.get(c,c) for c in str(value))


def write_text_once(path,content):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():
        if path.read_text()!=content:raise ValueError('Relazione già esistente diversa: '+str(path))
    else:path.write_text(content,encoding='utf-8')


def table_report(directory,title,explanation,headers,rows,figure=None):
    directory=Path(directory)
    body=' & '.join(escape(x) for x in headers)+r' \\ \hline'+'\n'
    body+='\n'.join(' & '.join(escape(x) for x in row)+r' \\' for row in rows)
    text=(r'\documentclass{article}'+'\n'+r'\usepackage[T1]{fontenc}'+'\n'+
          r'\usepackage[utf8]{inputenc}'+'\n'+r'\usepackage[italian]{babel}'+'\n'+
          r'\usepackage[a4paper,margin=22mm]{geometry}'+'\n'+r'\usepackage{graphicx}'+'\n'+r'\usepackage{pgfplots}\pgfplotsset{compat=1.18}'+'\n'+
          r'\begin{document}'+'\n'+r'\section*{'+escape(title)+'}\n'+escape(explanation)+'\n\n'+
          r'\begin{center}\small\begin{tabular}{'+'l'*len(headers)+'}\n'+body+'\n'+r'\end{tabular}\end{center}'+'\n')
    if figure:text+=r'\begin{center}'+(directory/figure).read_text()+r'\end{center}'+'\n'
    text+=r'\end{document}'+'\n'
    write_text_once(directory/'report.tex',text)


def validation_report():
    from seleziona import contract,verify_selection
    c=contract();selection=verify_selection()
    identity=s.digest({'selection':s.sha(s.VALIDATION/'selezione.json'),'code':s.sha(Path(__file__))})
    dest=s.VALIDATION/'report'/identity;dest.mkdir(parents=True,exist_ok=True)
    rows=selection['table'];buf=io.StringIO()
    writer=csv.DictWriter(buf,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    write_text_once(dest/'candidati.csv',buf.getvalue())
    s.same_or_save(dest/'riepilogo.json',selection)
    measured=[r for r in rows if r['candidate'] in selection['eligible_candidates']]
    labels=','.join('{'+escape(r['candidate'])+'}' for r in measured)
    coords=' '.join(f"({r[c['criterion']]},{i})" for i,r in enumerate(measured))
    plot=(r'\begin{tikzpicture}\begin{axis}[xbar,width=.9\linewidth,height=5cm,'
          r'xlabel={'+escape(c['criterion'])+r'},ytick={'+','.join(str(i) for i in range(len(measured)))+
          r'},yticklabels={'+labels+r'},xmin=0,enlarge y limits=.4]'+
          r'\addplot coordinates {'+coords+r'};\end{axis}\end{tikzpicture}')
    write_text_once(dest/'regret.pgf',plot)
    details=('La griglia dei candidati, le impostazioni e le impronte dei modelli sono congelate prima delle decisioni. '
             'Il Dataset e gli esempi RAG contengono solo train. Gli score validation vengono letti dopo il sigillo delle decisioni. '
             'La selezione privilegia la copertura valutabile e confronta il regret sui circuiti comuni dei candidati con copertura massima. '
             'Il riferimento è la migliore mediana osservata sui tre seed per le coppie eleggibili, non un ottimo teorico. '
             'Le risposte con fatti non verificati sono conteggiate separatamente nei registri. Test non è utilizzato. '
             'Criterio: '+c['criterion']+'. Selezione: '+selection['winner']['id']+'. Circuiti comuni: '+str(len(selection['common_circuits']))+'. '
             'Token e tempi mancanti restano mancanti; il riepilogo include anche candidati scartati e fallimenti. '
             'Le condizioni dipendono dai circuiti, dai Target sintetici e dalle risorse registrate per questa esecuzione.')
    table_report(dest,'Selezione sulla validation',details,['Candidato','Valutabili','Comuni','Regret medio','Correzioni'],
        [[r['candidate'],r['valid_and_compilable'],r['common_count'],f"{r['mean_regret']:.6g}" if r['mean_regret'] is not None else '--',r['repairs']] for r in rows],'regret.pgf')
    return {'directory':str(dest),'winner':selection['winner'],'pdf_compilation':'pdflatex -interaction=nonstopmode report.tex (nella directory del report)'}
