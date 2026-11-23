import json
from pathlib import Path

from qnx_port_doctor.scanner import scan, summarize
from qnx_port_doctor import report
from qnx_port_doctor.generate import generate
from qnx_port_doctor.cli import main

ROOT = Path(__file__).resolve().parents[1]
LINUX = ROOT / "examples" / "sensor-hub-linux"
QNX = ROOT / "examples" / "sensor-hub-qnx"


def ids(findings):
    return {f.rule_id for f in findings}


def test_linux_sample_flags_linux_apis():
    f = scan(LINUX)
    for rid in ["QPD001", "QPD002", "QPD003", "QPD005", "QPD007", "QPD008", "QPD009", "QPD016", "QPD017"]:
        assert rid in ids(f), rid
    assert summarize(f)["error"] > 5


def test_qnx_port_is_clean():
    f = scan(QNX)
    assert summarize(f)["error"] == 0
    assert summarize(f)["score"] == 100


def test_comments_and_ignore_are_skipped(tmp_path):
    (tmp_path / "a.c").write_text(
        "/* epoll_create1(0); */\n// eventfd(0,0);\nint x = epoll_create1(0); // qpd: ignore\n"
        "/* multi\n timerfd_create(0,0)\n*/\n")
    assert scan(tmp_path) == []


def test_linux_headers(tmp_path):
    (tmp_path / "b.c").write_text("#include <linux/if.h>\n#include <sys/syscall.h>\n")
    assert ids(scan(tmp_path)) == {"QPD006", "QPD010"}


def test_build_rules_only_apply_to_build_files(tmp_path):
    (tmp_path / "c.c").write_text('const char *s = "-lpthread";\n')
    (tmp_path / "Makefile").write_text("LDLIBS = -lpthread\n")
    f = scan(tmp_path)
    assert [(x.path, x.rule_id) for x in f] == [("Makefile", "QPD016")]


def test_sarif_is_valid_shape():
    doc = json.loads(report.to_sarif(scan(LINUX)))
    assert doc["version"] == "2.1.0"
    run = doc["runs"][0]
    assert run["tool"]["driver"]["name"] == "qnx-port-doctor"
    assert run["results"] and all(r["ruleId"].startswith("QPD") for r in run["results"])
    rule_ids = {r["id"] for r in run["tool"]["driver"]["rules"]}
    assert {r["ruleId"] for r in run["results"]} <= rule_ids


def test_html_report(tmp_path):
    assert main(["report", str(LINUX), "--out", str(tmp_path)]) == 0
    html = (tmp_path / "report.html").read_text()
    assert "QNX Neutrino 8.0" in html and "QPD001" in html


def test_generate_build_files(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "m.c").write_text("int main(void){return 0;}\n")
    files = generate(tmp_path, "aarch64le", "demo")
    tc = (tmp_path / "qnx" / "qnx800-aarch64le.cmake").read_text()
    assert "CMAKE_SYSTEM_NAME QNX" in tc and "gcc_ntoaarch64le" in tc
    mk = (tmp_path / "Makefile.qnx").read_text()
    assert "src/m.c" in mk and "qcc" in mk and "BIN     := $(OUT)/demo" in mk
    assert len(files) == 2


def test_fail_on_error_exit_code():
    assert main(["scan", str(LINUX), "--fail-on-error", "-f", "json", "-o", "/dev/null"]) == 1
    assert main(["scan", str(QNX), "--fail-on-error", "-f", "json", "-o", "/dev/null"]) == 0
