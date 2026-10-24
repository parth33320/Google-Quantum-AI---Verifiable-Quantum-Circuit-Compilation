"""Slice 1 runner for invsqrt benchmark circuit verification."""

import sys
sys.path.insert(0, '/kaggle/input/google-verifiable-quantum-circuit-compilation/kickmix')
from kickmix import kickmix as km
import subprocess
import os

def main():
    circuit_path = "/kaggle/input/google-verifiable-quantum-circuit-compilation/sample_submission/invsqrt.kmb"
    kickmix_path = "/kaggle/input/google-verifiable-quantum-circuit-compilation/kickmix/kickmix.so"
    verifier_script = "/kaggle/input/google-verifiable-quantum-circuit-compilation/verifiers/invsqrt/verify_submission_invsqrt.py"

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
