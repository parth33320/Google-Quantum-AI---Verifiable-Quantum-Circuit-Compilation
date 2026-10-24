"""Slice 2 optimizer for invsqrt benchmark circuit."""

import sys
import os
import shutil
import subprocess
import importlib.util

# Load kickmix shared library dynamically
kickmix_so = '/kaggle/input/competitions/google-verifiable-quantum-circuit-compilation/kickmix/kickmix.so'
spec = importlib.util.spec_from_file_location('kickmix', kickmix_so)
km = importlib.util.module_from_spec(spec)
spec.loader.exec_module(km)

INPUT_CIRCUIT = "/kaggle/input/competitions/google-verifiable-quantum-circuit-compilation/sample_submission/invsqrt.kmb"
VERIFIER_SCRIPT = "/kaggle/input/competitions/google-verifiable-quantum-circuit-compilation/verifiers/invsqrt/verify_submission_invsqrt.py"
TMP_DIR = "/kaggle/working/tmp"
TMP_CIRCUIT = os.path.join(TMP_DIR, "invsqrt.kmb")
SUBMISSION_DIR = "/kaggle/working/submission"
SUBMISSION_CIRCUIT = os.path.join(SUBMISSION_DIR, "invsqrt.kmb")


def run_verifier(circuit_path: str, shots_per_x: int = 1) -> tuple[bool, str]:
    """Runs the verifier script on the circuit and returns (passed, output_text)."""
    cmd = [
        sys.executable,
        VERIFIER_SCRIPT,
        circuit_path,
        "--shots-per-x", str(shots_per_x)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    passed = "PASS" in result.stdout or (result.returncode == 0 and "FAIL" not in result.stdout)
    return passed, result.stdout


def optimize_circuit_pass(circuit: km.Circuit) -> km.Circuit:
    """Attempts optimization strategies on the given kickmix circuit."""
    # Rebuilding circuit via CircuitBuilder if optimization API is available,
    # or returning a clean circuit structure.
    builder = km.CircuitBuilder()
    # Copying or rebuilding operations while applying peephole pass logic
    for op in circuit:
        # Example pass structure: append operations to builder
        pass
    # If builder was populated, finish_circuit(); otherwise return current circuit
    try:
        return builder.finish_circuit()
    except Exception:
        return circuit


def main():
    os.makedirs(TMP_DIR, exist_ok=True)
    os.makedirs(SUBMISSION_DIR, exist_ok=True)

    # 1. Load baseline circuit
    baseline_circuit = km.Circuit.from_file(INPUT_CIRCUIT, format="kmb")
    before_op_count = len(baseline_circuit)

    best_circuit = baseline_circuit
    best_op_count = before_op_count
    best_status = "FAIL"

    # Save baseline candidate to tmp and test verifier
    baseline_circuit.to_file(TMP_CIRCUIT, format="kmb")
    passed, _ = run_verifier(TMP_CIRCUIT, shots_per_x=1)
    if passed:
        best_status = "PASS"
        shutil.copy(TMP_CIRCUIT, SUBMISSION_CIRCUIT)

    # 3. Optimization loop
    max_iterations = 5
    current_circuit = baseline_circuit

    for i in range(max_iterations):
        candidate = optimize_circuit_pass(current_circuit)
        candidate_op_count = len(candidate)

        # Write candidate circuit to tmp first before verifier checks
        candidate.to_file(TMP_CIRCUIT, format="kmb")
        candidate_passed, _ = run_verifier(TMP_CIRCUIT, shots_per_x=1)

        if candidate_passed and (candidate_op_count < best_op_count or best_status == "FAIL"):
            best_circuit = candidate
            best_op_count = candidate_op_count
            best_status = "PASS"
            shutil.copy(TMP_CIRCUIT, SUBMISSION_CIRCUIT)
            current_circuit = candidate

    # 5. Print before and after operation counts, and PASS or FAIL
    after_op_count = best_op_count
    print(f"Before Operation Count: {before_op_count}")
    print(f"After Operation Count: {after_op_count}")
    print(f"Status: {best_status}")


if __name__ == "__main__":
    main()
