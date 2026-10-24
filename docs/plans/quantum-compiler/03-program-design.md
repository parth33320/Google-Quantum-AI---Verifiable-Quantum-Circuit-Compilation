# Program Design: Quantum Compiler Optimization Pipeline

## Files
Files that will be created for the compilation pipeline:

* `src/compiler/loader.py`: Circuit loader module to deserialize `.kmb` / `.kmx` baseline circuit files into `kickmix.Circuit` objects.
* `src/compiler/optimizer.py`: Core optimization pass engine executing peephole cancellation, phase commutation, and Toffoli/T-gate reductions via `kickmix.CircuitBuilder`.
* `src/compiler/verifier_adapter.py`: Wrapper interface adapter to invoke benchmark verifier scripts and retrieve correctness metrics and resource scores.
* `src/compiler/pipeline.py`: Main orchestration pipeline executing load, optimize, verify, and artifact export loops for all three competition benchmarks.
* `src/compiler/saver.py`: Artifact exporter writing validated, score-improved `kickmix.Circuit` instances back to `.kmb` binary format.

## Types & Signatures

```python
from typing import Dict, Any, Tuple, Optional
import kickmix as km

# --- src/compiler/loader.py ---
def load_circuit(filepath: str, format_type: str = "auto") -> km.Circuit:
    ...

def validate_input_registers(circuit: km.Circuit, benchmark_id: str) -> bool:
    ...

# --- src/compiler/optimizer.py ---
def optimize_circuit(circuit: km.Circuit, opt_level: int = 2) -> km.Circuit:
    ...

def apply_peephole_passes(builder: km.CircuitBuilder) -> km.CircuitBuilder:
    ...

def reduce_toffoli_gates(builder: km.CircuitBuilder) -> km.CircuitBuilder:
    ...

# --- src/compiler/verifier_adapter.py ---
def run_verifier(
    benchmark_id: str,
    circuit_path: str,
    data_root: str = "/kaggle/input/google-verifiable-quantum-circuit-compilation/"
) -> Dict[str, Any]:
    ...

def parse_verifier_output(raw_output: str) -> Dict[str, Any]:
    ...

# --- src/compiler/saver.py ---
def save_circuit(circuit: km.Circuit, output_path: str, format_type: str = "kmb") -> str:
    ...

# --- src/compiler/pipeline.py ---
def run_optimization_pipeline(
    benchmark_id: str,
    input_circuit_path: str,
    output_circuit_path: str,
    data_root: str = "/kaggle/input/google-verifiable-quantum-circuit-compilation/"
) -> Tuple[bool, float, Dict[str, Any]]:
    ...
```

## Call Stack

Execution Call Stack Trace:
└── [Project] Quantum Circuit Compiler Engine CLI Wrapper (`src/compiler/pipeline.py`)
    ├── [Configuration/Env] DATA_ROOT="/kaggle/input/google-verifiable-quantum-circuit-compilation/", KICKMIX_SO="/kaggle/input/google-verifiable-quantum-circuit-compilation/kickmix/kickmix.so"
    └── [Folder] `src/compiler`
        ├── [File] `loader.py`
        │   └── [Class] CircuitLoader
        │       └── [Method] load_circuit(filepath: str = "/kaggle/input/google-verifiable-quantum-circuit-compilation/sample_submission/invsqrt.kmb") -> km.Circuit
        │           ├── [Variable State Shift] Inbound Param: filepath = "/kaggle/input/google-verifiable-quantum-circuit-compilation/sample_submission/invsqrt.kmb"
        │           └── [Variable State Shift] Mutated Result: circuit.num_ops = 4850, circuit.num_qubits = 22
        ├── [File] `optimizer.py`
        │   └── [Class] CircuitOptimizer
        │       └── [Method] optimize_circuit(circuit: km.Circuit, opt_level: int = 2) -> km.Circuit
        │           ├── [Variable State Shift] Inbound Param: circuit.num_ops = 4850
        │           ├── [Variable State Shift] Mutated Result: optimized_circuit.num_ops = 4120, toffoli_count = 340
        │           └── [Method] apply_peephole_passes(builder: km.CircuitBuilder) -> km.CircuitBuilder
        │               └── [Variable State Shift] Mutated Result: builder.gate_count = 4120
        ├── [File] `verifier_adapter.py`
        │   └── [Class] VerifierAdapter
        │       └── [Method] run_verifier(benchmark_id: "invsqrt", circuit_path: "/kaggle/working/submission/invsqrt.kmb", data_root: "/kaggle/input/google-verifiable-quantum-circuit-compilation/") -> Dict[str, Any]
        │           ├── [Variable State Shift] Inbound Param: circuit_path = "/kaggle/working/submission/invsqrt.kmb"
        │           ├── [Variable State Shift] Mutated Result: result["status"] = "PASS", result["score"] = 12450.0
        │           └── [Project] External Verifier Script (`/kaggle/input/google-verifiable-quantum-circuit-compilation/verifiers/invsqrt/verify_submission_invsqrt.py`)
        └── [File] `saver.py`
            └── [Class] CircuitExporter
                └── [Method] save_circuit(circuit: km.Circuit, output_path: "/kaggle/working/submission/invsqrt.kmb") -> str
                    └── [Variable State Shift] Mutated Result: output_file_written = True

## Test Plan
* **`test_load_baseline_circuits`**: Verify that all baseline `.kmb` files from `/kaggle/input/google-verifiable-quantum-circuit-compilation/sample_submission/` load into valid `kickmix.Circuit` objects without raising exceptions.
* **`test_optimizer_gate_reduction`**: Assert that applying `optimize_circuit` on a test circuit reduces or maintains the total gate/Toffoli count without altering circuit register layouts.
* **`test_verifier_adapter_invsqrt`**: Execute `run_verifier` against `/kaggle/input/google-verifiable-quantum-circuit-compilation/verifiers/invsqrt/verify_submission_invsqrt.py` with baseline `/kaggle/input/google-verifiable-quantum-circuit-compilation/sample_submission/invsqrt.kmb` and assert `status == "PASS"`.
* **`test_verifier_adapter_dqi`**: Execute `run_verifier` against `/kaggle/input/google-verifiable-quantum-circuit-compilation/verifiers/dqi/verify_submission_dqi.py` with baseline `/kaggle/input/google-verifiable-quantum-circuit-compilation/sample_submission/dqi.kmb` and assert `status == "PASS"`.
* **`test_verifier_adapter_dfthcsos`**: Execute `run_verifier` against `/kaggle/input/google-verifiable-quantum-circuit-compilation/verifiers/dfthcsos/verify.py` with baseline files in `/kaggle/input/google-verifiable-quantum-circuit-compilation/sample_submission/dfthcsos/` and assert `status == "PASS"`.
* **`test_save_circuit_roundtrip`**: Verify that a circuit saved via `save_circuit` can be re-loaded and produces identical gate sequences.

## Least Confident Decisions (Resolved)
1. **Subprocess Isolation vs. Direct Python Import for Verifiers**: Resolved -> Use `subprocess.run` to call verifiers for clean process isolation.
2. **Fixed-Point Rotation Decomposition Strategy**: Resolved -> Keep native `Z_POW` rotations. Do not decompose to T-gates yet.
3. **Optimized Circuit Storage Location during Evaluation**: Resolved -> Write candidate circuits to `/kaggle/working/tmp/` first, and copy to `/kaggle/working/submission/` only after verifier confirms PASS.

---

Approve Gate 3, or what should change?
