#!/usr/bin/env python3
"""
Test runner script for RFI Processor tests.
"""
import sys
import os
import subprocess
from pathlib import Path

def run_tests():
    """Run all tests using pytest."""
    # Add the server directory to Python path
    server_dir = Path(__file__).parent.parent
    sys.path.insert(0, str(server_dir))
    
    # Change to server directory
    os.chdir(server_dir)
    
    # Run pytest with coverage
    cmd = [
        "python", "-m", "pytest",
        "tests/",
        "-v",
        "--tb=short",
        "--cov=rfiprocessor",
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov",
        "--cov-report=xml:coverage.xml"
    ]
    
    try:
        result = subprocess.run(cmd, check=True)
        print("\n✅ All tests passed!")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Tests failed with exit code {e.returncode}")
        return e.returncode

def run_unit_tests_only():
    """Run only unit tests."""
    server_dir = Path(__file__).parent.parent
    sys.path.insert(0, str(server_dir))
    os.chdir(server_dir)
    
    cmd = [
        "python", "-m", "pytest",
        "tests/unit/",
        "-v",
        "--tb=short"
    ]
    
    try:
        result = subprocess.run(cmd, check=True)
        print("\n✅ All unit tests passed!")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Unit tests failed with exit code {e.returncode}")
        return e.returncode

def run_integration_tests_only():
    """Run only integration tests."""
    server_dir = Path(__file__).parent.parent
    sys.path.insert(0, str(server_dir))
    os.chdir(server_dir)
    
    cmd = [
        "python", "-m", "pytest",
        "tests/integration/",
        "-v",
        "--tb=short"
    ]
    
    try:
        result = subprocess.run(cmd, check=True)
        print("\n✅ All integration tests passed!")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Integration tests failed with exit code {e.returncode}")
        return e.returncode

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "unit":
            exit(run_unit_tests_only())
        elif sys.argv[1] == "integration":
            exit(run_integration_tests_only())
        else:
            print("Usage: python run_tests.py [unit|integration]")
            print("  unit: Run only unit tests")
            print("  integration: Run only integration tests")
            print("  (no args): Run all tests with coverage")
            exit(1)
    else:
        exit(run_tests()) 