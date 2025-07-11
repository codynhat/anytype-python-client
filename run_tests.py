#!/usr/bin/env python3
"""
Test runner for the Anytype Python client test suite.

This script provides convenient commands to run different test categories
and configurations for the Anytype Python client.
"""
import os
import sys
import subprocess
import argparse
from typing import List, Optional


def check_requirements():
    """Check if required environment and dependencies are available."""
    # Check for API key
    if not os.getenv("ANYTYPE_API_KEY"):
        print("❌ Error: ANYTYPE_API_KEY environment variable not set")
        print("Please set your Anytype API key:")
        print("export ANYTYPE_API_KEY=your-api-key-here")
        return False
    
    # Check if pytest is available
    try:
        import pytest
        print(f"✅ pytest available (version: {pytest.__version__})")
    except ImportError:
        print("❌ Error: pytest not installed")
        print("Please install test dependencies:")
        print("pip install -e .[dev]")
        return False
    
    # Check if anytype_client is available
    try:
        import anytype_client
        print(f"✅ anytype_client available (version: {anytype_client.__version__})")
    except ImportError:
        print("❌ Error: anytype_client not installed")
        print("Please install the package:")
        print("pip install -e .")
        return False
    
    return True


def run_pytest(test_args: List[str], extra_args: Optional[List[str]] = None) -> int:
    """Run pytest with the given arguments."""
    cmd = ["python", "-m", "pytest"] + test_args
    if extra_args:
        cmd.extend(extra_args)
    
    print(f"Running: {' '.join(cmd)}")
    print("=" * 50)
    
    return subprocess.call(cmd)


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(
        description="Test runner for Anytype Python client",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py --quick          # Run basic tests only
  python run_tests.py --sync           # Run sync client tests only
  python run_tests.py --async          # Run async client tests only
  python run_tests.py --integration    # Run integration tests only
  python run_tests.py --all            # Run all tests
  python run_tests.py --verbose        # Run with verbose output
  python run_tests.py --space-check    # Just check if test space exists
        """
    )
    
    # Test categories
    parser.add_argument("--quick", action="store_true", 
                       help="Run quick tests (auth, spaces, basic operations)")
    parser.add_argument("--sync", action="store_true", 
                       help="Run synchronous client tests only")
    parser.add_argument("--async", action="store_true", 
                       help="Run asynchronous client tests only")
    parser.add_argument("--integration", action="store_true", 
                       help="Run integration tests only")
    parser.add_argument("--all", action="store_true", 
                       help="Run all tests")
    
    # Test options
    parser.add_argument("--verbose", "-v", action="store_true", 
                       help="Verbose output")
    parser.add_argument("--space-check", action="store_true", 
                       help="Check if ClientTestSpace exists and exit")
    parser.add_argument("--no-warnings", action="store_true", 
                       help="Disable warnings")
    parser.add_argument("--parallel", action="store_true", 
                       help="Run tests in parallel (requires pytest-xdist)")
    
    # Advanced options
    parser.add_argument("--filter", type=str, 
                       help="Run tests matching pattern (pytest -k)")
    parser.add_argument("--marker", type=str, 
                       help="Run tests with specific marker (pytest -m)")
    parser.add_argument("--stop-on-first", action="store_true", 
                       help="Stop on first failure (pytest -x)")
    parser.add_argument("--pdb", action="store_true", 
                       help="Drop into debugger on failures")
    
    args = parser.parse_args()
    
    # Check requirements
    print("Checking requirements...")
    if not check_requirements():
        return 1
    
    # Special case: space check
    if args.space_check:
        print("\nChecking test space configuration...")
        try:
            from anytype_client import AnytypeClient
            client = AnytypeClient()
            with client:
                spaces = client.list_spaces()
                test_space = None
                for space in spaces:
                    if space.name == "ClientTestSpace":
                        test_space = space
                        break
                
                if test_space:
                    print(f"✅ Found dedicated ClientTestSpace (ID: {test_space.id})")
                    print("  ✓ Test suite will use the dedicated test space")
                    return 0
                else:
                    print("ℹ️ No dedicated ClientTestSpace found")
                    print("Available spaces:")
                    for space in spaces:
                        print(f"  - {space.name} (ID: {space.id})")
                    
                    print(f"\n✅ Test suite will automatically CREATE 'ClientTestSpace' for testing")
                    print("  ✓ Dedicated test space will be created automatically")
                    print("  ✓ Test environment will be set up in the new space")
                    print("  ℹ️ This ensures complete test isolation")
                    return 0
        except Exception as e:
            print(f"❌ Error checking spaces: {e}")
            return 1
    
    # Build test arguments
    test_args = []
    
    # Select test files based on category
    if args.quick:
        test_args.extend([
            "tests/test_auth_and_spaces.py",
            "tests/test_objects.py::TestObjectCRUD::test_create_object",
            "tests/test_search_and_types.py::TestSearchOperations::test_search_objects_basic"
        ])
    elif args.sync:
        test_args.extend([
            "tests/test_auth_and_spaces.py",
            "tests/test_objects.py",
            "tests/test_search_and_types.py",
            "tests/test_lists.py",
            "tests/test_members.py",
            "tests/test_properties.py",
            "tests/test_tags.py",
            "tests/test_templates.py"
        ])
    elif getattr(args, 'async'):
        test_args.append("tests/test_async_client.py")
    elif args.integration:
        test_args.append("tests/test_integration.py")
    elif args.all:
        test_args.append("tests/")
    else:
        # Default: run core functionality tests
        test_args.extend([
            "tests/test_auth_and_spaces.py",
            "tests/test_objects.py",
            "tests/test_search_and_types.py"
        ])
    
    # Add pytest options
    extra_args = []
    
    if args.verbose:
        extra_args.append("-vvv")
    
    if args.no_warnings:
        extra_args.append("--disable-warnings")
    
    if args.parallel:
        extra_args.extend(["-n", "auto"])
    
    if args.filter:
        extra_args.extend(["-k", args.filter])
    
    if args.marker:
        extra_args.extend(["-m", args.marker])
    
    if args.stop_on_first:
        extra_args.append("-x")
    
    if args.pdb:
        extra_args.append("--pdb")
    
    # Add default options
    extra_args.extend([
        "--tb=short",
        "--color=yes"
    ])
    
    print(f"\nRunning tests...")
    print(f"Test selection: {', '.join(test_args)}")
    if extra_args:
        print(f"Extra options: {', '.join(extra_args)}")
    print()
    
    # Run the tests
    exit_code = run_pytest(test_args, extra_args)
    
    if exit_code == 0:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n❌ Tests failed with exit code {exit_code}")
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())