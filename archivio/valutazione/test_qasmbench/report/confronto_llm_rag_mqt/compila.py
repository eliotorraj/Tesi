'Compile the report twice and preserve logs, metadata and PNG previews.'
from pathlib import Path
import hashlib,json,subprocess,sys
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    for attempt in (1,2):
        with (HERE/f"compilazione_{attempt}.txt").open("wb") as log:
            proc=subprocess.run(["pdflatex","-interaction=nonstopmode","-halt-on-error","confronto_qasmbench.tex"],
                                cwd=HERE,stdout=log,stderr=subprocess.STDOUT)
        if proc.returncode:
            print((HERE/f"compilazione_{attempt}.txt").read_text(errors="replace")[-6000:])
            return proc.returncode
    text=subprocess.check_output(["pdfinfo",str(HERE/"confronto_qasmbench.pdf")],text=True)
    (HERE/"verifica_pdf.txt").write_text(text)
    print(text)
    subprocess.run(["pdftotext","-layout",str(HERE/"confronto_qasmbench.pdf"),str(HERE/"verifica_testo.txt")],check=True)
    preview=HERE/"anteprime";preview.mkdir(exist_ok=True)
    subprocess.run(["pdftoppm","-r","100","-png",str(HERE/"confronto_qasmbench.pdf"),str(preview/"pagina")],check=True)
    artifacts=json.loads((HERE/"artefatti.json").read_text())
    artifacts["sha256"].update({p.name:sha(p) for p in [Path(__file__),HERE/"confronto_qasmbench.pdf"]})
    artifacts["compiler"]=subprocess.check_output(["pdflatex","--version"],text=True).splitlines()[0]
    artifacts["visual_validation"]="pending"
    (HERE/"artefatti.json").write_text(json.dumps(artifacts,indent=2)+"\n")
    log=(HERE/"confronto_qasmbench.log").read_text(errors="replace")
    warnings=[x for x in log.splitlines() if "Overfull" in x or "Warning" in x or "Undefined" in x]
    print("WARNINGS",json.dumps(warnings))
    # Contact sheet: also retain each page at 100 dpi.
    try:
        from PIL import Image,ImageOps,ImageDraw
        paths=sorted(preview.glob("pagina-*.png"))
        w,h=300,450
        sheet=Image.new("RGB",(w*4,h*((len(paths)+3)//4)),"#dce1e5")
        draw=ImageDraw.Draw(sheet)
        for i,p in enumerate(paths):
            im=Image.open(p).convert("RGB");im.thumbnail((w-12,h-30))
            x=(i%4)*w+(w-im.width)//2;y=(i//4)*h+24
            sheet.paste(im,(x,y));draw.text((x,y-18),str(i+1),fill="black")
        sheet.save(preview/"insieme.png")
    except ImportError:
        print('Pillow unavailable; use the individual previews.')
    return 0
if __name__=="__main__":raise SystemExit(main())
