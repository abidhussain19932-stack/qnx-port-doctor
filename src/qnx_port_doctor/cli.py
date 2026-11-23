"""qnx-port-doctor command line."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from . import report as rep
from .generate import ARCHES, generate
from .scanner import scan, summarize


def cmd_scan(a) -> int:
    findings = scan(a.path)
    fmt = a.format
    out = {"text": rep.to_text, "json": rep.to_json, "sarif": rep.to_sarif}.get(fmt)
    text = out(findings) if out else rep.to_html(findings, Path(a.path).resolve().name)
    if a.output:
        Path(a.output).write_text(text)
        print(f"wrote {a.output}")
    else:
        print(text)
    s = summarize(findings)
    return 1 if (a.fail_on_error and s["error"]) else 0


def cmd_report(a) -> int:
    findings = scan(a.path)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    runlog = Path(a.runlog).read_text() if a.runlog else None
    (out / "report.html").write_text(rep.to_html(findings, Path(a.path).resolve().name, runlog))
    (out / "report.sarif").write_text(rep.to_sarif(findings))
    (out / "report.json").write_text(rep.to_json(findings))
    print(rep.to_text(findings).splitlines()[-1].strip())
    print(f"wrote {out}/report.html, report.sarif, report.json")
    return 0


def cmd_generate(a) -> int:
    for p in generate(Path(a.path), a.arch, a.name):
        print(f"generated {p}")
    return 0


def cmd_rules(a) -> int:
    print(rep.rules_table())
    return 0


def cmd_doctor(a) -> int:
    from . import target
    try:
        env = target.check_env()
    except target.QnxEnvError as e:
        print(f"[x] {e}")
        return 1
    for k, v in env.items():
        print(f"[ok] {k}: {v}")
    return 0


def cmd_build(a) -> int:
    from . import target
    out = target.build(Path(a.path), a.arch, a.cmake)
    print(f"built into {out}")
    return 0


def cmd_run(a) -> int:
    from . import target
    img = Path(a.image)
    if not (img / "output").exists():
        target.make_image(img, a.arch)
    ip = a.ip or target.boot(img)
    res = target.deploy_and_run(Path(a.binary), ip, args=a.args)
    log = res.stdout + res.stderr
    print(log)
    if a.log:
        Path(a.log).write_text(log)
    return res.returncode


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="qnx-port-doctor",
                                description="Find Linux-only APIs, generate QNX 8.0 build files, "
                                            "cross-build with qcc and run on a QNX QEMU target.")
    p.add_argument("--version", action="version", version=__version__)
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("scan", help="scan a source tree for Linux-only APIs")
    s.add_argument("path")
    s.add_argument("-f", "--format", choices=["text", "json", "sarif", "html"], default="text")
    s.add_argument("-o", "--output")
    s.add_argument("--fail-on-error", action="store_true", help="exit 1 if errors found (CI)")
    s.set_defaults(fn=cmd_scan)

    r = sub.add_parser("report", help="write HTML + SARIF + JSON reports")
    r.add_argument("path")
    r.add_argument("--out", default="qpd-report")
    r.add_argument("--runlog", help="include output captured from the QNX target")
    r.set_defaults(fn=cmd_report)

    g = sub.add_parser("generate", help="generate QNX CMake toolchain + Makefile.qnx")
    g.add_argument("path")
    g.add_argument("--arch", choices=list(ARCHES), default="x86_64")
    g.add_argument("--name")
    g.set_defaults(fn=cmd_generate)

    sub.add_parser("rules", help="list rules").set_defaults(fn=cmd_rules)
    sub.add_parser("doctor", help="check the QNX SDP 8.0 environment").set_defaults(fn=cmd_doctor)

    b = sub.add_parser("build", help="cross-build with qcc")
    b.add_argument("path")
    b.add_argument("--arch", choices=list(ARCHES), default="x86_64")
    b.add_argument("--cmake", action="store_true")
    b.set_defaults(fn=cmd_build)

    x = sub.add_parser("run", help="boot QNX 8.0 in QEMU, deploy a binary over ssh and run it")
    x.add_argument("binary")
    x.add_argument("--image", default="qnx-vm")
    x.add_argument("--arch", choices=list(ARCHES), default="x86_64")
    x.add_argument("--ip", help="use an already running target")
    x.add_argument("--log", help="save target output here")
    x.add_argument("args", nargs="*")
    x.set_defaults(fn=cmd_run)

    a = p.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
