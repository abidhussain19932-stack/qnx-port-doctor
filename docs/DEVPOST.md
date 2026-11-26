# QNX Port Doctor — Devpost text

**Category:** Developer Tooling & Host Tools

## Inspiration
Porting Linux C/C++ code to QNX 8.0 means hunting epoll, inotify, eventfd, signalfd, /proc and <linux/*.h> uses by hand.

## What it does
A Python host CLI that scans a Linux project, flags non-portable APIs (rules QPD001-018), explains the QNX 8.0 equivalent (ionotify, pulses/MsgSend, ThreadCtl, procfs differences), generates QNX build files, cross-builds with qcc, boots a QEMU x86_64 QNX 8.0 image, deploys and runs the binary, and writes text/JSON/SARIF/HTML reports.

## QNX-specific files
- src/qnx_port_doctor/generate.py -> qnx-toolchain.cmake, Makefile.qnx (qcc, -V gcc_ntox86_64)
- src/qnx_port_doctor/target.py -> qcc build, mkqnximage QEMU, ssh deploy/run
- examples/sensor-hub-linux (17 errors) and examples/sensor-hub-qnx (pulses/ThreadCtl port, 100/100)
- docs/QNX_SETUP.md, docs/CODELAB.md (tutorial)

## How to build and run
QNX SDP 8.0 (free non-commercial), qcc, target QEMU x86_64. See docs/QNX_SETUP.md.

## Challenges / Accomplishments / Next
Mapping epoll/inotify semantics onto QNX primitives; SARIF output works in VS Code. Next: more rules and auto-fix hints.

## Links
Repo: https://github.com/abidhussain19932-stack/qnx-port-doctor
Video: TODO (Abid's own recording, see docs/VIDEO_SCRIPT.md)
