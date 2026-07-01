"""List the quantum-device targets available through MQT Bench."""

from __future__ import annotations

import argparse

from mqt.bench.targets import get_available_device_names, get_device


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--details", metavar="DEVICE", help="Mostra gate e connettività di un singolo device.")
    return parser.parse_args()


def main() -> int:
    """Print all targets, or details for one selected target."""
    args = parse_args()
    available = list(get_available_device_names())

    if args.details:
        if args.details not in available:
            raise SystemExit(f"Device sconosciuto: {args.details}")
        device = get_device(args.details)
        coupling_map = device.build_coupling_map()
        print(f"Nome:          {device.description}")
        print(f"Qubit:         {device.num_qubits}")
        print(f"Operazioni:    {', '.join(sorted(device.operation_names))}")
        print(f"Coupling map:  {coupling_map}")
        return 0

    print(f"{'DEVICE':<28} {'QUBIT':>6} {'OPERAZIONI':>11}")
    print("-" * 49)
    for name in available:
        device = get_device(name)
        print(f"{name:<28} {device.num_qubits:>6} {len(device.operation_names):>11}")
    print(f"\nTotale device disponibili: {len(available)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
