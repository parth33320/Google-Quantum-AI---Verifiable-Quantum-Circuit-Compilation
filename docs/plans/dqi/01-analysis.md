# DQI Reed-Solomon MBUC Decoder Analysis

This document provides an analysis of the reversible Reed-Solomon syndrome decoder for Decoded Quantum Interferometry (DQI), based on `verifiers/dqi/dqi_reference_circuit.py` and `verifiers/dqi/verify_submission_dqi.py`.

---

## 1. Registers and Qubit Requirements

The circuit uses two main categories of registers: persistent problem registers and auxiliary/scratch registers.

### Quantum Registers
For field degree $b = \text{degree}$, syndrome count $n$, and extended polynomial length $m_{\text{eea}} = n + 3$:

| Register Name | Count / Type | Qubits per Register | Total Qubits ($n=70, b=12$) | Purpose / Description |
| :--- | :--- | :--- | :--- | :--- |
| **`syndromes` ($S_0 \dots S_{n-1}$)** | $n$ Quantum Regs | $b$ qubits | $70 \times 12 = 840$ | Holds initial syndrome values $S_i = \sum_j e_j \alpha^{(i+1)j}$. |
| **`reg_a[:3]` ($reg\_a[0..2]$)** | 3 Quantum Regs | $b$ qubits | $3 \times 12 = 36$ | Allocated quantum padding for $A(x)$ polynomial. ($reg\_a[3..n+2]$ alias $S_0..S_{n-1}$). |
| **`reg_b` ($reg\_b[0..n+2]$)** | $n+3$ Quantum Regs | $b$ qubits | $73 \times 12 = 876$ | Holds polynomial $B(x)$ and auxiliary polynomials for EEA. |
| **`n_A`** | 1 Quantum Reg | $\text{logm}$ qubits | 8 | Tracks degree of polynomial $A(x)$ ($\text{logm} = (n+3).\text{bit\_length}() + 1$). |
| **`n_B`** | 1 Quantum Reg | $\text{logm}$ qubits | 8 | Tracks degree of polynomial $B(x)$. |
| **`n_a`** | 1 Quantum Reg | $\text{logm}$ qubits | 8 | Tracks degree of auxiliary polynomial $a(x)$. |
| **`n_b`** | 1 Quantum Reg | $\text{logm}$ qubits | 8 | Tracks degree of auxiliary polynomial $b(x)$. |
| **`n_q`** | 1 Quantum Reg | $\text{logm}$ qubits | 8 | Tracks quotient degree $q(x)$. |
| **`flag`** | 1 Qubit | 1 qubit | 1 | Flag toggled when active EEA sub-step completes. |
| **`counter`** | 1 Quantum Reg | 2 qubits | 2 | 2-bit counter tracking the 4 sub-steps (0..3) of an EEA iteration. |
| **`halting_counter`** | 1 Quantum Reg | $\lceil\log_2(N_{\text{iters}})\rceil$ qubits | 8 | Counter tracking halting state after EEA termination condition is reached ($N_{\text{iters}}=222$). |

* **Total persistent/scratch quantum qubits allocated**: $840 + 36 + 876 + 40 + 1 + 2 + 8 = 1,803\text{ qubits}$.

### Classical Registers
| Register Name | Count / Type | Bits per Register | Total Bits ($m=4095, b=12$) | Purpose / Description |
| :--- | :--- | :--- | :--- | :--- |
| **`error_mbuc` ($E_0 \dots E_{m-1}$)** | $m$ Classical Regs | $b$ bits | $4095 \times 12 = 49,140$ | Holds MBUC measurement outcomes $M_0 \dots M_{m-1}$. |

---

## 2. Toffoli Gate Breakdown and Dominant Stage

For default parameters ($m = 4095, n = 70, b = 12$), the reference circuit generates **5,725,461 Toffoli-like gates**.

