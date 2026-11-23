/* sensor-hub (Linux original): event loop that samples a "sensor" on a timer,
 * wakes a worker with eventfd, watches a config file with inotify, reads
 * CPU load from /proc and pins itself to CPU 0. */
#define _GNU_SOURCE
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <unistd.h>
#include <sched.h>
#include <sys/epoll.h>
#include <sys/eventfd.h>
#include <sys/timerfd.h>
#include <sys/inotify.h>
#include <sys/prctl.h>

int main(void) {
    prctl(PR_SET_NAME, "sensor-hub");
    cpu_set_t set; CPU_ZERO(&set); CPU_SET(0, &set);
    sched_setaffinity(0, sizeof set, &set);

    int ep = epoll_create1(0);
    int tfd = timerfd_create(CLOCK_MONOTONIC, 0);
    struct itimerspec its = {{0, 100000000}, {0, 100000000}};
    timerfd_settime(tfd, 0, &its, NULL);
    int efd = eventfd(0, 0);
    int ino = inotify_init1(0);
    inotify_add_watch(ino, "/tmp", IN_MODIFY);

    struct epoll_event ev = {.events = EPOLLIN, .data.fd = tfd};
    epoll_ctl(ep, EPOLL_CTL_ADD, tfd, &ev);
    ev.data.fd = efd; epoll_ctl(ep, EPOLL_CTL_ADD, efd, &ev);

    FILE *f = fopen("/proc/loadavg", "r");
    double load = 0; if (f) { fscanf(f, "%lf", &load); fclose(f); }
    printf("sensor-hub start, load=%.2f\n", load);

    int samples = 0;
    while (samples < 10) {
        struct epoll_event out[4];
        int n = epoll_wait(ep, out, 4, 1000);
        for (int i = 0; i < n; i++) {
            uint64_t v;
            read(out[i].data.fd, &v, sizeof v);
            if (out[i].data.fd == tfd) { samples++; uint64_t one = 1; write(efd, &one, 8); }
            else printf("sample %d processed\n", samples);
        }
    }
    printf("sensor-hub done: %d samples\n", samples);
    return 0;
}
