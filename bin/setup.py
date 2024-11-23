#!/usr/bin/env/python3
import argparse
import logging
import os
import subprocess
from glob import glob
from pathlib import Path
from typing import List
from typing import Tuple

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("scraper_log.log"), logging.StreamHandler()],
)
LOG = logging.getLogger(__name__)

OS = os.uname().sysname


def find_environment_files() -> List[Tuple[Path, Path]]:
    paths = []
    dot_env_files = glob("**/.python-env", recursive=True)
    for dot_env_file in dot_env_files:
        env_path = Path(dot_env_file).parent
        if (env_path / ".python-version").exists():
            paths.append((env_path / ".python-env", env_path / ".python-version"))
    return paths


def install_pyenv():
    try:
        subprocess.run(
            ["pyenv", "--version"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        LOG.info("Pyenv is already installed.")
    except subprocess.CalledProcessError:
        LOG.info("Pyenv not found. Installing pyenv...")
        if OS in ["Linux", "Darwin"]:
            subprocess.run("curl https://pyenv.run | bash", shell=True)
            LOG.info(
                "Pyenv installed. Please restart your shell or source your profile to use pyenv."
            )


def setup_venv(envs: List[Tuple[Path, Path]]):
    for env_path, version_path in envs:
        python_version = version_path.read_text().strip()
        venv_name = env_path.read_text().strip()

        if (
            subprocess.run(
                f"pyenv versions --bare | grep -q ^{python_version}$", shell=True
            ).returncode
            != 0
        ):
            LOG.info(f"Installing Python version {python_version}...")
            subprocess.run(["pyenv", "install", python_version], check=True)

        if (
            subprocess.run(
                f"pyenv virtualenvs --bare | grep -q ^{venv_name}$", shell=True
            ).returncode
            != 0
        ):
            LOG.info(
                f"Creating virtual environment {venv_name} with Python {python_version}..."
            )
            subprocess.run(
                ["pyenv", "virtualenv", python_version, venv_name],
                check=True,
                capture_output=True,
            )
        else:
            LOG.info(f"Virtual environment {venv_name} already exists.")

        env_path = Path(env_path).absolute()
        if (env_path.parent / "requirements.txt").exists():
            LOG.info(
                f'Installing dependencies from {env_path.parent / "requirements.txt"}...'
            )
            subprocess.run(
                f"""export PYENV_VERSION={venv_name} && pyenv exec pip install -r {env_path.parent / "requirements.txt"}""",
                capture_output=False,
                shell=True,
                check=True,
            )
        else:
            LOG.info("No requirements.txt found.")


def delete_all_venvs(envs: List[Tuple[Path, Path]]):
    LOG.info("Deleting all virtual environments...")
    for env_path, _ in envs:
        venv_name = env_path.read_text().strip()
        if (
            subprocess.run(
                f"pyenv virtualenvs --bare | grep -q ^{venv_name}$", shell=True
            ).returncode
            == 0
        ):
            LOG.info(f"Deleting virtual environment {venv_name}...")
            subprocess.run(["pyenv", "uninstall", "-f", venv_name], check=True)
        else:
            LOG.info(f"Virtual environment {venv_name} not found.")


def re_setup(envs: List[Tuple[Path, Path]]):
    delete_all_venvs(envs)
    setup_venv(envs)


def main():
    parser = argparse.ArgumentParser(
        description="Manage Python environments with pyenv."
    )
    parser.add_argument(
        "--setup",
        action="store_true",
        help="Set up virtual environments based on .python-env and .python-version.",
    )
    parser.add_argument(
        "--delete-all",
        action="store_true",
        help="Delete all existing virtual environments defined in .python-env files.",
    )
    parser.add_argument(
        "--re-setup",
        action="store_true",
        help="Delete all existing virtual environments and set them up again.",
    )

    args = parser.parse_args()

    install_pyenv()  # Ensure pyenv is installed
    envs = find_environment_files()  # Find all relevant directories

    if args.setup:
        setup_venv(envs)
    elif args.delete_all:
        delete_all_venvs(envs)
    elif args.re_setup:
        re_setup(envs)
    else:
        LOG.info(
            "No valid argument provided. Use --setup, --delete-all, or --re-setup."
        )


if __name__ == "__main__":
    main()
