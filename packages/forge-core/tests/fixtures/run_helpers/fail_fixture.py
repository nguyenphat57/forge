import sys

print("Module not found: payments.service", file=sys.stderr, flush=True)
raise SystemExit(1)
