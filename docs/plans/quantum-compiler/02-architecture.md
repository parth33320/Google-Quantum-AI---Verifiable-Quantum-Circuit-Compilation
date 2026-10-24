# Architecture: Quantum Compiler Optimization Pipeline

## Fit
The Quantum Compiler Optimization Pipeline provides automated circuit compilation, optimization, and verification for Google Verifiable Quantum Circuit Compilation benchmarks inside a Kaggle notebook environment.

* **Component Integration**: Integrates directly with the `kickmix` core library (`kickmix.so`) for in-memory circuit manipulation, builder operations, and CPU-only simulation.
* **Verifier Integration**: Interfaces with benchmark verifier modules in `/kaggle/input/google-verifiable-quantum-circuit-compilation/verifiers/` to ensure correctness, state restoration, and scoring.
* **Input/Output Seam**: Reads baseline circuit definitions (`.kmb` / `.kmx` binary formats) from `/kaggle/input/google-verifiable-quantum-circuit-compilation/sample_submission/` and outputs optimized circuit artifacts to Kaggle working storage.

## Endpoints
none

## Data
All input data paths are rooted strictly at `/kaggle/input/google-verifiable-quantum-circuit-compilation/`:

### Input Circuit Artifacts
* **Benchmark I (InvSqrt)**: `/kaggle/input/google-verifiable-quantum-circuit-compilation/sample_submission/invsqrt.kmb`
* **Benchmark II (DQI)**: `/kaggle/input/google-verifiable-quantum-circuit-compilation/sample_submission/dqi.kmb`
* **Benchmark III (DFTHC-SOS)**: `/kaggle/input/google-verifiable-quantum-circuit-compilation/sample_submission/dfthcsos/angle_k_0.kmb` through `/kaggle/input/google-verifiable-quantum-circuit-compilation/sample_submission/dfthcsos/angle_k_9.kmb`

### Verifier Verification Modules
* **InvSqrt Verifier**: `/kaggle/input/google-verifiable-quantum-circuit-compilation/verifiers/invsqrt/verify_submission_invsqrt.py`
* **DQI Verifier**: `/kaggle/input/google-verifiable-quantum-circuit-compilation/verifiers/dqi/verify_submission_dqi.py`
* **DFTHC-SOS Verifier**: `/kaggle/input/google-verifiable-quantum-circuit-compilation/verifiers/dfthcsos/verify.py`

### Binary Core & Extension
* **Kickmix Library**: `/kaggle/input/google-verifiable-quantum-circuit-compilation/kickmix/kickmix.so`

### Output Destination
* **Optimized Submission Artifacts**: `/kaggle/working/submission/` (e.g. `/kaggle/working/submission/invsqrt.kmb`, `/kaggle/working/submission/dqi.kmb`, `/kaggle/working/submission/dfthcsos/angle_k_0.kmb` ... `angle_k_9.kmb`)

## Flow
The complete optimization and verification lifecycle operates through the following sequential stages:

1. **Environment Initialization & Extension Import**:
   The Python execution environment appends `/kaggle/input/google-verifiable-quantum-circuit-compilation/kickmix` to `sys.path` and imports the `kickmix` C++ extension (`kickmix.so`). All execution is configured to run strictly on CPU (using Python 3.13 / C++ thread pools), explicitly disabling GPU acceleration dependencies.

2. **Circuit Ingestion (`.kmb` Loading)**:
   Target benchmark circuit files are read from `/kaggle/input/google-verifiable-quantum-circuit-compilation/sample_submission/`. The binary payload is deserialized into native `kickmix.Circuit` objects via the core `kickmix` C++ reader, reconstructing register definitions (`km.q` quantum registers, `km.b` classical registers) and operation ASTs.

3. **Compilation & Circuit Optimization (`kickmix.so` on CPU only)**:
   The circuit undergoes iterative compiler passes using `kickmix.CircuitBuilder`:
   * **Peephole Optimization**: Identity gate cancellation, adjacent Pauli simplification, and Toffoli/T-gate reductions.
   * **Commutation & Reordering**: Moving diagonal phases and commuting control gates to uncover cancellation opportunities.
   * **Ancilla Management & Routing**: Reclaiming workspace qubits returning to $|0\rangle$ and optimizing reaction depth.
   * All compilation routines run entirely on CPU.

4. **Correctness Check & Score Evaluation (Verifier Integration)**:
   The candidate optimized circuit is passed to the corresponding verifier module loaded from `/kaggle/input/google-verifiable-quantum-circuit-compilation/verifiers/`:
   * **Functional Correctness**: Verifies output phases/states match analytical targets (InvSqrt phase accuracy, DQI syndrome decoding & MBUC phase matching, DFTHC-SOS oracle streaming).
   * **Clean State Restoration**: Asserts input registers are unchanged and all workspace ancillas return to $|0\rangle$.
   * **Statistical Bound Verification**: For DQI, evaluates Clopper-Pearson error bounds $\varepsilon_+ < 1/16$ across test shots.
   * **Resource Scoring**: Computes the benchmark metric ($Q \cdot C$ for InvSqrt, $R \cdot Q^2 \cdot T$ for DQI, $\lambda_{\text{eff}} \cdot T_{\text{total}} \cdot Q_{\text{total}}$ for DFTHC-SOS).

5. **Saving Improved Artifacts**:
   If the verified circuit passes all correctness assertions and achieves a lower metric score than the preceding candidate, it is serialized via `kickmix.Circuit` into binary `.kmb` format and saved to the output path under `/kaggle/working/submission/`.

## External
* **Environment**: Kaggle CPU notebook runtime with Python 3.13.
* **Native Binaries**: `/kaggle/input/google-verifiable-quantum-circuit-compilation/kickmix/kickmix.so` (requires glibc, libstdc++).
* **Environment Variables**: `PYTHONPATH`, `OMP_NUM_THREADS` (for CPU multi-threading configuration).

## Least Confident Decisions
1. **Verification Module Invocation Mechanism (Subprocess vs Direct Import)**: Choosing between executing verifier scripts via `subprocess.run` Python CLI calls vs directly importing verification functions (`verify_submission_*`). Direct import minimizes process spawning overhead during iteration loops but risks namespace collisions, whereas subprocess isolation strictly mirrors Kaggle scoring execution.
2. **Phase Precision Handling in InvSqrt Decomposition**: Deciding whether to maintain explicit `Z_POW` turns during compiler passes or decompose them into fixed-precision Clifford+T sequences. The InvSqrt verifier evaluates `Z_POW` using a synthetic rotation error margin (`rotation_eps`), so premature decomposition on CPU might inflate T-count unnaturally.
3. **MBUC Classical Feedback Preserving in DQI Rewrites**: Deciding how aggressively to commute or reorder operations touching classical registers (`km.b`) during DQI optimization passes without invalidating the MBUC global phase equation $(-1)^{\sum_j \text{popcount}(e_j \land M_j)}$.

---

Approve Gate 2, or what should change?
