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

