"""Esporta tutte le pagine del PDF in PNG per il controllo visivo."""
import argparse
from pathlib import Path
def main():
    parser=argparse.ArgumentParser();parser.add_argument("pdf",type=Path);parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    import pymupdf
    args.output.mkdir(parents=True,exist_ok=True)
    with pymupdf.open(args.pdf) as document:
        for index,page in enumerate(document):
            page.get_pixmap(matrix=pymupdf.Matrix(1.5,1.5),alpha=False).save(args.output/f"pagina-{index+1:03}.png")
        print(f"PDF: {len(document)} pagine; anteprime in {args.output}")
if __name__=="__main__": main()
