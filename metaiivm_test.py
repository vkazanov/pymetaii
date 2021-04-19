import io

import pytest

from metaiivm import VM, parse_file, Inst
from metaiivm import op_TST, op_ID, op_NUM, op_SR, op_CLL, op_R, op_SET
from metaiivm import op_B, op_BT, op_BF, op_BE
from metaiivm import op_CL, op_CI, op_GN1, op_GN2
from metaiivm import op_LB, op_OUT, op_ADR


#
# Test reading opcodes from a file

@pytest.mark.parametrize("code, instrs_want", [
    ("        ID\n", [Inst(op="ID")]),
    ("        ID ARG\n", [Inst(op="ID", arg="ARG")]),
    ("LBL\n        ID ARG\n", [Inst(op="ID", arg="ARG", labels=["LBL"])]),
    ("L01\nL02\n        ID ARG\n", [Inst(op="ID", arg="ARG", labels=["L01", "L02"])]),
    (
"""\
L2
        CLL AS
        BT L2
        SET
        BE\
""",
        [
            Inst(op="CLL", arg="AS", labels=["L2"]),
            Inst(op="BT", arg="L2"),
            Inst(op="SET"),
            Inst(op="BE"),
        ]),
])
def test_parse_file(code, instrs_want):
    instrs_got  = parse_file(io.StringIO(code))

    assert instrs_got == instrs_want


#
# Test ops

@pytest.mark.parametrize("vm_buf_begin, op_arg, vm_buf_end, is_success", [
    ("true", "true", "", True),
    ("   true1", "true", "1", True),
    ("   1true", "true", "1true", False),
    ("false", "true", "false", False),
    ("   false", "true", "false", False),
])
def test_op_TST(vm_buf_begin, op_arg, vm_buf_end, is_success):
    vm = VM(vm_buf_begin)
    op_TST(vm, op_arg)

    assert vm.switch == is_success
    assert vm.input() == vm_buf_end


@pytest.mark.parametrize("vm_buf_begin, token_found, vm_buf_end, is_success", [
    ("id", "id", "", True),
    ("    id", "id", "", True),
    ("    id1", "id1", "", True),
    ("    1id", None, "1id", False),
    ("1id", None, "1id", False),
])
def test_op_ID(vm_buf_begin, token_found, vm_buf_end, is_success):
    vm = VM(vm_buf_begin)
    op_ID(vm, None)

    assert vm.switch == is_success
    assert vm.input() == vm_buf_end
    if is_success:
        assert vm.token_buf == token_found


@pytest.mark.parametrize("vm_buf_begin, token_found, vm_buf_end, is_success", [
    ("id", None, "id", False),
    ("    id", None, "id", False),
    ("    id1", None, "id1", False),
    ("    1id", "1", "id", True),
    ("1id", "1", "id", True),
    ("123id", "123", "id", True),
    ("123", "123", "", True),
])
def test_op_NUM(vm_buf_begin, token_found, vm_buf_end, is_success):
    vm = VM(vm_buf_begin)
    op_NUM(vm, None)

    assert vm.switch == is_success
    assert vm.input() == vm_buf_end
    if is_success:
        assert vm.token_buf == token_found


@pytest.mark.parametrize("vm_buf_begin, vm_buf_end, is_success", [
    ("id", "id", False),
    ("    id", "id", False),
    ("    id1", "id1", False),
    ("    1id", "1id", False),
    ("'1id'", "", True),
    ("    '123id'", "", True),
    ("'123'id", "id", True),
])
def test_op_SR(vm_buf_begin, vm_buf_end, is_success):
    vm = VM(vm_buf_begin)
    op_SR(vm, None)

    assert vm.switch == is_success
    assert vm.input() == vm_buf_end


@pytest.mark.parametrize("label_target, pc_target", [
    ("TARGET1", 10)
])
def test_op_CLL(label_target, pc_target):
    vm = VM("bla")
    pc_original = vm.pc
    vm.label_to_pc[label_target] = pc_target
    vm.label1_set("label1_orig")
    vm.label2_set("label2_orig")

    assert pc_original != pc_target
    assert vm.label1() == "label1_orig"
    assert vm.label2() == "label2_orig"

    op_CLL(vm, label_target)
    assert vm.pc == pc_target
    assert vm.label1() is None
    assert vm.label2() is None


