# Redis Clone

A lightweight, Redis-inspired in-memory key-value server written in **C++17**. The project implements a small binary request/response protocol, a command-line client, string values, sorted sets, key expiration, and platform-specific networking/thread-pool implementations for Linux and Windows.

> **Project status:** This is an educational Redis-like implementation, not a drop-in replacement for Redis. It uses a custom protocol and currently stores data in memory only.

## Features

- **TCP server and client** communicating over `127.0.0.1:1234`.
- **String operations:** `SET`, `GET`, and `DEL`.
- **Key listing:** `KEYS`.
- **Sorted sets:** `ZADD`, `ZSCORE`, `ZQUERY`, and `ZREM`.
- **Key expiration:** `PEXPIRE` and `PTTL`, with expiration times specified in milliseconds.
- **Core data structures implemented in C++:**
  - Hash table with incremental migration.
  - AVL tree with subtree counts for sorted-set ordering and offset-based traversal.
  - Binary heap for tracking expiration deadlines.
  - Doubly linked list for connection-idle tracking.
- **Non-blocking network I/O** and an event-driven connection loop.
- **Worker thread pool** for deferred cleanup of large sorted sets.
- **Separate Linux and Windows implementations** for sockets, server/client networking, and thread-pool primitives.
- **Python regression tests** for commands, sorted-set behavior, expiration, and worker-pool cleanup.

## Project Structure

```text
redis/
├── CMakeLists.txt
├── compile                         # Legacy/manual Linux build helper
├── src/
│   ├── common.h                    # Shared protocol/helpers
│   ├── avl.cpp / avl.h             # AVL tree
│   ├── hashtable.cpp / hashtable.h # Hash table
│   ├── heap.cpp / heap.h           # Heap utilities
│   ├── list.h                      # Doubly linked list
│   ├── zset.cpp / zset.h            # Sorted-set implementation
│   ├── linux/
│   │   ├── server.cpp
│   │   ├── client.cpp
│   │   └── threadpool.cpp / .h     # POSIX sockets and pthreads
│   └── windows/
│       ├── server.cpp
│       ├── client.cpp
│       └── threadpool.cpp / .h     # Winsock and Windows threading
├── test/
│   ├── test_server.py              # Command and expiration regression tests
│   └── test_threadpool.py           # Large sorted-set cleanup test
├── linuxbuild/                     # Generated Linux build artifacts (if present)
└── build/                          # Generated Windows/build artifacts (if present)
```

The `build/` and `linuxbuild/` directories and prebuilt binaries may be included in the archive, but they are generated artifacts. For a clean build, configure a new build directory from `CMakeLists.txt` instead.

## Prerequisites

### Linux

- A C++ compiler with C++17 support (for example, GCC or Clang).
- CMake 3.16 or newer.
- A build tool supported by CMake, such as Ninja or Make.
- Python 3 for the regression tests.

The Linux implementation uses POSIX sockets and pthreads.

### Windows

- Windows 10 or later is a reasonable target for the configured Windows APIs.
- CMake 3.16 or newer.
- A C++17-capable compiler/toolchain, such as Visual Studio Build Tools with the C++ workload, or MinGW-w64.
- Python 3 for the regression tests.

The Windows implementation uses Winsock (`ws2_32`) and Windows threading APIs. CMake selects the platform-specific source files automatically.

## Build and Installation

No separate installation step is required; build the `server` and `client` executables with CMake.

### Linux

