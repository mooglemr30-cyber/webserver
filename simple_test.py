#!/usr/bin/env python3
"""
Simple test runner - just run: python3 simple_test.py
"""

import os
import sys

print("=" * 70)
print("  RUNNING COMPREHENSIVE TESTS")
print("=" * 70)
print()

# Change to correct directory
os.chdir('/home/admin1/Documents/webserver')

# Check if comprehensive test exists
if not os.path.exists('comprehensive_test.py'):
    print("ERROR: comprehensive_test.py not found!")
    sys.exit(1)

# Run the comprehensive test
print("Starting tests...")
print()

exit_code = os.system('python3 comprehensive_test.py')

print()
print("=" * 70)
print(f"  Test completed with exit code: {exit_code}")
print("=" * 70)

sys.exit(exit_code)