### Stage Breakdown
1. **Stage 1: Forward EEA** (`initial_shift` + `forward_eea`):
   - Left-aligns syndromes and executes $N_{\text{iters}} = 222$ synchronized EEA iterations.
   - Computes polynomial division ratios over $\text{GF}(2^{12})$, sweeps across 73 polynomial array slots, updates degree metadata, and shifts/swaps polynomial arrays.
   - Accounts for **~2,862,600 Toffolis (~50.0% of total)**.

2. **Stage 2: Chien Search and Forney MBUC** (`chien_forney_mbuc`):
   - Evaluates error-locator polynomial $\sigma(x)$ and error-evaluator polynomial $\omega(x)$ across all $m = 4095$ codeword positions.
   - Computes field inverses via scaffolds and applies MBUC phase kickback $(-1)^{\text{popcount}(e_j \ \& \ M_j)}$.
   - Accounts for **~260 Toffolis (< 0.01% of total)** because classical conditional checks bypass unneeded operations and field inversions are evaluated in-place.

3. **Stage 3: Reverse EEA** (`reverse_eea` + `uncompute_initial_shift`):
   - Runs 222 adjoint EEA iterations and reverse shifts to uncompute polynomials $\sigma(x)$ and $\omega(x)$ and restore syndrome registers $S_0 \dots S_{n-1}$.
   - Accounts for **~2,862,600 Toffolis (~50.0% of total)**.

### Conclusion on Dominance
The **Synchronized Extended Euclidean Algorithm (EEA)** stages (Forward EEA + Reverse EEA) dominate the circuit cost, accounting for **> 99.9%** (over 5.725 million) of all Toffoli gates.

---

## 3. Persistent vs. Scratch Registers

### Persistent Registers
Registers that are part of the input/output contract of the circuit and must be preserved across execution:
* **`syndromes` ($S_0 \dots S_{n-1}$)**: Quantum input registers. They undergo transformations during forward shift and EEA, but are strictly restored to their original quantum state by `reverse_eea` and `uncompute_initial_shift` before circuit completion (verified by `verify_submission_dqi.py`).
* **`error_mbuc` ($E_0 \dots E_{m-1}$)**: Classical input registers holding measurement outcomes. They are read-only controls during phase kickbacks and remain unchanged.

### Scratch Registers
Registers allocated at circuit setup or dynamically within subroutines, which are guaranteed to be uncomputed and returned to $|0\rangle$ (or freed) before completion:
* **`reg_a[:3]`**: Quantum padding registers for $A(x)$.
* **`reg_b[0..n+2]`**: Quantum polynomial registers for $B(x)$ and auxiliary polynomials.
* **Degree Metadata (`n_A`, `n_B`, `n_a`, `n_b`, `n_q`)**: Width-$\text{logm}$ quantum registers tracking degrees.
* **Execution Status Qubits (`flag`, `counter`, `halting_counter`)**: Qubits tracking EEA sub-step sequence and halting conditions.
* **Subroutine Ancillas**: Temporary qubits allocated for division scaffolds (`scaffold`), inversion scaffolds (`inverse_chain`), control gating (`is_c3`, `is_hc_zero`, `ctrl`), and phase evaluation (`located`, `sigma_prime_inv`). All are explicitly freed and returned to $|0\rangle$.

---

## 4. Extended Euclidean Algorithm (EEA) Iteration Count Formula

The number of synchronized EEA iterations $N_{\text{iters}}$ required by the reference decoder is defined by `default_n_iters(n_syndromes)` in `verifiers/dqi/dqi_reference_circuit.py`:

$$N_{\text{iters}}(n) = 3 \times (n + 1) + 9 = 3n + 12$$

Where $n = \text{n\_syndromes}$ is the number of quantum syndrome registers.

### Evaluation for Benchmark Parameters
For the default competition benchmark setting $n = 70$:

$$N_{\text{iters}}(70) = 3 \times (70 + 1) + 9 = 3 \times 71 + 9 = 213 + 9 = 222 \text{ iterations.}$$

Both the forward EEA stage and reverse EEA stage execute exactly 222 iterations, resulting in a total of 444 EEA iteration step evaluations.
