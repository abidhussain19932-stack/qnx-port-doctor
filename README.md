# QNX Port Doctor

Port Linux C/C++ code to **QNX Neutrino 8.0** without guesswork.

`qnx-port-doctor` is a host-side CLI (Linux, macOS, Windows) that:

1. **Scans** a C/C++ project for Linux-only APIs (epoll, eventfd, timerfd, signalfd, inotify, `<linux/*.h>`, `/proc` text files, `sched_setaffinity`, `prctl`, raw syscalls, glibc extensions, Linux link flags...) and explains the QNX 8.0 equivalent for each (poll, pulses + `MsgReceivePulse`, `timer_create(SIGEV_PULSE)`, `ThreadCtl(_NTO_TCTL_RUNMASK)`, `devctl`, `-lsocket`...).
2. **Generates QNX build files**: a CMake toolchain file for `qcc` and a `Makefile.qnx`.
3. **Cross-builds** with `qcc` from QNX SDP 8.0.
4. **Boots** a QNX 8.0 QEMU image (`mkqnximage`), **deploys** the binary over SSH and **runs** it.
5. Writes **HTML, SARIF 2.1.0 and JSON** reports (SARIF plugs into GitHub code scanning / VS Code).

| | |
|---|---|
| QNX version | QNX Software Development Platform (SDP) 8.0, QNX Neutrino RTOS 8.0 |
| Target | QEMU x86_64 virtual machine created with `mkqnximage` (aarch64le also supported for build files) |
| Toolchain | `qcc -Vgcc_ntox86_64` / `q++` from SDP 8.0 |
| Host | Python 3.9+ (no dependencies) |
| Licence | MIT |

## Install

```bash
git clone https://github.com/abidhussain19932-stack/qnx-port-doctor
cd qnx-port-doctor
pip install -e .
```

## Quick start

```bash
# 1. What would break on QNX?
qnx-port-doctor scan examples/sensor-hub-linux

# 2. Reports (HTML + SARIF + JSON)
qnx-port-doctor report examples/sensor-hub-linux --out qpd-report

# 3. Generate QNX build files for the ported code
qnx-port-doctor generate examples/sensor-hub-qnx --name sensor-hub

# 4. Cross-build with qcc (needs QNX SDP 8.0)
source ~/qnx800/qnxsdp-env.sh
qnx-port-doctor doctor
qnx-port-doctor build examples/sensor-hub-qnx

# 5. Boot QNX 8.0 in QEMU, deploy over ssh and run
qnx-port-doctor run examples/sensor-hub-qnx/build-qnx/x86_64/sensor-hub --image qnx-vm --log run.log -- 20
qnx-port-doctor report examples/sensor-hub-qnx --runlog run.log
```

`scan --fail-on-error` exits 1 when errors are found, so it works as a CI gate.

## The demo: sensor-hub

`examples/sensor-hub-linux` is a typical Linux event loop (epoll + timerfd + eventfd + inotify + `/proc/loadavg` + `sched_setaffinity` + `prctl`). The scanner reports 17 errors and a portability score of 0/100.

`examples/sensor-hub-qnx` is the port guided by the tool. It scores 100/100 and uses QNX-native mechanisms:

| Linux | QNX 8.0 port |
|---|---|
| `timerfd_create` + `epoll_wait` | `ChannelCreate` + `timer_create(SIGEV_PULSE)` + `MsgReceivePulse` |
| `eventfd` | `pipe()` + `poll()` |
| `sched_setaffinity` | `ThreadCtl(_NTO_TCTL_RUNMASK)` |
| `prctl(PR_SET_NAME)` | `pthread_setname_np` |
| `/proc/loadavg` | `sysconf(_SC_NPROCESSORS_ONLN)` |

### QNX-specific files

- `examples/sensor-hub-qnx/src/main.c`: QNX Neutrino port (channels, pulses, `ThreadCtl`)
- `examples/sensor-hub-qnx/Makefile.qnx`: generated qcc Makefile
- `examples/sensor-hub-qnx/qnx/qnx800-x86_64.cmake`: generated CMake toolchain file for SDP 8.0
- `src/qnx_port_doctor/target.py`: qcc build, `mkqnximage` QEMU boot, ssh deploy/run
- `src/qnx_port_doctor/rules.py`: Linux to QNX 8.0 portability rules

## Rules

Run `qnx-port-doctor rules`. Suppress a line with a `// qpd: ignore` comment.

## Tests

```bash
pip install pytest && pytest -q
```

## Status

Work in progress for the QNX Global Hackathon (Developer Tooling & Host Tools). Target run logs from QNX 8.0 in QEMU will be committed under `examples/sensor-hub-qnx/target-run/`.
