# DQI Decoder Optimization Targets Analysis

This document analyzes `verifiers/dqi/dqi_reference_circuit.py`, focusing on the `ProosAndZalkaDecoder` class and its method `build_syndrome_decoding_mbuc`.

---

## Question 1: GF(2^12) Multiplications per EEA Iteration and Builder Calls

### 1.1 Number of GF(2^12) Multiplications per EEA Iteration
In `build_syndrome_decoding_mbuc`, each EEA iteration runs `_multiply_and_add_or_sub`.

Inside `_multiply_and_add_or_sub`:
- Multiplications occur within the loop over `i in order` (where `order` has $m = n + 3$ positions, e.g., $m = 73$ for $n = 70$).
- For each position $i$, if `multiplies = (i < lim_a or i >= 2)` holds true (where `lim_a = min(m - 2, it // 2 + 1)`):
  - `builder.ixor_gf2_mul(q_i, reg_a[i], target=reg_b[i], field=gf, control=mul)` is called.
- For $m = 73$ ($n = 70$), `lim_a` ranges from $1$ to $37$.
  - When $i < \text{lim\_a}$, position $i$ is multiplied.
  - When $i \ge 2$, position $i$ is multiplied.
  - Notice that positions $0$ and $1$ are excluded when $i \ge \text{lim\_a}$. Specifically, position $0$ is multiplied if $0 < \text{lim\_a}$ (which is always true since $\text{lim\_a} \ge 1$), and position $1$ is multiplied if $1 < \text{lim\_a}$ (which is true for $\text{it} \ge 2$).
  - Thus, depending on iteration $\text{it}$, either 72 (for $\text{it} < 2$) or 73 (for $\text{it} \ge 2$) multiplications by $q_i$ via `ixor_gf2_mul` occur per EEA iteration.
- Note on Division / Scaffold:
  - `accumulate_quotient` calls `init_gf2_div_with_scaffold` twice per iteration (once for leading term, once for trailing term). `init_gf2_div_with_scaffold` computes division via inversion + multiplication scaffold, but uses division primitives internally (`init_gf2_div_with_scaffold` / `del_gf2_div_with_scaffold`), not explicit `gf2_imul` or `init_gf2_mul` builder methods.

### 1.2 Builder Method Calls
Listing of all exact builder calls in `verifiers/dqi/dqi_reference_circuit.py` using `gf2_imul`, `init_gf2_mul`, `del_gf2_mul`, or `gf2_idiv`:

1. `builder.ixor_gf2_mul(q_i, reg_a[i], target=reg_b[i], field=gf, control=mul)`
   - Called in `_multiply_and_add_or_sub` (lines 280-281 & 291-292).
2. `builder.gf2_imul(step, target=reg_b[k], field=gf)`
   - Called in `_chien_search_and_forney_mbuc` (line 427) during Chien search stepping.
3. `builder.gf2_idiv(gf.pow(step, num_positions - 1), target=reg_b[k], field=gf)`
   - Called in `_chien_search_and_forney_mbuc` (lines 430-431) for unstepping multipliers.

*(Note: `init_gf2_mul` and `del_gf2_mul` are NOT called anywhere in `dqi_reference_circuit.py`).*

---

## Question 2: Qubit Layout of `reg_b`, Qubit Count, and Sharing with `reg_a`

### 2.1 Qubit Layout of `reg_b`
- `reg_b` is initialized in `build_syndrome_decoding_mbuc` as:
  `reg_b = [builder.alloc_qubits(degree) for _ in range(m)]`
- It is a list of $m = n + 3$ quantum registers, each of length `degree` (12 qubits for $\text{GF}(2^{12})$).
- Total qubits allocated for `reg_b`: $m \times \text{degree} = (n + 3) \times \text{degree}$.
  - For $n = 70, b = 12$: $73 \times 12 = 876 \text{ qubits}$.

### 2.2 Sharing Qubits Between `reg_b` and `reg_a`
- `reg_a` is defined as:
  `reg_a = [builder.alloc_qubits(degree) if i < 3 else syndromes[i - 3] for i in range(m)]`
  - $reg\_a[0..2]$ are newly allocated scratch registers ($3 \times 12 = 36$ qubits).
  - $reg\_a[3..m-1]$ alias the $n$ quantum `syndromes` registers.
- **Can any qubits of `reg_b` be shared with `reg_a`?**
  - During the EEA, `reg_a` and `reg_b` represent two distinct polynomial state registers $A(x)$ and $B(x)$ that undergo cross-operations (e.g. `reg_b ^= q_i * reg_a` and `cswap(reg_a, reg_b)`). Therefore, during EEA execution, all elements of `reg_b` must be distinct from `reg_a`.
  - However, $reg\_a[0..2]$ are local scratch qubits allocated solely for the decoder. `reg_b` is also fully allocated as scratch.
  - While `reg_a` and `reg_b` cannot overlap during EEA, after EEA and Chien search/Forney phase, uncomputation returns `reg_b` and $reg\_a[0..2]$ to $|0\rangle$.
  - In terms of memory footprint optimization, if intermediate values in $reg\_a[0..2]$ or `reg_b` are not active simultaneously across different sub-routines, scratch allocations could potentially be reused or pooled, but during the active EEA loop, $A(x)$ and $B(x)$ registers must remain disjoint.

