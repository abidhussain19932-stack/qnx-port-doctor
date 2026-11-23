# Running QNX Port Doctor against real QNX 8.0 (QEMU)

The QNX SDP 8.0 non-commercial licence allows installing the SDP on your own developer machine
(up to two), but **not in a cloud computing environment** (licence section 4.2.6). So the
qcc build and the QEMU run are done on a local Linux PC (Ubuntu 22.04/24.04, native or in a
local VM such as VirtualBox/WSL2 with nested virtualisation).

## 1. Get the free licence and QNX Software Center
1. Sign in at https://www.qnx.com/account/ and open the myQNX License Manager
   (https://www.qnx.com/account/dashboard/). The *QNX SDP 8.0 Non-Commercial Single-User License*
   should show as **Deployed**. (Free licence: https://www.qnx.com/products/everywhere/)
2. Download *QNX Software Center 2.0.4 - Linux Hosts*:
   https://www.qnx.com/download/download/79441/qnx-setup-2.0.4-202501021438-linux.run

```bash
chmod +x qnx-setup-*-linux.run
./qnx-setup-*-linux.run            # installs QNX Software Center to ~/qnx/qnxsoftwarecenter
~/qnx/qnxsoftwarecenter/qnxsoftwarecenter   # sign in with your myQNX account
```
3. In QNX Software Center: **Add Installation -> QNX Software Development Platform 8.0**,
   install to `~/qnx800` (accept defaults, licence is picked up from myQNX).

## 2. Host packages
```bash
sudo apt update
sudo apt install -y qemu-system-x86 qemu-utils bridge-utils net-tools openssh-client python3-pip git make cmake
```

## 3. Environment check
```bash
source ~/qnx800/qnxsdp-env.sh
git clone https://github.com/abidhussain19932-stack/qnx-port-doctor && cd qnx-port-doctor
pip install -e .
qnx-port-doctor doctor          # prints QNX_HOST, QNX_TARGET and qcc versions
```

## 4. Cross-build the ported demo with qcc
```bash
qnx-port-doctor build examples/sensor-hub-qnx
file examples/sensor-hub-qnx/build-qnx/x86_64/sensor-hub   # ELF 64-bit x86-64, QNX
```

## 5. Boot QNX 8.0 in QEMU and run it
```bash
mkdir -p ~/qnxvm && cd ~/qnxvm
mkqnximage --type=qemu --arch=x86_64 --ip=dhcp --run    # first run builds the image, then boots it
# in a second terminal:
cd ~/qnxvm && mkqnximage --getip                        # prints the VM's IP
```
Default login is `root` / `root` (see `mkqnximage --help` for options such as `--ssh-ident`).

```bash
cd ~/qnx-port-doctor
qnx-port-doctor run examples/sensor-hub-qnx/build-qnx/x86_64/sensor-hub \
    --ip <VM-IP> --log examples/sensor-hub-qnx/target-run/run.log -- 20
qnx-port-doctor report examples/sensor-hub-qnx --runlog examples/sensor-hub-qnx/target-run/run.log \
    --out examples/sensor-hub-qnx/target-run
```
Expected output starts with `sensor-hub on QNX 8.0.0 (x86_64)` and ends with
`sensor-hub done: 20 samples, 20 processed`.

## 6. Commit the evidence
```bash
git add examples/sensor-hub-qnx/build-qnx examples/sensor-hub-qnx/target-run
git commit -m "QNX 8.0 qcc build output and QEMU target run log" && git push
```
