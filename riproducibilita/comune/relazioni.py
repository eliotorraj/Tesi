'Reproducible reports from records: JSON/CSV, figures and LaTeX sources.'
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
        if path.read_text()!=content:raise ValueError('A different report already exists: '+str(path))
    else:path.write_text(content,encoding='utf-8')


def table_report(directory,title,explanation,headers,rows,figure=None):
    directory=Path(directory)
    body=' & '.join(escape(x) for x in headers)+r' \\ \hline'+'\n'
    body+='\n'.join(' & '.join(escape(x) for x in row)+r' \\' for row in rows)
    text=(r'\documentclass{article}'+'\n'+r'\usepackage[T1]{fontenc}'+'\n'+
          r'\usepackage[utf8]{inputenc}'+'\n'+'\\usepackage[english]{babel}'+'\n'+
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
    details=('The candidate grid, settings and model fingerprints are frozen before decisions. The Dataset and RAG examples contain train only. Validation scores are read after decisions are sealed. Selection prioritizes evaluable coverage and compares regret on common circuits among candidates with maximum coverage. The reference is the best observed three-seed median among eligible pairs, not a theoretical optimum. Responses with unverified facts are recorded separately. Test is not used. Criterion: '+c['criterion']+'. Selection: '+selection['winner']['id']+'. Common circuits: '+str(len(selection['common_circuits']))+'. Missing tokens and timings remain missing; the summary includes rejected candidates and failures. Conditions depend on the circuits, synthetic Targets and resources recorded for this run.')
    table_report(dest,'Validation selection',details,['Candidate','Evaluable','Shared','Mean regret','Repairs'],
        [[r['candidate'],r['valid_and_compilable'],r['common_count'],f"{r['mean_regret']:.6g}" if r['mean_regret'] is not None else '--',r['repairs']] for r in rows],'regret.pgf')
    return {'directory':str(dest),'winner':selection['winner'],'pdf_compilation':'pdflatex -interaction=nonstopmode report.tex (in the report directory)'}
