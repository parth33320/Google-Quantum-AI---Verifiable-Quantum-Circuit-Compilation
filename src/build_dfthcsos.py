"""Script to build DFTHCSOS circuits and save to /kaggle/working/submission/dfthcsos/."""

import os
import sys
import importlib.util

# Dynamic loading of kickmix module
kickmix_so = '/kaggle/input/competitions/google-verifiable-quantum-circuit-compilation/kickmix/kickmix.so'
if not os.path.exists(kickmix_so):
    # Fallback to local path if running outside standard competition path setup
    kickmix_so = os.path.abspath(os.path.join(os.path.dirname(__file__), '../kickmix/kickmix.so'))

spec = importlib.util.spec_from_file_location('kickmix', kickmix_so)
km = importlib.util.module_from_spec(spec)
sys.modules['kickmix'] = km
spec.loader.exec_module(km)

# Adjust path to find verifiers module if needed
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from verifiers.dfthcsos.example_submission.angle_k_reference_circuit import (
    build_angle_k_family,
    load_angle_words,
    write_kmx_family,
)

def main():
    brot = 12
    batch_size = 8

    # Paths to submission.npz and output directory
    submission_npz = '/kaggle/input/competitions/google-verifiable-quantum-circuit-compilation/sample_submission/dfthcsos/submission.npz'
    if not os.path.exists(submission_npz):
        submission_npz = os.path.join(repo_root, 'verifiers/dfthcsos/example_submission/FeMoCo76o113e/submission.npz')
        if not os.path.exists(submission_npz):
            submission_npz = os.path.join(repo_root, 'sample_submission/dfthcsos/submission.npz')

    out_dir = '/kaggle/working/submission/dfthcsos/'
    os.makedirs(out_dir, exist_ok=True)

    angle_words = load_angle_words(submission_npz)
    circuits = build_angle_k_family(angle_words, brot=brot, batch_size=batch_size)
    paths = write_kmx_family(circuits, out_dir, format='kmb', overwrite=True)

    print(f"Successfully saved {len(paths)} DFTHCSOS circuits to {out_dir}")

if __name__ == '__main__':
    main()
