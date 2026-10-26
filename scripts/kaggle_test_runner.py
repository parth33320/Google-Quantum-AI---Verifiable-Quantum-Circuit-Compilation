import os
import shutil
import subprocess
import sys

REPO_URL = "https://github.com/parth33320/Google-Quantum-AI---Verifiable-Quantum-Circuit-Compilation.git"
REPO_DIR = "Google-Quantum-AI---Verifiable-Quantum-Circuit-Compilation"

def main():
    print(f"=== Step 1: Cloning repository from {REPO_URL} ===")
    if os.path.exists(REPO_DIR):
        print(f"Directory {REPO_DIR} already exists. Removing it for a fresh clone...")
        shutil.rmtree(REPO_DIR, ignore_errors=True)

    clone_cmd = ["git", "clone", REPO_URL, REPO_DIR]
    res = subprocess.run(clone_cmd, capture_output=True, text=True)
    print(res.stdout)
    if res.stderr:
        print(res.stderr, file=sys.stderr)

    if res.returncode != 0:
        print(f"Error cloning repository (exit code {res.returncode})", file=sys.stderr)
        sys.exit(res.returncode)

    test_script = "src/dqi_test_niters.py"
    target_path = os.path.join(REPO_DIR, test_script)

    print(f"\n=== Step 2: Running {test_script} ===")
    if not os.path.exists(target_path):
        print(f"Error: {test_script} does not exist in the repository.", file=sys.stderr)
        src_dir = os.path.join(REPO_DIR, "src")
        if os.path.exists(src_dir):
            print(f"Available files in src/: {os.listdir(src_dir)}")
        sys.exit(1)

    env = os.environ.copy()
    env["PYTHONPATH"] = f".:{env.get('PYTHONPATH', '')}"

    run_cmd = [sys.executable, test_script]
    proc = subprocess.Popen(
        run_cmd,
        cwd=REPO_DIR,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    print("=== Step 3: Printing Output ===")
    if proc.stdout:
        for line in proc.stdout:
            print(line, end="")

    proc.wait()
    print(f"\n=== Process finished with exit code {proc.returncode} ===")
    if proc.returncode != 0:
        sys.exit(proc.returncode)

if __name__ == "__main__":
    main()
