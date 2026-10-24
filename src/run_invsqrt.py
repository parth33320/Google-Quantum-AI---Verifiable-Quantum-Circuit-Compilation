"""Slice 1 runner for invsqrt benchmark circuit verification."""

import sys
import importlib.util

kickmix_so = '/kaggle/input/competitions/google-verifiable-quantum-circuit-compilation/kickmix/kickmix.so'
spec = importlib.util.spec_from_file_location('kickmix', kickmix_so)
km = importlib.util.module_from_spec(spec)
spec.loader.exec_module(km)
import subprocess
import os

def main():
    circuit_path = "/kaggle/input/competitions/google-verifiable-quantum-circuit-compilation/sample_submission/invsqrt.kmb"
    kickmix_path = "/kaggle/input/competitions/google-verifiable-quantum-circuit-compilation/kickmix/kickmix.so"
    verifier_script = "/kaggle/input/competitions/google-verifiable-quantum-circuit-compilation/verifiers/invsqrt/verify_submission_invsqrt.py"

    # Load circuit using kickmix
    circuit = km.Circuit.from_file(circuit_path, format="kmb")
    op_count = len(circuit)

    # Call verifier script using subprocess.run
    cmd = [
        sys.executable,
        verifier_script,
        circuit_path,
        "--shots-per-x", "1"  # Fast verification run
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    status = "FAIL"
    if "PASS" in result.stdout:
        status = "PASS"
    elif result.returncode == 0:
        status = "PASS"

    print(f"Status: {status}")
    print(f"Operation Count: {op_count}")

if __name__ == "__main__":
    main()
