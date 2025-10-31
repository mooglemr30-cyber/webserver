#!/usr/bin/env python3
"""
Run smoke tests and capture output to a file.
"""
import subprocess
import sys
import os

os.chdir('/home/admin1/Documents/webserver')

print("Running smoke tests...")
result = subprocess.run(
    [sys.executable, 'test_smoke.py'],
    capture_output=True,
    text=True
)

output = result.stdout + result.stderr

print(output)

# Write to file
with open('test_results.txt', 'w') as f:
    f.write(output)
    f.write(f"\n\nExit code: {result.returncode}\n")

print(f"\n{'='*60}")
if result.returncode == 0:
    print("✅ ALL TESTS PASSED")
else:
    print("❌ SOME TESTS FAILED")
print(f"{'='*60}")
print(f"Full results saved to: test_results.txt")

sys.exit(result.returncode)

