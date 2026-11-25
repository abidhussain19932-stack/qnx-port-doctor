# Demo video script (under 3:00, your own screen + your own voice)
1. 0:00-0:15 Intro: "I'm Abid. QNX Port Doctor ports Linux C code to QNX 8.0." Show README.
2. 0:15-0:45 Terminal: `python -m qnx_port_doctor scan examples/sensor-hub-linux` - point out epoll/inotify/eventfd errors and QNX equivalents.
3. 0:45-1:10 `report --format html`; open report in browser, then SARIF in VS Code.
4. 1:10-1:35 `generate` - show qnx.toolchain.cmake and Makefile.qnx (qcc, x86_64).
5. 1:35-2:15 `build` with qcc (QNX SDP 8.0 env sourced) - show binary built.
6. 2:15-2:45 Boot QEMU QNX 8.0 image (mkqnximage), `run`, show test output on QNX (uname -a shows QNX).
7. 2:45-2:58 Rescan ported example: 100/100. Mention repo URL + CODELAB.md.
Upload to YouTube as Public; send me the link.
