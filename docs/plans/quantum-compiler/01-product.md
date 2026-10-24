# Product Specification: Quantum Compiler Verifiers & Sample Submissions

This document details the structure, purpose of `.kmb` files, verifier checks, and input/output contracts for all benchmarks in `verifiers/` and `sample_submission/`.

---

## 1. What Each `.kmb` File Is For

`.kmb` files are binary serializations of `kickmix.Circuit` objects representing quantum circuits for specific computational tasks.

### 1.1 `sample_submission/invsqrt.kmb`
* **Benchmark**: Benchmark I (InvSqrt / Newton-Raphson Phasing).
* **Purpose**: Implements quantum phasing by $\theta(x) = \frac{\beta}{\sqrt{x}}$ for integers $x \in [1, \text{max\_x}]$, where $\text{max\_x} = 3(2^{n_p} - 2)^2 = 3,133,452$ ($n_p = 10$).
* **Function**: Given input state $|x\rangle|0\dots0\rangle$, it applies the phase shift $\exp\left(2\pi i \frac{\beta}{\sqrt{x}}\right) |x\rangle|0\dots0\rangle$ and restores all workspace registers and input state $x$.

### 1.2 `sample_submission/dqi.kmb`
* **Benchmark**: Benchmark II (DQI / Decoded Quantum Interferometry).
* **Purpose**: Implements a reversible Reed-Solomon syndrome decoder with Measurement-Based Uncomputation (MBUC).
* **Function**: Accepts quantum syndrome registers $S_0, \dots, S_{n-1}$ over $GF(2^b)$ and classical MBUC outcome registers $E_0, \dots, E_{m-1}$. Computes error locations/evaluators using synchronized Extended Euclidean Algorithm (EEA) and Chien search + Forney formula, applies the MBUC global phase $(-1)^{\sum_j \text{popcount}(e_j \land M_j)}$, and restores syndrome/ancilla qubits.

### 1.3 `sample_submission/dfthcsos/angle_k_0.kmb` through `angle_k_9.kmb`
* **Benchmark**: Benchmark III (DFTHC-SOS / Double-Factorized Tensor Hypercontraction Sum-of-Squares for FeMoCo).
* **Purpose**: Family of $K = 10$ sequential XOR oracle circuits for Task 3 of DFTHC-SOS.
* **Function**:
  * Circuit $k$ maps $|a\rangle|z\rangle \to |a\rangle|z \oplus \delta[k, a]\rangle$, where $\delta[k, a] = \text{batch}[k, a] \oplus \text{batch}[k-1, a]$ and $\text{batch}[k, a]$ holds batch $k$ of $J=8$ angle words (width $\text{brot}=12$ bits each) for address $a < 76 + R \cdot B = 3976$.
  * Sequential evaluation $k=0 \dots 9$ loads angle words into registers `word_0`..`word_7`. Sequential reverse evaluation $k=9 \dots 0$ clears the word registers back to zero.

---

## 2. What Each Verifier Script Checks

### 2.1 Benchmark I Verifier (`verifiers/invsqrt/verify_submission_invsqrt.py`)
* **Register Schema**:
  * Must contain exactly one register named `'x'` containing `width` ($2 n_p + 2 = 22$) distinct quantum qubits (`km.q`).
  * All other qubits are scratch ancillas (`km.q`). No other registers or classical bits are allowed in `'x'`.
* **State Restoration & Scratch Cleanup**:
  * After running circuit on $|x\rangle|0\dots0\rangle$, register `'x'` must be unchanged ($|x\rangle$).
  * All scratch qubits must return to $|0\rangle$.
* **Phase Accuracy**:
  * Tracks output phase $\theta$ in fixed-point $2^{-64}$ turns.
  * Ensures phase error $|\text{error}(x)| = |\theta - \text{target}(x)|$ is within tolerance:
    $$\text{tol}(x) = 2^{-\text{precision\_bits}} \frac{\beta}{\sqrt{x}} \pmod 1$$
* **Rotation Synthesis Error Margin**:
  * Ensures non-Clifford `Z_POW` rotations leave enough error budget: $\pi \cdot \text{min\_margin} / 2^{64} / n_{\text{rot}} > 0$.
