from qnx_port_doctor.rules import RULES_BY_ID
import re

def test_timerfd_memfd():
    assert RULES_BY_ID["QPD019"].regex.search("fd = timerfd_create(0,0);")
    assert RULES_BY_ID["QPD020"].regex.search("memfd_create(\"x\",0)")
