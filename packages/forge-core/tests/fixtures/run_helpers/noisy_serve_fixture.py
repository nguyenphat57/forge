import time

print("Ready on http://localhost:3000", flush=True)
for index in range(800):
    print(f"log line {index} " + ("x" * 48), flush=True)
time.sleep(1.0)
