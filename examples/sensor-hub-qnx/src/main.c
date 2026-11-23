/* sensor-hub ported to QNX Neutrino 8.0 with the help of qnx-port-doctor.
 *   epoll            -> poll()
 *   timerfd          -> POSIX timer_create(SIGEV_PULSE) on a QNX channel
 *   eventfd          -> pipe() wake-up
 *   inotify on /tmp  -> mtime polling of the watched file
 *   /proc/loadavg    -> sysconf(_SC_NPROCESSORS_ONLN) + SYSPAGE info
 *   sched_setaffinity-> ThreadCtl(_NTO_TCTL_RUNMASK)
 *   prctl(PR_SET_NAME)-> pthread_setname_np()
 * Builds with: make -f Makefile.qnx   (qcc -Vgcc_ntox86_64)
 */
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <poll.h>
#include <pthread.h>
#include <time.h>
#include <signal.h>
#include <sys/stat.h>
#include <sys/neutrino.h>
#include <sys/siginfo.h>
#include <sys/utsname.h>

#define PULSE_TICK (_PULSE_CODE_MINAVAIL + 1)

static int wake_pipe[2];
static volatile int processed;

static void *worker(void *arg) {
    (void)arg;
    pthread_setname_np(pthread_self(), "sh-worker");
    struct pollfd p = {.fd = wake_pipe[0], .events = POLLIN};
    for (;;) {
        if (poll(&p, 1, 2000) <= 0) continue;
        char c;
        if (read(wake_pipe[0], &c, 1) != 1 || c == 'q') break;
        printf("sample %d processed\n", ++processed);
        fflush(stdout);
    }
    return NULL;
}

int main(int argc, char **argv) {
    int nsamples = argc > 1 ? atoi(argv[1]) : 10;
    struct utsname u; uname(&u);
    printf("sensor-hub on %s %s (%s)\n", u.sysname, u.release, u.machine);

    pthread_setname_np(pthread_self(), "sensor-hub");
    unsigned runmask = 0x1;                     /* pin to CPU 0 */
    if (ThreadCtl(_NTO_TCTL_RUNMASK, (void *)(uintptr_t)runmask) == -1)
        perror("ThreadCtl runmask");
    printf("cpus online: %ld\n", sysconf(_SC_NPROCESSORS_ONLN));

    if (pipe(wake_pipe) == -1) { perror("pipe"); return 1; }
    pthread_t th; pthread_create(&th, NULL, worker, NULL);

    /* QNX-native periodic timer: deliver a pulse every 100 ms to our channel */
    int chid = ChannelCreate(_NTO_CHF_PRIVATE);
    int coid = ConnectAttach(0, 0, chid, _NTO_SIDE_CHANNEL, 0);
    struct sigevent ev;
    SIGEV_PULSE_INIT(&ev, coid, SIGEV_PULSE_PRIO_INHERIT, PULSE_TICK, 0);
    timer_t tid; timer_create(CLOCK_MONOTONIC, &ev, &tid);
    struct itimerspec its = {{0, 100000000}, {0, 100000000}};
    timer_settime(tid, 0, &its, NULL);

    struct stat st0 = {0}; stat("/tmp", &st0);
    int samples = 0;
    while (samples < nsamples) {
        struct _pulse pulse;
        if (MsgReceivePulse(chid, &pulse, sizeof pulse, NULL) == -1) { perror("MsgReceivePulse"); break; }
        if (pulse.code == PULSE_TICK) {
            samples++;
            write(wake_pipe[1], "s", 1);
            struct stat st; if (stat("/tmp", &st) == 0 && st.st_mtime != st0.st_mtime) {
                printf("config dir changed\n"); st0 = st;
            }
        }
    }
    write(wake_pipe[1], "q", 1);
    pthread_join(th, NULL);
    timer_delete(tid);
    ConnectDetach(coid); ChannelDestroy(chid);
    printf("sensor-hub done: %d samples, %d processed\n", samples, processed);
    return processed == samples ? 0 : 2;
}
