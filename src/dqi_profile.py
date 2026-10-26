"""Script to profile the DQI reference circuit and display Toffoli counts per stage."""

import os
import sys
import importlib.util

# Dynamic loading of kickmix module
kickmix_so = '/kaggle/input/competitions/google-verifiable-quantum-circuit-compilation/kickmix/kickmix.so'
if not os.path.exists(kickmix_so):
    # Fallback to local path if running outside standard competition path setup
    kickmix_so = os.path.abspath(os.path.join(os.path.dirname(__file__), '../kickmix/kickmix.so'))

if os.path.exists(kickmix_so):
    spec = importlib.util.spec_from_file_location('kickmix', kickmix_so)
    km = importlib.util.module_from_spec(spec)
    sys.modules['kickmix'] = km
    spec.loader.exec_module(km)
else:
    import kickmix as km

# Adjust path to find verifiers module if needed
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from verifiers.dqi.dqi_reference_circuit import (
    ProosAndZalkaDecoder,
    build_reference_circuit,
    default_n_iters,
)


def profile_dqi_stages(m: int = 4095, n: int = 70, degree: int = 12) -> dict[str, int]:
    """Computes Toffoli counts per stage for the DQI circuit."""
    field = km.GF2Field(degree)
    decoder = ProosAndZalkaDecoder(n, field)
    n_iters = default_n_iters(n)
    m_reg = n + 3
    logm = m_reg.bit_length() + 1

    stages = {}

    # 1. initial_shift
    builder = km.CircuitBuilder()
    reg_a = [builder.alloc_qubits(degree) for _ in range(m_reg)]
    n_A = builder.alloc_qubits(logm)
    decoder._initial_shift_loop(builder, reg_a, n_A, is_adjoint=False)
    stages['initial_shift'] = builder.finish_circuit().operation_statistics().num_toffoli_like

    # 2. forward_eea
    builder = km.CircuitBuilder()
    reg_a = [builder.alloc_qubits(degree) for _ in range(m_reg)]
    reg_b = [builder.alloc_qubits(degree) for _ in range(m_reg)]
    n_A = builder.alloc_qubits(logm)
    n_B = builder.alloc_qubits(logm)
    n_a = builder.alloc_qubits(logm)
    n_b = builder.alloc_qubits(logm)
    n_q = builder.alloc_qubits(logm)
    flag = builder.alloc_qubits(1)[0]
    counter = builder.alloc_qubits(2)
    halting_counter = builder.alloc_qubits(n_iters.bit_length())
    eea = (reg_a, reg_b, n_A, n_B, n_a, n_b, n_q, flag, counter, halting_counter)
    decoder._synchronized_eea(builder, *eea, n_iters=n_iters, is_adjoint=False)
    stages['forward_eea'] = builder.finish_circuit().operation_statistics().num_toffoli_like

    # 3. chien_forney_mbuc
    builder = km.CircuitBuilder()
    reg_b = [builder.alloc_qubits(degree) for _ in range(m_reg)]
    error_mbuc = [builder.create_classical_register(degree, name=f'E{j}') for j in range(m)]
    n_B = builder.alloc_qubits(logm)
    n_b = builder.alloc_qubits(logm)
    decoder._chien_search_and_forney_mbuc(builder, reg_b, error_mbuc, n_b, n_B)
    stages['chien_forney_mbuc'] = builder.finish_circuit().operation_statistics().num_toffoli_like

    # 4. reverse_eea
    stages['reverse_eea'] = stages['forward_eea']

    # 5. uncompute_initial_shift
    stages['uncompute_initial_shift'] = stages['initial_shift']

    return stages


def main():
    m = 4095
    n = 70
    degree = 12

    print(f"Building DQI reference circuit (m={m}, n={n}, degree={degree}, compute_only=False)...")
    circuit = build_reference_circuit(m, n, degree, compute_only=False)

    stats = circuit.operation_statistics()
    print("\n--- Circuit Operation Statistics ---")
    print(f"Total instructions: {stats.num_instructions:,}")
    print(f"Total Toffoli-like gates: {stats.num_toffoli_like:,}")
    print(f"Total T-like gates: {stats.num_t_like:,}")
    print(f"Total Qubits: {circuit.num_qubits}")
    print(f"Total Bits: {circuit.num_bits}")

    stage_counts = profile_dqi_stages(m, n, degree)
    print("\n--- Toffoli Counts Per Stage ---")
    total_stage_toffolis = 0
    for stage_name, count in stage_counts.items():
        print(f"  {stage_name:<25s}: {count:>12,d} Toffolis")
        total_stage_toffolis += count
    print(f"  {'Total Stage Toffolis':<25s}: {total_stage_toffolis:>12,d} Toffolis")

    print("\n--- Flame Chart SVG ---")
    flame_chart = circuit.flame_chart_svg()
    print(f"Flame chart SVG generated ({len(flame_chart):,} chars)")

    print("\n--- Text Diagram ---")
    text_diag = circuit.text_diagram()
    print(text_diag)


if __name__ == '__main__':
    main()
