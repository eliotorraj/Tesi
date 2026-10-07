'Configure experiments through readable commands without editing JSON manually.'
import sys

sys.dont_write_bytecode = True

from comune.configuratore_cli import main

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, KeyError) as exc:
        print(f'Error: {exc}', file=sys.stderr)
        raise SystemExit(2)
