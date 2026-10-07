'Arguments shared by the LLM launcher and esperimento.py server.'
def add_arguments(parser):
    parser.add_argument("modello", nargs="?", help='Active candidate ID')
    parser.add_argument("--bin", help='Linux executable; overrides the saved path')
    parser.add_argument("--device", help='GPU identifier exposed by llama.cpp')
    parser.add_argument("--list-devices", action="store_true", help='List backend devices without loading the GGUF')
    parser.add_argument("--gpu-layers", type=int, help='GPU layers; overrides the saved profile')
    parser.add_argument("--threads", type=int, help='Threads; overrides the saved profile')
    parser.add_argument("--controlla", action="store_true", help='Check identity and context of an already running server')
