#!/usr/bin/env python3
"""Test runner script for SpendCast backend."""

import subprocess
import sys
import argparse
from pathlib import Path


def run_tests(test_type=None, verbose=False, coverage=False, parallel=False):
    """Run tests with specified options."""

    # Base pytest command
    cmd = ["python", "-m", "pytest"]

    # Add test type marker if specified
    if test_type:
        cmd.extend(["-m", test_type])

    # Add verbosity
    if verbose:
        cmd.append("-v")
    else:
        cmd.append("-q")

    # Add coverage
    if coverage:
        cmd.extend(["--cov=src", "--cov-report=term-missing", "--cov-report=html"])

    # Add parallel execution
    if parallel:
        cmd.extend(["-n", "auto"])

    # Add test directory
    cmd.append("tests/")

    print(f"Running: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, cwd=Path(__file__).parent.parent)
        return result.returncode
    except KeyboardInterrupt:
        print("\nTests interrupted by user")
        return 1
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1


def main():
    """Main test runner entry point."""
    parser = argparse.ArgumentParser(description="SpendCast Backend Test Runner")

    parser.add_argument(
        "--type", choices=["unit", "integration", "slow"], help="Run specific test type"
    )

    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")

    parser.add_argument(
        "--coverage", action="store_true", help="Run with coverage report"
    )

    parser.add_argument("--parallel", action="store_true", help="Run tests in parallel")

    args = parser.parse_args()

    exit_code = run_tests(
        test_type=args.type,
        verbose=args.verbose,
        coverage=args.coverage,
        parallel=args.parallel,
    )

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
