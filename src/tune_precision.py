"""Tune precision parameters for Newton-Raphson inverse square root circuit.

Tries reducing Precision dataclass parameters one at a time, builds the circuit with
build_nr_circuit(n_p=10), checks num_qubits and num_toffoli_like, and prints a summary table.
"""

from __future__ import annotations

import dataclasses
import importlib.util
import os
import sys


def load_kickmix() -> None:
    """Dynamically loads kickmix shared library if not already imported."""
    if 'kickmix' in sys.modules:
        return

    candidate_paths = [
        './kickmix/kickmix.so',
        '/app/kickmix/kickmix.so',
        '/kaggle/input/competitions/google-verifiable-quantum-circuit-compilation/kickmix/kickmix.so',
        '/kaggle/input/google-verifiable-quantum-circuit-compilation/kickmix/kickmix.so',
    ]

    for path in candidate_paths:
        if os.path.exists(path):
            spec = importlib.util.spec_from_file_location('kickmix', path)
            if spec and spec.loader:
                km = importlib.util.module_from_spec(spec)
                sys.modules['kickmix'] = km
                spec.loader.exec_module(km)
                return

    # Fallback to direct import if installed in site-packages
    import kickmix as km  # type: ignore # noqa: F401


def setup_path() -> None:
    """Ensure verifiers path is in sys.path."""
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.abspath(os.path.join(curr_dir, '..'))
    verifiers_dir = os.path.join(repo_root, 'verifiers')
    invsqrt_dir = os.path.join(verifiers_dir, 'invsqrt')

    for path in (repo_root, verifiers_dir, invsqrt_dir):
        if path not in sys.path:
            sys.path.insert(0, path)


def main() -> None:
    load_kickmix()
    setup_path()

    from verifiers.invsqrt.nr_reference_circuit import Precision, build_nr_circuit

    n_p = 10
    baseline_prec = Precision()
    baseline_circuit = build_nr_circuit(n_p, prec=baseline_prec)
    baseline_qubits = baseline_circuit.num_qubits
    baseline_toffolis = baseline_circuit.operation_statistics().num_toffoli_like

    print("=" * 80)
    print("INVERSE SQUARE ROOT PRECISION PARAMETER TUNING")
    print(f"n_p: {n_p}")
    print(f"Baseline Precision: {baseline_prec}")
    print(f"Baseline Stats: Qubits = {baseline_qubits}, Toffoli-like = {baseline_toffolis}")
    print("=" * 80)

    header = f"{'Parameter':<15} | {'Original':<8} | {'New':<6} | {'Delta':<5} | {'Qubits':<8} | {'Toffolis':<10} | {'Toffoli Diff':<12} | {'Status':<10}"
    divider = "-" * len(header)

    print(header)
    print(divider)
    print(f"{'BASELINE':<15} | {'-':<8} | {'-':<6} | {'0':<5} | {baseline_qubits:<8} | {baseline_toffolis:<10} | {0:<12} | {'OK':<10}")

    fields = dataclasses.fields(Precision)

    for field in fields:
        param_name = field.name
        orig_val = getattr(baseline_prec, param_name)

        # Try reducing by 1, 2, 3, 4, 5
        for reduce_by in range(1, 6):
            new_val = orig_val - reduce_by
            if new_val < 1:
                continue

            kwargs = {f.name: getattr(baseline_prec, f.name) for f in fields}
            kwargs[param_name] = new_val
            candidate_prec = Precision(**kwargs)

            try:
                circuit = build_nr_circuit(n_p, prec=candidate_prec)
                num_qubits = circuit.num_qubits
                num_toffolis = circuit.operation_statistics().num_toffoli_like
                toffoli_diff = num_toffolis - baseline_toffolis
                status = "OK"
                print(f"{param_name:<15} | {orig_val:<8} | {new_val:<6} | {-reduce_by:<5} | {num_qubits:<8} | {num_toffolis:<10} | {toffoli_diff:<12} | {status:<10}")
            except Exception as err:
                status = "ERROR"
                print(f"{param_name:<15} | {orig_val:<8} | {new_val:<6} | {-reduce_by:<5} | {'N/A':<8} | {'N/A':<10} | {'N/A':<12} | {status:<10} ({type(err).__name__})")

        print(divider)


if __name__ == '__main__':
    main()