---

## Question 3: Scratch Qubits Allocated Inside Each EEA Iteration

Inside each EEA iteration (`_synchronized_eea`), several temporary qubits are dynamically allocated and freed within subroutines:

1. **Step Controls & Halting Controls**:
   - `is_c3 = builder.alloc_qubits(1)[0]` (1 qubit) - Allocated in `_synchronized_eea`.
   - `is_hc_zero = builder.alloc_qubits(1)[0]` (1 qubit) - Allocated in `_synchronized_eea`.
   - `ctrl = builder.alloc_qubits(4)` (4 qubits) - Allocated in `_counter_controls`.
2. **`_update_flag`**:
   - `aux = builder.alloc_qubits(1)[0]` (1 qubit).
3. **`_multiply_and_add_or_sub`**:
   - `q_i = builder.alloc_qubits(gf.degree)` (`degree` qubits, e.g. 12 qubits).
   - `ratio, scaffold = builder.init_gf2_div_with_scaffold(...)` - Inside `accumulate_quotient`, allocates `ratio` (`degree` qubits) and `scaffold` qubits for division.
   - `mul = builder.alloc_qubits(1)[0]` (1 qubit) - Used in `sweep_positions`.
   - `both = builder.alloc_qubits(1)[0]` (1 qubit) - Temporarily allocated when `len(swaps) > 1`.
4. **`_shift_b_array_right`**:
   - `nf = builder.alloc_qubits(2)` (2 qubits).
   - `ctrl_nB = builder.alloc_qubits(1)[0]` (1 qubit).
   - `do_shift = builder.alloc_qubits(1)[0]` (1 qubit).
5. **`_update_metadata`**:
   - `nf = builder.alloc_qubits(2)` (2 qubits).
6. **`_swap_a_and_b`**:
   - `swap_ctrl = builder.alloc_qubits(1)[0]` (1 qubit).
7. **`_update_halting_counter`**:
   - `work = builder.alloc_qubits(3)` (3 qubits).

### Reuse Opportunity
All these temporary qubits (`is_c3`, `is_hc_zero`, `ctrl`, `aux`, `q_i`, `mul`, `both`, `nf`, `ctrl_nB`, `do_shift`, `swap_ctrl`, `work`) are allocated and freed on every single EEA iteration (444 times total across forward + reverse EEA).
Allocating a static scratchpad register once outside the EEA loop and reusing it across all iterations would eliminate thousands of dynamic `alloc_qubits` / `free` allocations.

---

## Question 4: `default_n_iters` Return Value and Iteration Count Reduction

### 4.1 Return Value of `default_n_iters`
The function `default_n_iters(n_syndromes)` is defined as:
```python
def default_n_iters(n_syndromes: int) -> int:
  return 3 * (n_syndromes + 1) + 9
```
- For $n = 70$: `default_n_iters(70) = 3 * (70 + 1) + 9 = 222`.

### 4.2 Can Iteration Count Be Reduced While Decoding Correctly?
- **Theoretical EEA Bound**: The standard Extended Euclidean Algorithm for Reed-Solomon decoding with $n = 2t$ syndromes requires at most $t$ division steps. In synchronized EEA with degree tracking and shift steps, the maximum number of degree reduction steps to find $\sigma(x)$ with $\deg(\sigma) \le t$ is bounded by $O(n)$.
- **Why `3 * (n + 1) + 9` is Conservative**:
  - The constant factor 3 accounts for sub-steps per division round (shift, divide, swap).
  - The +9 additive offset provides extra safety margin for alignment and halting counter synchronization.
- **Reduction Possibilities**:
  - For typical error weights $e \le t = n/2 = 35$, EEA terminates much earlier than 222 iterations.
  - If we only need to guarantee worst-case correctness for up to $t$ errors, formal degree bounds show that degree reduction completes in fewer total sub-steps (e.g. $2n + C$ or $3n/2 + C$ depending on maximum degree alignment).
  - Empirical testing on syndrome evaluation sets can determine the strict minimal $N_{\text{iters}}$ threshold needed for 100% decoding success on valid error patterns, potentially cutting $N_{\text{iters}}$ significantly (e.g., from 222 down to ~110-150), which directly reduces Toffoli count by the same ratio.

---

## 3 Least Confident Answers

1. **Exact lower bound for reduced `n_iters` (Question 4.2)**: While $N_{\text{iters}} = 222$ is conservative, the exact minimum number of iterations $N_{\text{min}}$ that guarantees zero decoding failures across all worst-case $t$-error patterns without modifying the inner loop control logic requires empirical verification on test circuits.
2. **Scaffold qubit count in `init_gf2_div_with_scaffold` (Question 3)**: The exact number of auxiliary qubits allocated inside `kickmix`'s C++ binary for `init_gf2_div_with_scaffold` depends on the underlying GF(2^b) division implementation in `kickmix.so`.
3. **Sharing/overlapping `reg_a` padding and `reg_b` scratch (Question 2.2)**: Whether `reg_a[:3]` and `reg_b` can share underlying physical qubits depends on whether `kickmix` circuit builder performs automated qubit alias/reuse optimizations or requires distinct qubit ID handles for `cswap` / `gf2_iadd` operations.
