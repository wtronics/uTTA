# uTTA - Python Scripts Collection

Cross-platform measurement & post-processing tool.

## Quick Start Guide

This project includes an automated setup and launcher script (`install_and_run.py`) that manages the virtual environment, installs dependencies directly from `pyproject.toml`, and runs the application across Windows, macOS, and Linux.

---

### Prerequisites

* **Python 3.11+** installed on your system.
* Internet connection (required for initial setup and dependency installation).

---

### How to Run

1. Open your terminal (**Command Prompt** or **PowerShell** on Windows, **Terminal** on macOS/Linux).
2. Navigate to the project directory:
   ```bash
   cd path/to/uTTA
   ```

3. Run the setup and launcher script:

* Windows:
   ```DOS
   python install_and_run.py
   ```
* macOS/Linux
   ```bash
   python3 install_and_run.py
   ```

## What the Script Does Automatically
* Virtual Environment Setup: Detects whether a local environment (```.venv/```) exists. If missing, it creates one automatically.
* Dependency Management: Reads ```pyproject.toml``` and installs or updates all required Python packages with live progress in the console.
* Script Discovery & Execution:
   * If only one ```.py```/```.pyw``` script is present in the directory, it launches automatically.
   * If multiple scripts are found, an interactive menu allows you to select which script to execute.

* Logging: All execution output and setup steps are simultaneously printed to the console and saved to ```install_log.txt``` for troubleshooting.

## File Structure
* ```install_and_run.py``` - Cross-platform launcher and setup script.
* ```pyproject.toml``` - Project configuration and dependency definitions.
* ```install_log.txt``` - Log file generated automatically during setup and execution.
* ```.venv/``` - Local virtual environment (created on first run).