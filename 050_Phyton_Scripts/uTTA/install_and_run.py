import os
import sys
import glob
import subprocess
import venv
from pathlib import Path

# Path definitions
BASE_DIR = Path(__file__).parent.resolve()
VENV_DIR = BASE_DIR / ".venv"
LOG_FILE = BASE_DIR / "install_log.txt"
REQS_FILE = BASE_DIR / "pyproject.toml"

# Python-Executable im venv ermitteln (Betriebssystem-Unterscheidung)
if sys.platform == "win32":
    VENV_PYTHON = VENV_DIR / "Scripts" / "python.exe"
else:
    VENV_PYTHON = VENV_DIR / "bin" / "python"

def log(message: str):
    """Simultaneous output to console and logfile"""
    print(message)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(message + "\n")

def main():
    # create virtual environment
    if not VENV_DIR.exists():
        log("[INFO] Creating Virtual Environment...")
        builder = venv.EnvBuilder(with_pip=True)
        builder.create(VENV_DIR)
        log("[OK] Virtual Environment created.")

    # Upgrade Pip
    log("[STEP 2] Update-Check (Pip & Requirements)")
    subprocess.run([str(VENV_PYTHON), "-m", "pip", "install", "--upgrade", "pip"], stdout=subprocess.DEVNULL)

    # Install pyproject.toml dependencies
    if REQS_FILE.exists():
        log(f"[INFO] Reading dependencies from {REQS_FILE.name}...")
        # Uses tomllib
        import tomllib
        with open(REQS_FILE, "rb") as f:
            data = tomllib.load(f)
        
        deps = data.get("project", {}).get("dependencies", [])
        total = len(deps)
        
        with open(LOG_FILE, "a", encoding="utf-8") as log_f:
            for i, req in enumerate(deps, 1):
                print(f"[{i}/{total}] Installing {req}...")
                subprocess.run([str(VENV_PYTHON), "-m", "pip", "install", req], stdout=log_f, stderr=log_f)
        log("[OK] All dependencies installed.")

    # List scripts and add selection dialogue
    scripts = sorted(glob.glob(str(BASE_DIR / "*.py")) + glob.glob(str(BASE_DIR / "*.pyw")))
    # Remove the install and run script from the list
    scripts = [s for s in scripts if Path(s).resolve() != Path(__file__).resolve()]

    if not scripts:
        log("[ERROR] No scripts found in this folder!")
        return

    # Auto-Start in case just one script exists
    if len(scripts) == 1:
        selected_script = scripts[0]
        log(f"[INFO] Only one script found. Starting {Path(selected_script).name}...")
    else:
        print("\n======================================================")
        print("  Available scripts:")
        print("======================================================")
        print("  [X] EXIT")
        for idx, s in enumerate(scripts, 1):
            print(f"  [{idx}] {Path(s).name}")
        
        choice = input("\nPlease enter the number of the script you'd like to run or type X to exit: ").strip()
        if choice.lower() == "x":
            return
        
        try:
            selected_script = scripts[int(choice) - 1]
        except (ValueError, IndexError):
            print("[ERROR] Invalid input.")
            return

    # Run the selected script and log its output
    print(f"\nStarting {Path(selected_script).name}...")
    with open(LOG_FILE, "a", encoding="utf-8") as log_f:
        proc = subprocess.Popen([str(VENV_PYTHON), "-u", selected_script], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in proc.stdout:
            sys.stdout.write(line)
            log_f.write(line)

if __name__ == "__main__":
    main()