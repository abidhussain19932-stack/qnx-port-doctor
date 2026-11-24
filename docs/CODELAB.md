# Codelab: Port a Linux C project to QNX 8.0 with QNX Port Doctor

Time: ~30 min. Target: QNX 8.0 on QEMU x86_64. Toolchain: qcc (QNX SDP 8.0, free non-commercial licence).

## 1. Prerequisites
- QNX SDP 8.0 installed on your own PC (see docs/QNX_SETUP.md); `source ~/qnx800/qnxsdp-env.sh`
- Python 3.9+, git

## 2. Get the tool
```
git clone https://github.com/abidhussain19932-stack/qnx-port-doctor
cd qnx-port-doctor && export PYTHONPATH=src
```

## 3. Scan the Linux sample
```
python3 -m qnx_port_doctor scan examples/sensor-hub-linux
```
You get 17 findings (epoll, inotify, eventfd, signalfd, /proc, <linux/*.h>...), each with a rule ID (QPD001-018) and the QNX 8.0 replacement (ionotify, pulses/MsgSend, ThreadCtl...).

## 4. Read the report
```
python3 -m qnx_port_doctor report examples/sensor-hub-linux --format html > report.html
python3 -m qnx_port_doctor report examples/sensor-hub-linux --format sarif > report.sarif
```
Open the SARIF in VS Code (SARIF Viewer extension) to jump to each line.

## 5. Apply the fixes
Replace each finding using the hints. examples/sensor-hub-qnx is the finished port (scores 100/100):
```
python3 -m qnx_port_doctor scan examples/sensor-hub-qnx
```

## 6. Generate QNX build files
```
python3 -m qnx_port_doctor generate examples/sensor-hub-qnx
```
Creates a qcc CMake toolchain file and Makefile.qnx.

## 7. Cross-build with qcc
```
python3 -m qnx_port_doctor doctor
python3 -m qnx_port_doctor build examples/sensor-hub-qnx
```

## 8. Boot QNX in QEMU and run
```
python3 -m qnx_port_doctor run examples/sensor-hub-qnx
```
This uses mkqnximage to boot QNX 8.0 under QEMU, deploys over ssh and runs the binary. Save the output to examples/sensor-hub-qnx/target-run/run.log.

## 9. Add to CI
Use the SARIF output with GitHub code scanning to block new Linux-only calls.
