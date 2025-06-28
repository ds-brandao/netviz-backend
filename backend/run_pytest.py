#!/usr/bin/env python3
"""
Pytest runner script for NetViz backend tests.
Provides convenient commands for running different test suites.
"""

import subprocess
import sys
import argparse
from pathlib import Path


def run_command(cmd):
    """Run a command and return the exit code."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    return result.returncode


def main():
    parser = argparse.ArgumentParser(description="Run NetViz backend tests with pytest")
    parser.add_argument("--unit", action="store_true", help="Run only unit tests")
    parser.add_argument("--integration", action="store_true", help="Run only integration tests")
    parser.add_argument("--coverage", action="store_true", help="Run tests with coverage report")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--parallel", "-n", type=int, help="Run tests in parallel")
    parser.add_argument("--file", "-f", help="Run specific test file")
    parser.add_argument("--test", "-t", help="Run specific test function")
    
    args = parser.parse_args()
    
    # Base pytest command
    cmd = ["python", "-m", "pytest"]
    
    # Add verbosity
    if args.verbose:
        cmd.append("-v")
    
    # Add coverage
    if args.coverage:
        cmd.extend(["--cov=src", "--cov-report=html", "--cov-report=term-missing"])
    
    # Add parallel execution
    if args.parallel:
        cmd.extend(["-n", str(args.parallel)])
    
    # Filter by test type
    if args.unit:
        cmd.extend(["-m", "unit"])
    elif args.integration:
        cmd.extend(["-m", "integration"])
    
    # Run specific file
    if args.file:
        test_file = f"tests/{args.file}" if not args.file.startswith("tests/") else args.file
        cmd.append(test_file)
    
    # Run specific test
    if args.test:
        if args.file:
            cmd.append(f"::{args.test}")
        else:
            cmd.extend(["-k", args.test])
    
    # If no specific options, run all tests
    if not any([args.unit, args.integration, args.file, args.test]):
        cmd.append("tests/")
    
    # Run the command
    exit_code = run_command(cmd)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()