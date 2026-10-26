"""Script to build DQI reference circuit and analyze qubit/register/operation statistics."""

import os
import sys
import importlib.util

# Dynamic loading of kickmix module
kickmix_so = '/kaggle/input/competitions/google-verifiable-quantum-circuit-compilation/kickmix/kickmix.so'
if not os.path.exists(kickmix_so):
    # Fallback to local path if running outside standard competition path setup
    kickmix_so = os.path.abspath(os.path.join(os.path.dirname(__file__), '../kickmix/kickmix.so'))

spec = importlib.util.spec_from_file_location('kickmix', kickmix_so)
km = importlib.util.module_from_spec(spec)
sys.modules['kickmix'] = km
spec.loader.exec_module(km)

# Adjust path to find verifiers module if needed
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from verifiers.dqi.dqi_reference_circuit import build_reference_circuit


def main():
    circuit = build_reference_circuit(m=4095, n=70, degree=12)

    print(f"Total qubits: {circuit.num_qubits}")

    print("Register num_qubits:")
    for name, reg in circuit.register_data.items():
        print(f"  {name}: {len(reg)}")

    print(f"Operation statistics: {circuit.operation_statistics()}")


if __name__ == '__main__':
    main()
