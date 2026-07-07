import glob
import multiprocessing
import os
import subprocess
import sys


def lint():
    try:
        # Run Ruff for linting
        subprocess.run(["ruff", "check", "."], check=True)
        # Run Ruff for formatting
        subprocess.run(["ruff", "format", "--check", "."], check=True)
        # Run Pylint only for the custom format_html f-string check
        subprocess.run(["pylint", "."], check=True)
        # Run mypy for type checking
        subprocess.run(
            ["mypy", ".", "--disable-error-code", "annotation-unchecked"], check=True
        )
        # Run djlint for Django template linting
        subprocess.run(["djlint", "."], check=True)
        subprocess.run(["djlint", "--check", "."], check=True)  # check formatting
    except subprocess.CalledProcessError as error:
        print("Error linting: ")
        print(error)
        sys.exit(error.returncode)


def run_development_server():
    subprocess.run(["python", "manage.py", "runserver"], check=False)


def format_code():
    # Run Ruff for lint auto-fixing
    subprocess.run(["ruff", "check", "--fix", "."], check=True)
    # Run Ruff for formatting auto-fixing
    subprocess.run(["ruff", "format", "."], check=True)
    # Run djlint for Django template formatting
    subprocess.run(["djlint", "--reformat", "--quiet", "."], check=False)


def test():
    try:
        subprocess.run(["coverage", "erase"], check=True)
        subprocess.run(
            ["coverage", "run", "manage.py", "test"] + sys.argv[1:],
            check=True,
            env=dict(os.environ, ENTRA_ID_ENABLED="True"),
        )
        subprocess.run(["coverage", "report"], check=True)
    except subprocess.CalledProcessError as error:
        print("Test run not successful: ")
        print(error)
        sys.exit(error.returncode)


def test_parallel():
    cpu_count = str(multiprocessing.cpu_count())
    print(f"Running tests with {cpu_count} parallel processes...", flush=True)
    try:
        subprocess.run(["coverage", "erase"], check=True)
        subprocess.run(
            [
                "coverage",
                "run",
                "manage.py",
                "test",
                "--parallel",
                cpu_count,
            ]
            + sys.argv[1:],
            check=True,
            env=dict(os.environ, ENTRA_ID_ENABLED="True"),
        )
        subprocess.run(["coverage", "report"], check=True)
    except subprocess.CalledProcessError as error:
        print("Test run not successful: ")
        print(error)
        sys.exit(error.returncode)


def seed_db():
    """
    Usage from within ECS container:
        -c,python manage.py shell -c "from hfurb_scripts.seeders import run; run()"
    """
    from hfurb_scripts.seeders import run  # noqa: E402

    run()


def disable_non_admin_user_access():
    from hfurb_scripts.toggle_non_admin_user_access import disable_users  # noqa: E402

    disable_users()


def reenable_non_admin_user_access():
    from hfurb_scripts.toggle_non_admin_user_access import enable_users  # noqa: E402

    enable_users()


def lint_shell():
    files = glob.glob("**/*.sh", recursive=True, include_hidden=True)

    if not files:
        print("No .sh files found.")
        return

    print(f"Scanning {len(files)} files...")

    try:
        subprocess.run(["poetry", "run", "shellcheck"] + files, check=True)

    except subprocess.CalledProcessError as error:
        print("Error running Shellcheck: ")
        print(error)
        sys.exit(error.returncode)
