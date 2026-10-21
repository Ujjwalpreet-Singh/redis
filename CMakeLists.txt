cmake_minimum_required(VERSION 3.16)

project(RedisClone LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Shared source files
set(COMMON_SOURCES
    src/avl.cpp
    src/hashtable.cpp
    src/heap.cpp
    src/zset.cpp
)

# Select OS-specific implementations
if(WIN32)
    message(STATUS "Building for Windows")

    set(SERVER_SOURCES
        src/windows/server.cpp
        src/windows/threadpool.cpp
    )

    set(CLIENT_SOURCES
        src/windows/client.cpp
    )

elseif(CMAKE_SYSTEM_NAME STREQUAL "Linux")
    message(STATUS "Building for Linux")

    set(SERVER_SOURCES
        src/linux/server.cpp
        src/linux/threadpool.cpp
    )

    set(CLIENT_SOURCES
        src/linux/client.cpp
    )

else()
    message(FATAL_ERROR
        "Unsupported operating system: ${CMAKE_SYSTEM_NAME}"
    )
endif()

# Server executable
add_executable(server
    ${COMMON_SOURCES}
    ${SERVER_SOURCES}
)

# Client executable
add_executable(client
    ${CLIENT_SOURCES}
)

# Header include directories
target_include_directories(server PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/src
)

target_include_directories(client PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/src
)

# Windows-specific settings
if(WIN32)
    target_compile_definitions(server PRIVATE
        _WIN32_WINNT=0x0600
    )

    target_compile_definitions(client PRIVATE
        _WIN32_WINNT=0x0600
    )

    target_link_libraries(server PRIVATE ws2_32)
    target_link_libraries(client PRIVATE ws2_32)
endif()