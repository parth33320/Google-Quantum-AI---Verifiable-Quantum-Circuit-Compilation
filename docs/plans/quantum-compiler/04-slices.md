# Vertical Slices: Quantum Compiler Pipeline

All paths use `/kaggle/input/google-verifiable-quantum-circuit-compilation/` as the root directory.

## Slice 1: Tracer Bullet (`invsqrt`)
- Load `invsqrt.kmb` from `/kaggle/input/google-verifiable-quantum-circuit-compilation/sample_submission/invsqrt.kmb`.
- Run `invsqrt.kmb` through `kickmix.so` and verify with `/kaggle/input/google-verifiable-quantum-circuit-compilation/verifiers/invsqrt/verify_submission_invsqrt.py`.
- Print pass or fail result.

## Slice 2: Optimization Loop (`invsqrt` only)
- Implement optimization loop for `invsqrt` circuit only (peephole cancellation, phase commutation, Toffoli/T-gate reductions).
- Validate optimized circuit against `/kaggle/input/google-verifiable-quantum-circuit-compilation/verifiers/invsqrt/verify_submission_invsqrt.py`.
- Verify resource score reduction and PASS status.

## Slice 3: Full Benchmark Support (`dqi` & `dfthcsos`)
- Extend optimizer pipeline to support `dqi` (`/kaggle/input/google-verifiable-quantum-circuit-compilation/sample_submission/dqi.kmb`) and `dfthcsos` (`/kaggle/input/google-verifiable-quantum-circuit-compilation/sample_submission/dfthcsos/`).
- Validate `dqi` using `/kaggle/input/google-verifiable-quantum-circuit-compilation/verifiers/dqi/verify_submission_dqi.py`.
- Validate `dfthcsos` using `/kaggle/input/google-verifiable-quantum-circuit-compilation/verifiers/dfthcsos/verify.py`.
- Ensure all 3 benchmarks pass verification and output formatted results.
