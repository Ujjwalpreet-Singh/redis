import subprocess
import time

CLIENT = "..//client.exe"

def run(command):
    result = subprocess.run(
        [CLIENT, *command],
        capture_output=True,
        text=True,
        timeout=10,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Command failed: {command}\n{result.stderr}"
        )
    return result.stdout.strip()

key = "threadpool_test"

print("Creating sorted set with 5,000 members...")

for i in range(5000):
    run(["zadd", key, str(i), f"member_{i}"])

print("Sorted set created.")
print("Deleting sorted set...")

result = run(["del", key])
print("DEL response:", result)

time.sleep(1)
print("Done. Check the server's terminal for worker logs.")