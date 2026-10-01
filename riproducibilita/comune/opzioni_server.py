"""Argomenti condivisi fra l'avviatore LLM e il comando esperimento.py server."""
def add_arguments(parser):
    parser.add_argument("modello", nargs="?", help="ID del candidato attivo")
    parser.add_argument("--bin", help="Eseguibile Linux; prevale sul percorso salvato")
    parser.add_argument("--device", help="Identificativo GPU esposto da llama.cpp")
    parser.add_argument("--list-devices", action="store_true", help="Elenca i dispositivi del backend, senza caricare il GGUF")
    parser.add_argument("--gpu-layers", type=int, help="Strati su GPU; prevale sul profilo salvato")
    parser.add_argument("--threads", type=int, help="Thread; prevale sul profilo salvato")
    parser.add_argument("--controlla", action="store_true", help="Verifica identità e contesto del server già avviato")