* **Scoring Metric**:
  * Score = $Q \cdot C$ (where $Q = \text{num\_qubits}$, $C = \text{Toffolis} + \frac{T}{4}$). Lower is better.

### 2.2 Benchmark II Verifier (`verifiers/dqi/verify_submission_dqi.py`)
* **Register Schema**:
  * Exactly $n$ quantum syndrome registers named `S0`..`S{n-1}` (each width $b = \text{degree}$ qubits).
  * Exactly $m$ classical bit registers named `E0`..`E{m-1}` (each width $b$ classical bits `km.b`).
  * Disjoint registers; no overlap allowed.
* **Gate Restrictions**:
  * `Z_POW` gates are strictly forbidden.
* **MBUC Phase & State Restoration**:
  * Syndromes $S_0, \dots, S_{n-1}$ must be completely restored to initial values across all shots.
  * Ancilla qubits must return to $|0\rangle$.
  * Phase flip must match target $(-1)^{\sum_j \text{popcount}(e_j \land M_j)}$.
* **Error Rate & Statistical Bound**:
  * Calculates value errors and phase errors over `num_shots` (default 102,400).
  * Computes one-sided Clopper-Pearson upper bound $\varepsilon_+$ at confidence $1 - 2^{\text{log2\_delta}}$ ($\delta = 2^{-128}$).
  * Requires $\varepsilon_+ < 1/16$; fails with `AssertionError` if $\varepsilon_+ \ge 1/16$.
* **Scoring Metric**:
  * Score = $R(\varepsilon_+) \cdot Q^2 \cdot T$, where $R(\varepsilon) = \frac{\ln 2}{-\ln(1/2 + 2\sqrt{\varepsilon})}$, $Q = \text{num\_qubits}$, and $T = \text{mean Toffolis/shot}$.

### 2.3 Benchmark III Verifier (`verifiers/dfthcsos/verify.py` & `scoreinfra/circuits.py`)
* **Register Contract**:
  * Register `"selection"` with exactly $\lceil\log_2(76 + R \cdot B)\rceil$ qubits.
  * Registers `"word_0"` .. `"word_{J-1}"` (contiguous $0 \dots J-1$), each with width $\text{brot}$ qubits.
  * All other qubits are workspace (must start/end in $|0\rangle$).
  * No `Z_POW` gates (all phases must be multiples of $\pi$).
* **Circuit Execution & Oracle Consistency**:
  * Forward pass ($k=0 \dots K-1$) must stream angle word batches into `word_j`.
  * Words loaded for the same address must be deterministic across shots.
  * Padding words beyond $N-1 = 75$ must be zero.
  * Reverse pass ($k=K-1 \dots 0$) must clear `word_j` back to 0.
  * Workspace must be clean and phase unflipped at every stage.
* **Accuracy & Domain Gates**:
  * One-body residual $\text{error}_1 \le 0.020$ Ha (20 mHa).
  * Two-body residual $\text{error}_2 \le 0.020$ Ha (20 mHa).
  * SOS gap $E_{\text{gap}} = E_{\text{upper}} - E_{\text{SOS}} \in (0, 2\Lambda)$.
  * Strict floors: raw $\Lambda > 49.0$ and $E_{\text{gap}} > 3.914898$ Ha.
  * Maximum qubit cap: $\max_k \text{num\_qubits}(\text{ANGLE}_k) \le 128$.
* **Scoring Metric**:
  * Score = $\lambda_{\text{eff}} \cdot T_{\text{total}} \cdot Q_{\text{total}}$ where $\lambda_{\text{eff}} = \sqrt{E_{\text{gap}}(2\Lambda - E_{\text{gap}})}$.

---

## 3. Expected Inputs and Outputs

### 3.1 InvSqrt Verifier Input/Output Contract
* **CLI Command**:
  ```bash
  python verifiers/invsqrt/verify_submission_invsqrt.py submission.kmb [options]
  ```
