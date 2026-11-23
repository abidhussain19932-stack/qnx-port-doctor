"""Cross-build with qcc, boot a QNX 8.0 QEMU image, deploy and run over SSH.

Requires QNX SDP 8.0 installed and its environment sourced
(`source ~/qnx800/qnxsdp-env.sh`), which provides qcc and mkqnximage.
"""
from __future__ import annotations

import os
import shutil
import socket
import subprocess
import time
from pathlib import Path


class QnxEnvError(RuntimeError):
    pass


def check_env() -> dict:
    host, target = os.environ.get("QNX_HOST"), os.environ.get("QNX_TARGET")
    if not host or not target:
        raise QnxEnvError("QNX SDP environment not found. Run: source ~/qnx800/qnxsdp-env.sh")
    qcc = shutil.which("qcc")
    if not qcc:
        raise QnxEnvError("qcc not on PATH; re-source qnxsdp-env.sh")
    ver = subprocess.run([qcc, "-V"], capture_output=True, text=True).stderr.strip()
    return {"QNX_HOST": host, "QNX_TARGET": target, "qcc": qcc, "qcc_versions": ver}


def run(cmd: list[str], cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess:
    print("+", " ".join(cmd), flush=True)
    return subprocess.run(cmd, cwd=cwd, check=check, text=True)


def build(project: Path, arch: str = "x86_64", use_cmake: bool = False) -> Path:
    check_env()
    project = Path(project).resolve()
    if use_cmake and (project / "CMakeLists.txt").exists():
        bdir = project / "build-qnx" / arch
        run(["cmake", "-S", str(project), "-B", str(bdir),
             f"-DCMAKE_TOOLCHAIN_FILE={project / 'qnx' / f'qnx800-{arch}.cmake'}"])
        run(["cmake", "--build", str(bdir)])
        return bdir
    run(["make", "-f", "Makefile.qnx", f"ARCH={arch}"], cwd=project)
    return project / "build-qnx" / arch


def make_image(workdir: Path, arch: str = "x86_64") -> Path:
    """Create a QEMU QNX 8.0 image with mkqnximage (ships with SDP 8.0)."""
    check_env()
    workdir = Path(workdir).resolve()
    workdir.mkdir(parents=True, exist_ok=True)
    run(["mkqnximage", "--type=qemu", f"--arch={arch}", "--ssh-ident=none", "--hostname=qnxpd",
         "--ip=dhcp", "--noprompt"], cwd=workdir)
    return workdir


def _ip_from_image(workdir: Path) -> str:
    f = Path(workdir) / "output" / "ip"
    if f.exists():
        return f.read_text().strip()
    return "172.31.1.11"  # mkqnximage default for the qemu bridge


def boot(workdir: Path, wait: int = 90) -> str:
    workdir = Path(workdir).resolve()
    subprocess.Popen(["mkqnximage", "--run=-h"], cwd=workdir,
                     stdout=open(workdir / "qemu.log", "w"), stderr=subprocess.STDOUT)
    ip = _ip_from_image(workdir)
    deadline = time.time() + wait
    while time.time() < deadline:
        try:
            with socket.create_connection((ip, 22), timeout=2):
                return ip
        except OSError:
            time.sleep(2)
    raise TimeoutError(f"QNX VM did not open ssh on {ip}:22 within {wait}s; see qemu.log")


SSH_OPTS = ["-o", "StrictHostKeyChecking=no", "-o", "UserKnownHostsFile=/dev/null"]


def deploy_and_run(binary: Path, ip: str, user: str = "root", args: list[str] | None = None,
                   remote_dir: str = "/data/home/root") -> subprocess.CompletedProcess:
    binary = Path(binary)
    run(["scp", *SSH_OPTS, str(binary), f"{user}@{ip}:{remote_dir}/"])
    remote = f"cd {remote_dir} && uname -a && ./{binary.name} {' '.join(args or [])}"
    print("+ ssh", remote, flush=True)
    return subprocess.run(["ssh", *SSH_OPTS, f"{user}@{ip}", remote], text=True, capture_output=True)