From the project root:

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug
cmake --build build --parallel
```

This produces:

```text
build/server
build/client
```

If you prefer Ninja and have it installed:

```bash
cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Debug
cmake --build build
```

### Windows (Visual Studio generator)

Run these commands from a Developer PowerShell or a terminal where CMake and the Visual Studio C++ toolchain are available:

```powershell
cmake -S . -B build
cmake --build build --config Debug
```

The executables are typically placed under `build\Debug\` when using a multi-configuration generator:

```text
build\Debug\server.exe
build\Debug\client.exe
```

For a single-configuration generator such as MinGW Makefiles or Ninja, the executables are generally placed directly in `build\`.

> **Tip:** Use a fresh build directory if the archive contains cached CMake files from another operating system or machine. CMake build directories are usually platform- and toolchain-specific.

## Usage

The server listens on **127.0.0.1, port 1234**. Start it in one terminal, then run client commands from another terminal. The client accepts a command and its arguments as command-line arguments; each invocation sends one request and prints one response.

### 1. Start the server

Linux:

```bash
./build/server
```

Windows (adjust the path for your generator):

```powershell
.\build\Debug\server.exe
```

Keep the server running while issuing client commands. The server logs connection information to its terminal.

### 2. Run commands with the client

Linux:

```bash
./build/client set greeting "hello world"
./build/client get greeting
./build/client del greeting
```

Windows:

```powershell
.\build\Debug\client.exe set greeting "hello world"
.\build\Debug\client.exe get greeting
.\build\Debug\client.exe del greeting
```

Example output:

```text
(nil)
(str) hello world
(int) 1
```

### Supported Commands

| Command | Syntax | Description |
|---|---|---|
| `SET` | `set <key> <value>` | Create a string key or replace its value. Returns `(nil)` on success. |
| `GET` | `get <key>` | Return the string value, or `(nil)` if the key does not exist. |
| `DEL` | `del <key>` | Delete a key. Returns `(int) 1` if deleted, otherwise `(int) 0`. |
| `KEYS` | `keys` | Return the keys currently stored in the database. |
| `ZADD` | `zadd <key> <score> <member>` | Add a member to a sorted set or update its score. Returns `1` for a new member and `0` when updating an existing member. |
| `ZSCORE` | `zscore <key> <member>` | Return a member's score, or `(nil)` if the member is absent. |
| `ZREM` | `zrem <key> <member>` | Remove a member from a sorted set. Returns `1` if removed, otherwise `0`. |
| `ZQUERY` | `zquery <key> <score> <member> <offset> <limit>` | Query sorted-set entries from a score/member starting position, applying an offset and result limit. Results are returned as alternating member and score values. |
| `PEXPIRE` | `pexpire <key> <milliseconds>` | Set or update a key's expiration in milliseconds. Returns `1` if the key exists, otherwise `0`. |
| `PTTL` | `pttl <key>` | Return remaining TTL in milliseconds; `-1` means no expiration and `-2` means the key is missing or expired. |

Commands are case-sensitive in the current implementation; use the lowercase spellings shown above. A key is stored as either a string or a sorted set, so string and sorted-set commands are not interchangeable for the same key.

### Sorted-set examples

```bash
./build/client zadd leaderboard 100 alice
./build/client zadd leaderboard 125 bob
./build/client zscore leaderboard alice
./build/client zquery leaderboard 0 "" 0 10
./build/client zrem leaderboard alice
```

On Windows, replace `./build/client` with the path to `client.exe`. `ZQUERY` takes six command-line arguments including the command name; pass an empty member argument as `""` when you want an empty starting member.

### Expiration examples

```bash
./build/client set temporary "delete soon"
./build/client pexpire temporary 5000
./build/client pttl temporary
```

After the TTL elapses, the key is treated as expired and is removed when the server processes expiration handling.

## Running Tests

The tests expect the server to be running already and connect through the built client.

1. Build the project.
2. Start the server in a separate terminal.
3. From the project root, run the regression suite.

Linux:

```bash
python3 test/test_server.py --client ./build/client
```

Windows PowerShell (adjust the executable path if needed):

```powershell
python test\test_server.py --client .\build\Debug\client.exe
```

The server regression test checks string operations, key listing, sorted-set insertion/update/query/removal, and TTL behavior. It prints a `PASS` line for each check and exits nonzero if a check fails.

The additional `test/test_threadpool.py` script is configured to use `..\client.exe` and is Windows-oriented in its current form. Run it only after adjusting its `CLIENT` path to the client executable you built. It inserts 5,000 sorted-set members and deletes the key to exercise deferred cleanup; inspect the server terminal for worker logs.

## Implementation Notes and Limitations

- **In-memory storage:** the database is not persisted to disk; restarting the server loses stored data.
- **Custom protocol:** this project does not implement the Redis Serialization Protocol (RESP), so standard Redis clients such as `redis-cli` are not expected to work with it.
- **Local-only client:** the bundled client connects to `127.0.0.1:1234`; remote-host configuration is not exposed through command-line options.
- **One request per client process:** each client invocation sends a single command, prints the response, and exits.
- **Platform selection:** CMake supports Windows and Linux and reports an error for other operating systems.
- **Protocol portability:** the current implementation serializes integer lengths and numeric values using native byte representations and comments that assume little-endian layout. Cross-endian interoperability is not implemented.
- **No authentication or encryption:** use only in a trusted local development environment. The server is intended for learning and experimentation, not production deployment.
- **Message sizes differ by component:** the server accepts substantially larger request/response buffers than the bundled client, whose message limit is 4 KiB.

## Troubleshooting

- **Client cannot connect:** make sure the server is running and listening on port `1234`; check whether another process is already using that port.
- **Build fails after moving the project:** remove the generated build directory and reconfigure with CMake so cached compiler and source paths are refreshed.
- **Tests fail to find the client:** pass the correct path with `--client`.
- **Sorted-set test output looks empty:** verify the `ZQUERY` start score/member, offset, and limit; its output is an array of alternating member and score values.

## License

No license file was found in the supplied source archive. Until a license is added, all rights remain with the copyright holder by default.

If you intend to publish this project as open source, add a `LICENSE` file and replace this section with the selected license (for example, MIT or GPL-3.0).
