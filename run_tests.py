#!/usr/bin/env python3
"""
Test runner script for orbnet package.

This script provides a convenient way to run tests with different configurations
and generate test reports.
"""

import argparse
import sys
import subprocess
from pathlib import Path


def run_command(cmd: list, description: str) -> bool:
    """Run a command and return success status."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print('='*60)
    
    result = subprocess.run(cmd, capture_output=False)
    return result.returncode == 0


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description="Run orbnet tests")
    parser.add_argument(
        "--unit", 
        action="store_true", 
        help="Run unit tests only"
    )
    parser.add_argument(
        "--integration", 
        action="store_true", 
        help="Run integration tests only"
    )
    parser.add_argument(
        "--all", 
        action="store_true", 
        help="Run all tests (default)"
    )
    parser.add_argument(
        "--coverage", 
        action="store_true", 
        help="Run tests with coverage reporting"
    )
    parser.add_argument(
        "--verbose", "-v", 
        action="store_true", 
        help="Verbose output"
    )
    parser.add_argument(
        "--fast", 
        action="store_true", 
        help="Skip slow tests"
    )
    parser.add_argument(
        "--format", 
        choices=["short", "long", "json"], 
        default="short",
        help="Test output format"
    )
    parser.add_argument(
        "--parallel", "-n", 
        type=int, 
        help="Run tests in parallel with N workers"
    )
    
    args = parser.parse_args()
    
    # Default to running all tests if no specific type is specified
    if not any([args.unit, args.integration, args.all]):
        args.all = True
    
    # Build pytest command
    cmd = ["python", "-m", "pytest"]
    
    # Add test paths based on arguments
    if args.unit:
        cmd.extend(["tests/test_models.py", "tests/test_client.py"])
    elif args.integration:
        cmd.extend(["tests/test_integration.py"])
    elif args.all:
        cmd.append("tests/")
    
    # Add options
    if args.verbose:
        cmd.append("-v")
    
    if args.fast:
        cmd.extend(["-m", "not slow"])
    
    if args.format == "long":
        cmd.append("--tb=long")
    elif args.format == "json":
        cmd.extend(["--tb=no", "--json-report", "--json-report-file=test-report.json"])
    
    if args.parallel:
        cmd.extend(["-n", str(args.parallel)])
    
    if args.coverage:
        cmd.extend([
            "--cov=src/orbnet",
            "--cov-report=html",
            "--cov-report=term-missing",
            "--cov-report=xml"
        ])
    
    # Add common options
    cmd.extend([
        "--strict-markers",
        "--disable-warnings",
        "--color=yes"
    ])
    
    print("Orbnet Test Runner")
    print("==================")
    print(f"Python version: {sys.version}")
    print(f"Working directory: {Path.cwd()}")
    
    # Run the tests
    success = run_command(cmd, "Running tests")
    
    if args.coverage and success:
        print(f"\nCoverage report generated in htmlcov/index.html")
    
    if success:
        print(f"\n✅ All tests passed!")
        return 0
    else:
        print(f"\n❌ Some tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())

