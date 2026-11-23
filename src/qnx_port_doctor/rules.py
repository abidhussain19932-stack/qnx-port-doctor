"""Portability rules: Linux-only APIs and their QNX 8.0 equivalents.

Each rule has a stable id (used in SARIF), a regex matched per source line,
a severity, and advice describing the QNX Neutrino 8.0 replacement.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Rule:
    id: str
    title: str
    pattern: str
    severity: str  # "error" = will not compile/run on QNX, "warning" = behaves differently, "note" = review
    qnx_equivalent: str
    docs: str = "https://www.qnx.com/developers/docs/8.0/"
    autofix: str | None = None  # name of a shim header in qnx_port_doctor/shims, if any
    regex: re.Pattern = field(init=False, repr=False, compare=False)

    def __post_init__(self):
        object.__setattr__(self, "regex", re.compile(self.pattern))


RULES: list[Rule] = [
    Rule("QPD001", "epoll is Linux-only",
         r"\bepoll_(create1?|ctl|wait|pwait)\b|<sys/epoll\.h>",
         "error",
         "Use poll()/select() (POSIX, available on QNX), or ionotify() with pulses delivered to a "
         "channel for scalable event loops. libevent/libuv already have QNX backends."),
    Rule("QPD002", "eventfd is Linux-only",
         r"\beventfd(_read|_write)?\s*\(|<sys/eventfd\.h>",
         "error",
         "Use a pipe() pair (write one byte to wake, poll the read end), or a QNX pulse "
         "(MsgSendPulse) on a channel/connection."),
    Rule("QPD003", "timerfd is Linux-only",
         r"\btimerfd_(create|settime|gettime)\b|<sys/timerfd\.h>",
         "error",
         "Use POSIX timer_create() with SIGEV_PULSE (QNX) or SIGEV_THREAD, or compute the "
         "timeout for poll() from clock_gettime(CLOCK_MONOTONIC)."),
    Rule("QPD004", "signalfd is Linux-only",
         r"\bsignalfd\s*\(|<sys/signalfd\.h>",
         "error",
         "Block the signals and use sigwaitinfo() in a dedicated thread, or SignalAction()/"
         "sigevent pulses to turn signals into messages on a channel."),
    Rule("QPD005", "inotify is Linux-only",
         r"\binotify_(init1?|add_watch|rm_watch)\b|<sys/inotify\.h>",
         "error",
         "QNX provides inotify-compatible notifications through the io-notify interface: "
         "include <sys/inotify.h> from QNX's libc only where supported, otherwise poll file "
         "mtimes or use ionotify() on the resource manager."),
    Rule("QPD006", "Linux kernel headers",
         r"#\s*include\s*<linux/[^>]+>",
         "error",
         "<linux/*.h> does not exist on QNX. Find the POSIX header (e.g. <netinet/in.h>, "
         "<net/if.h>) or the QNX driver/devctl interface (<devctl.h>, <sys/dcmd_*.h>)."),
    Rule("QPD007", "/proc layout differs",
         r"\"/proc/(self/|[0-9]+/)?(stat|status|maps|meminfo|cpuinfo|loadavg|net/|exe|fd/)[^\"]*\"",
         "warning",
         "QNX has /proc/<pid>/as and /proc/<pid>/ctl rather than Linux text files. Use "
         "devctl(DCMD_PROC_*) on /proc/<pid>/as, or sysconf()/SYSPAGE_ENTRY() for system info."),
    Rule("QPD008", "CPU affinity API differs",
         r"\b(sched_setaffinity|sched_getaffinity|pthread_setaffinity_np|CPU_SET|CPU_ZERO)\b",
         "error",
         "Use ThreadCtl(_NTO_TCTL_RUNMASK_GET_AND_SET_INHERIT, ...) with a runmask, or "
         "'on -C' at launch."),
    Rule("QPD009", "prctl is Linux-only",
         r"\bprctl\s*\(|<sys/prctl\.h>",
         "error",
         "Thread names: pthread_setname_np(). Privileges: QNX procmgr abilities "
         "(procmgr_ability())."),
    Rule("QPD010", "Raw Linux syscalls",
         r"\bsyscall\s*\(\s*(SYS_|__NR_)\w+|<sys/syscall\.h>",
         "error",
         "QNX is a microkernel; there is no Linux syscall table. Replace with the libc function "
         "(e.g. gettid() -> gettid() on QNX 8 / pthread_self())."),
    Rule("QPD011", "sendfile/splice are Linux-only",
         r"\b(sendfile|splice|tee|vmsplice)\s*\(|<sys/sendfile\.h>",
         "warning",
         "Fall back to a read()/write() loop with a reusable buffer, or mmap() + write()."),
    Rule("QPD012", "Linux-specific socket options",
         r"\b(SO_BINDTODEVICE|SO_PRIORITY|TCP_CORK|SOCK_NONBLOCK|SOCK_CLOEXEC|MSG_MORE|accept4)\b",
         "warning",
         "Set O_NONBLOCK/FD_CLOEXEC with fcntl() after socket()/accept(); QNX io-sock is "
         "FreeBSD-derived, so prefer BSD options (e.g. IP_BOUND_IF where available)."),
    Rule("QPD013", "glibc-only extensions",
         r"\b(backtrace|backtrace_symbols|malloc_usable_size|mallinfo|get_nprocs|program_invocation_name|__progname_full)\b|<execinfo\.h>|<malloc\.h>",
         "warning",
         "Not in QNX libc. Use sysconf(_SC_NPROCESSORS_ONLN), getprogname(), and the QNX "
         "backtrace library (libbacktrace) where needed."),
    Rule("QPD014", "Linux futex",
         r"\bFUTEX_(WAIT|WAKE)\b|<linux/futex\.h>",
         "error",
         "Use pthread mutexes/condvars or C11 atomics; QNX SyncMutex*/SyncCondvar* underlie them."),
    Rule("QPD015", "Linux-only memory APIs",
         r"\b(memfd_create|mremap|madvise\s*\(\s*\w+\s*,\s*\w+\s*,\s*MADV_(DONTDUMP|HUGEPAGE))\b",
         "warning",
         "Use shm_open()/shm_ctl() (QNX typed memory, SHMCTL_ANON) or posix_typed_mem_open()."),
    Rule("QPD016", "GNU ld / -ldl / -lrt / -lpthread link flags",
         r"(-lrt\b|-lpthread\b|-ldl\b|-Wl,--as-needed|-static-libgcc)",
         "note",
         "On QNX, pthread, rt and dl live in libc; drop -lpthread/-lrt/-ldl. Sockets need -lsocket."),
    Rule("QPD017", "Hard-coded gcc/clang compiler",
         r"\b(CC\s*[:?]?=\s*(gcc|clang)|CMAKE_C_COMPILER\s+(gcc|clang))\b",
         "note",
         "Cross-compile with qcc: qcc -Vgcc_ntox86_64 (x86_64) or -Vgcc_ntoaarch64le (aarch64). "
         "Use the generated QNX CMake toolchain file."),
    Rule("QPD018", "Sockets need libsocket",
         r"\b(socket|getaddrinfo|inet_pton)\s*\(",
         "note",
         "Works on QNX, but link with -lsocket (the generated build files do this)."),
]

RULES_BY_ID = {r.id: r for r in RULES}

C_EXTS = {".c", ".h", ".cc", ".cpp", ".cxx", ".hpp", ".hh", ".hxx"}
BUILD_FILES = {"Makefile", "makefile", "GNUmakefile", "CMakeLists.txt"}
BUILD_ONLY_RULES = {"QPD016", "QPD017"}