@pytest.mark.parametrize("label_target, pc_target", [
    ("TARGET1", 10)
])
def test_op_R(label_target, pc_target):
    vm = VM("bla")
    pc_original = vm.pc
    vm.label_to_pc[label_target] = pc_target
    vm.label1_set("label1_orig")
    vm.label2_set("label2_orig")

    assert pc_original != pc_target
    assert vm.label1() == "label1_orig"
    assert vm.label2() == "label2_orig"

    op_CLL(vm, label_target)
    assert vm.pc == pc_target
    assert vm.label1() is None
    assert vm.label2() is None

    op_R(vm, None)
    assert pc_original == vm.pc
    assert vm.label1() == "label1_orig"
    assert vm.label2() == "label2_orig"


@pytest.mark.parametrize("switch_orig", [
    (True), (False)
])
def test_op_SET(switch_orig):
    vm = VM("bla")
    vm.switch = switch_orig

    op_SET(vm, None)
    assert vm.switch is True


@pytest.mark.parametrize("switch, label_target, pc_target", [
    (True, "TARGET", 10),
    (False, "TARGET", 10),
])
def test_op_B(switch, label_target, pc_target):
    vm = VM("bla")
    vm.label_to_pc[label_target] = pc_target
    vm.switch = switch
    vm_orig = vm.pc
    assert vm_orig != pc_target

    op_B(vm, "TARGET")
    assert vm.pc == pc_target


@pytest.mark.parametrize("switch, must_jump, label_target, pc_target", [
    (True, True, "TARGET", 10),
    (False, False, "TARGET", 10),
])
def test_op_BT(switch, must_jump, label_target, pc_target):
    vm = VM("bla")
    vm.label_to_pc[label_target] = pc_target
    vm.switch = switch
    vm_orig = vm.pc
    assert vm_orig != pc_target

    op_BT(vm, "TARGET")
    if must_jump:
        assert vm.pc == pc_target
    else:
        assert vm.pc == vm_orig


@pytest.mark.parametrize("switch, must_jump, label_target, pc_target", [
    (True, False, "TARGET", 10),
    (False, True, "TARGET", 10),
])
def test_op_BF(switch, must_jump, label_target, pc_target):
    vm = VM("bla")
    vm.label_to_pc[label_target] = pc_target
    vm.switch = switch
    vm_orig = vm.pc
    assert vm_orig != pc_target

    op_BF(vm, "TARGET")
    if must_jump:
        assert vm.pc == pc_target
    else:
        assert vm.pc == vm_orig


@pytest.mark.parametrize("switch, must_err", [
    (True, False),
    (False, True),
])
def test_op_BE(switch, must_err):
    vm = VM("bla")
    vm.switch = switch

    assert not vm.is_err
    op_BE(vm, None)
    if must_err:
        assert vm.is_err
    else:
        assert not vm.is_err


def test_op_CL():
    vm = VM("bla")

    assert not vm.output_buf
    op_CL(vm, "test")
    assert vm.output_buf[-1] == "test"


def test_op_CI():
    vm = VM("bla")
    vm.token_buf = "test"

    assert not vm.output_buf
    op_CI(vm, None)
    assert vm.output_buf[-1] == "test"


def test_op_GN1():
    vm = VM("bla")
    assert vm.label_counter == 0
    assert vm.label1() is None
    op_GN1(vm, None)
    assert vm.label1() == "L0"
    assert vm.output_buf[-1] == "L0"


def test_op_GN2():
    vm = VM("bla")
    assert vm.label_counter == 0
    assert vm.label2() is None
    op_GN2(vm, None)
    assert vm.label2() == "L0"
    assert vm.output_buf[-1] == "L0"


def test_op_LB():
    vm = VM("bla")
    vm.output_column = 10
    op_LB(vm, None)
    assert vm.output_column == 0


def test_op_OUT():
    output = io.StringIO()
    vm = VM("bla", output_file=output)
    vm.output_column = 0
    vm.output_buf = ["teststr"]

    op_OUT(vm, None)
    assert len(vm.output_buf) == 0
    assert vm.output_col == 8
    assert output.getvalue() == "teststr\n"


def test_op_ADR():
    vm = VM("bla")
    vm.label_to_pc["START"] = 100

    assert vm.pc == 0
    op_ADR(vm, "START")
    assert vm.pc == 100


def test_op_END():
    # noop
    pass
