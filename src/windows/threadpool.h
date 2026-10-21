#pragma once
#ifndef _WIN32_WINNT
#define _WIN32_WINNT 0x0600
#endif

#ifndef WINVER
#define WINVER 0x0600
#endif

#include <windows.h>
#include <stddef.h>
#include <windows.h>
#include <vector>
#include <deque>


struct Work {
    void (*f)(void *) = NULL;
    void *arg = NULL;
};

struct ThreadPool {
    std::vector<HANDLE> threads;
    std::deque<Work> queue;
    CRITICAL_SECTION mu;
    CONDITION_VARIABLE not_empty;
};

void thread_pool_queue(ThreadPool *tp, void(*f)(void *),void *arg);
void thread_pool_init(ThreadPool *tp, size_t num_threads);