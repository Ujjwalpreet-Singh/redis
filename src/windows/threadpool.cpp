#include "threadpool.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>


static DWORD WINAPI worker(LPVOID arg) {
    ThreadPool *tp = static_cast<ThreadPool *>(arg);

    while (true) {
        EnterCriticalSection(&tp->mu);

        while (tp->queue.empty()) {
            BOOL ok = SleepConditionVariableCS(
                &tp->not_empty,
                &tp->mu,
                INFINITE
            );

            if (!ok) {
                DWORD err = GetLastError();
                LeaveCriticalSection(&tp->mu);

                fprintf(stderr,
                    "SleepConditionVariableCS failed: %lu\n", err);
                return 1;
            }
        }

        Work w = tp->queue.front();
        tp->queue.pop_front();

        LeaveCriticalSection(&tp->mu);

        w.f(w.arg);
    }

    return 0;
}

void thread_pool_init(ThreadPool *tp, size_t num_threads){
    InitializeCriticalSection(&tp->mu);
    InitializeConditionVariable(&tp->not_empty);
    tp->threads.resize(num_threads);
    for (size_t i = 0; i < num_threads; i++) {
        tp->threads[i] = CreateThread(
            NULL, 0, worker, tp, 0, NULL
        );

        if (tp->threads[i] == NULL) {
            fprintf(stderr, "CreateThread failed: %lu\n",
                    GetLastError());
            abort();
        }
    }
}
void thread_pool_queue(ThreadPool *tp, void(*f)(void *),void *arg){
    EnterCriticalSection(&tp->mu);

    tp->queue.push_back(Work{f, arg});

    WakeConditionVariable(&tp->not_empty);

    LeaveCriticalSection(&tp->mu);
}