* **CLI Inputs / Options**:
  * `circuit_file` (positional): Path to `.kmb` or `.kmx` circuit.
  * `--format`: `auto` (default), `kmb`, or `kmx`.
  * `--n-p`: Bits per momentum component (default: 10).
  * `--beta`: Fraction phase scaling (default: 1).
  * `--precision-bits`: Relative precision bits (default: 24).
  * `--shots-per-x`: Shots per $x$ (default: 64).
  * `--salt`: String salt for RNG seed derivation.
  * `--seed`: Explicit RNG seed integer.
  * `--batch-size`: Simulator batch size (default: 256).
  * `--max-workers`: Parallel worker count.
* **Output Format** (JSON on stdout):
  * On Success:
    ```json
    {
      "status": "PASS",
      "score": float,
      "toffoli_equivalent": float,
      "toffoli_count": float,
      "max_toffoli_count": int,
      "t_count": float,
      "rotation_count": float,
      "rotation_eps": float,
      "num_qubits": int,
      "reaction_depth": int,
      "num_ops": int,
      "verified_shots": int,
      "worst_error_over_tolerance": float,
      "worst_x": int,
      "circuit_sha256": "hex_string"
    }
    ```
  * On Failure:
    ```json
    {
      "status": "FAIL",
      "error": "error message"
    }
    ```

### 3.2 DQI Verifier Input/Output Contract
* **CLI Command**:
  ```bash
  python verifiers/dqi/verify_submission_dqi.py submission.kmb [options]
  ```
* **CLI Inputs / Options**:
  * `circuit_file` (positional): Path to `.kmb` or `.kmx` circuit file.
  * `--format`: `auto` (default), `kmb`, or `kmx`.
  * `--m`: Codeword length (default: 4095).
  * `--n`: Number of syndromes (default: 70).
  * `--degree`: Field degree $b$ for $GF(2^b)$ (default: 12).
  * `--r`: Accepted values per constraint $|F_i|$ (default: 2016).
  * `--num-shots`: Total verification shots (default: 102,400).
  * `--batch-size`: Simulator batch size (default: 256).
  * `--log2-delta`: Clopper-Pearson confidence log2 delta (default: -128.0).
  * `--salt` / `--seed`: Salt string or explicit seed.
  * `--max-workers`: Max processes (default: 4).
* **Output Format** (JSON on stdout):
  * On Success:
    ```json
    {
      "status": "PASS",
      "score": float,
      "m": int,
      "n": int,
      "degree": int,
      "r": int,
      "verified_shots": int,
      "value_errors": int,
      "phase_errors": int,
      "empirical_error_rate": float,
      "effective_error_rate": float,
      "log2_delta": float,
      "repetition_factor": float,
      "mean_error_weight": float,
      "toffoli_count": float,
      "max_toffoli_count": int,
      "reaction_depth": int,
      "num_ops": int,
      "shot_operation_counts": dict,
      "num_qubits": int,
      "num_bits": int,
      "circuit_sha256": "hex_string"
    }
    ```
  * On Failure:
    ```json
    {
      "status": "FAIL",
      "error": "error message"
    }
    ```

### 3.3 DFTHC-SOS Verifier Input/Output Contract
* **CLI Command**:
  ```bash
  python verifiers/dfthcsos/verify.py RUN_DIR/ [submission.npz] [options]
  ```
* **CLI Inputs / Options**:
  * `inputs` (positional): Path to submission directory containing `angle_k_*.kmb`/`.kmx` and `submission.npz`, or explicit factorization `.npz` and circuit paths.
  * `--tree-edges`: Path to `.npy`/`.npz` containing $(75, 2)$ Givens tree.
  * `--format`: `auto` (default), `kmb`, or `kmx`.
  * `--shots-per-address`: Shots per address (default: 64).
  * `--salt` / `--seed`: Salt string or explicit seed integer.
* **Output Format** (JSON on stdout):
  * On Success:
    ```json
    {
      "status": "PASS",
      "score": float,
      "lambda_eff": float,
      "toffoli_count": float,
      "num_qubits": int,
      "brot": int,
      "batch_size": int,
      "num_circuits": int,
      "reaction_depth": int,
      "num_ops": int,
      "verified_shots": int,
      "submission_sha256": "hex_string",
      "resources": dict,
      "metrics": dict
    }
    ```
  * On Failure:
    ```json
    {
      "status": "FAIL",
      "error": "error message"
    }
    ```
