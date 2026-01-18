"""Development server script."""

import subprocess
import sys


def main():
    """Run the development server."""
    subprocess.run(
        ["uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"],
        cwd="src",
        check=False,
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
