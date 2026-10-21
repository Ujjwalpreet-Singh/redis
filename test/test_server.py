#!/usr/bin/env python3
"""Regression tests for the mini Redis-like server.

Usage:
    python test_server.py
    python test_server.py --client ./client
    python test_server.py --client .\\client.exe

The server must already be running.
"""
import argparse
import shlex
import subprocess
import sys
import time
import uuid


def run_client(client, command, timeout=5):
    argv = [client, *command]
    try:
        result = subprocess.run(
            argv, capture_output=True, text=True, timeout=timeout, check=False
        )
    except FileNotFoundError:
        raise AssertionError(
            f"Client executable {client!r} not found; build it or pass --client PATH."
        )
    except subprocess.TimeoutExpired:
        raise AssertionError(f"Command timed out: {shlex.join(argv)}")

    if result.returncode != 0:
        raise AssertionError(
            f"Command failed: {shlex.join(argv)}\n"
            f"Exit code: {result.returncode}\nStderr: {result.stderr}"
        )
    return result.stdout


def expect_exact(client, command, expected):
    actual = run_client(client, command)
    if actual != expected:
        raise AssertionError(
            f"Command: {shlex.join([client, *command])}\n"
            f"Expected: {expected!r}\nActual:   {actual!r}"
        )
    print(f"PASS  {shlex.join(command)}")


def expect_int(client, command, predicate, description):
    actual = run_client(client, command).strip()
    prefix = "(int) "
    if not actual.startswith(prefix):
        raise AssertionError(
            f"Command: {shlex.join([client, *command])}\n"
            f"Expected integer response, got {actual!r}"
        )
    try:
        value = int(actual[len(prefix):])
    except ValueError:
        raise AssertionError(f"Could not parse integer response: {actual!r}")
    if not predicate(value):
        raise AssertionError(
            f"Command: {shlex.join([client, *command])}\n"
            f"Got {value}; expected {description}"
        )
    print(f"PASS  {shlex.join(command)} -> {value}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--client", default="./client", help="path to client executable")
    args = parser.parse_args()
    client = args.client

    # Unique keys avoid collisions with existing server data.
    prefix = "__pytest_" + uuid.uuid4().hex[:10]
    string_key = prefix + "_string"
    missing_key = prefix + "_missing"
    zset_key = prefix + "_zset"
    ttl_key = prefix + "_ttl"
    cleanup_keys = [string_key, zset_key, ttl_key]
    passed = 0

    def exact(command, expected):
        nonlocal passed
        expect_exact(client, command, expected)
        passed += 1

    def integer(command, predicate, description):
        nonlocal passed
        expect_int(client, command, predicate, description)
        passed += 1

    try:
        # GET, SET, DEL, KEYS
        exact(["get", missing_key], "(nil)\n")
        exact(["set", string_key, "hello"], "(nil)\n")
        exact(["get", string_key], "(str) hello\n")
        exact(["set", string_key, "updated"], "(nil)\n")
        exact(["get", string_key], "(str) updated\n")

        keys_output = run_client(client, ["keys"])
        if f"(str) {string_key}\n" not in keys_output:
            raise AssertionError(
                f"KEYS did not contain {string_key!r}. Output:\n{keys_output}"
            )
        print("PASS  keys (contains the created key)")
        passed += 1

        exact(["del", missing_key], "(int) 0\n")
        exact(["del", string_key], "(int) 1\n")
        exact(["get", string_key], "(nil)\n")

        # ZADD, ZSCORE, ZQUERY, ZREM
        exact(["zscore", zset_key, "n1"], "(nil)\n")
        exact(["zquery", zset_key, "1", "", "0", "10"],
              "(arr) len=0\n(arr) end\n")
        exact(["zadd", zset_key, "1", "n1"], "(int) 1\n")
        exact(["zadd", zset_key, "2", "n2"], "(int) 1\n")
        exact(["zadd", zset_key, "1.1", "n1"], "(int) 0\n")
        exact(["zscore", zset_key, "n1"], "(dbl) 1.1\n")
        exact(
            ["zquery", zset_key, "1", "", "0", "10"],
            "(arr) len=4\n(str) n1\n(dbl) 1.1\n"
            "(str) n2\n(dbl) 2\n(arr) end\n",
        )
        exact(
            ["zquery", zset_key, "1.1", "", "1", "10"],
            "(arr) len=2\n(str) n2\n(dbl) 2\n(arr) end\n",
        )
        exact(
            ["zquery", zset_key, "1.1", "", "2", "10"],
            "(arr) len=0\n(arr) end\n",
        )
        exact(["zrem", zset_key, "does-not-exist"], "(int) 0\n")
        exact(["zrem", zset_key, "n1"], "(int) 1\n")
        exact(
            ["zquery", zset_key, "1", "", "0", "10"],
            "(arr) len=2\n(str) n2\n(dbl) 2\n(arr) end\n",
        )
        exact(["zrem", zset_key, "n2"], "(int) 1\n")
        exact(["zscore", zset_key, "n2"], "(nil)\n")

        # PEXPIRE, PTTL, and expiration deletion.
        exact(["set", ttl_key, "temporary"], "(nil)\n")
        integer(["pttl", ttl_key], lambda n: n == -1, "no TTL (-1)")
        integer(["pttl", prefix + "_not_found"], lambda n: n == -2, "missing key (-2)")
        exact(["pexpire", prefix + "_not_found", "1000"], "(int) 0\n")
        exact(["pexpire", ttl_key, "3000"], "(int) 1\n")
        integer(
            ["pttl", ttl_key], lambda n: 0 < n <= 3000,
            "a positive TTL no greater than 3000 ms"
        )
        exact(["pexpire", ttl_key, "150"], "(int) 1\n")
        time.sleep(0.35)
        exact(["get", ttl_key], "(nil)\n")
        integer(["pttl", ttl_key], lambda n: n == -2, "expired key is missing (-2)")

        print(f"\nAll {passed} checks passed.")
        return 0
    except AssertionError as exc:
        print(f"\nFAIL: {exc}", file=sys.stderr)
        return 1
    finally:
        # Best-effort cleanup if a test fails midway.
        for key in cleanup_keys:
            try:
                run_client(client, ["del", key])
            except AssertionError:
                pass


if __name__ == "__main__":
    raise SystemExit(main())
