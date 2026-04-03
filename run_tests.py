#!/usr/bin/env python3
"""Run all 194 tests across the 6 modules."""
import subprocess, sys, time

modules = [
    ("prepare.py", 35),
    ("prepare_provincial.py", 32),
    ("prepare_accounts.py", 42),
    ("prepare_clawbacks.py", 31),
    ("prepare_integration.py", 32),
    ("strategy.py", 22),
]

print("=" * 60)
print("RUNNING ALL TESTS")
print("=" * 60)

total_pass, total_expected, failures = 0, 0, []
t0 = time.time()

for mod, expected in modules:
    r = subprocess.run([sys.executable, mod], capture_output=True, text=True, cwd="src")
    passed = r.stdout.count("[PASS]")
    failed = r.stdout.count("[FAIL]")
    total_pass += passed
    total_expected += expected
    status = "PASS" if r.returncode == 0 and failed == 0 else "FAIL"
    print(f"  [{status}] {mod}: {passed}/{expected}")
    if status == "FAIL":
        failures.append(mod)

elapsed = time.time() - t0
print(f"\n{'=' * 60}")
print(f"TOTAL: {total_pass}/{total_expected} tests in {elapsed:.1f}s")
if failures:
    print(f"FAILURES: {', '.join(failures)}")
    sys.exit(1)
else:
    print("ALL TESTS PASSED")
    sys.exit(0)
