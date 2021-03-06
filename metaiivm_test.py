import io

import pytest

from metaiivm import VM, parse_code, Inst


# Test the AEXP example language
@pytest.mark.parametrize("masm_file, aexp_file, result_file", [
    # expression language
    ("tests/aexp.masm", "tests/aexp_expr.aexp",
     "tests/aexp_expr.output"),
    ("tests/aexp.masm", "tests/aexp_expr_simple.aexp",
     "tests/aexp_expr_simple.output"),
    ("tests/aexp_add.masm", "tests/aexp_add.aexp",
     "tests/aexp_add.output"),

    # let's compile the compiler and see if it's circular
    ("metaii.masm", "metaii.meta",
     "metaii.masm"),
])
def test_aexp(masm_file, aexp_file, result_file):
    code = parse_code(open(masm_file))
    expr = open(aexp_file).read()
    result = open(result_file).read()

    output_file = io.StringIO()
    vm = VM(expr, output_file)

    vm.run(code)
    assert result == output_file.getvalue()


#
# Test executing programs

@pytest.mark.parametrize("input_buf, code, output", [
    # Just stop immediately
    ("bla", [Inst(op="END", arg=None, labels=[])], ""),

    # Output a string twice
    ("bla", [
         Inst(op="ID", arg=None, labels=[]),
         Inst(op="CI", arg=None, labels=[]),
         Inst(op="CI", arg=None, labels=[]),
         Inst(op="OUT", arg=None, labels=[]),
         Inst(op="END", arg=None, labels=[]),
     ], "        blabla\n"),

    # Output a label and a string
    ("", [
         Inst(op="CL", arg="test1", labels=[]),
         Inst(op="OUT", arg=None, labels=[]),

         Inst(op="LB", arg=None, labels=[]),
         Inst(op="GN1", arg=None, labels=[]),
         Inst(op="OUT", arg=None, labels=[]),

         Inst(op="CL", arg="test2", labels=[]),
         Inst(op="OUT", arg=None, labels=[]),
         Inst(op="END", arg=None, labels=[]),
     ], "        test1\nL1\n        test2\n"),

    # Skip some code
    ("bla bla2", [
         Inst(op="ADR", arg="START", labels=[]),
         Inst(op="CL", arg="before", labels=[]),
         Inst(op="CL", arg="before1", labels=[]),
         Inst(op="CL", arg="before2", labels=[]),
         Inst(op="CL", arg="after", labels=["START"]),
         Inst(op="OUT", arg=None, labels=[]),
         Inst(op="END", arg=None, labels=[]),
     ], "        after\n"),

    # Check a string, successfully jump
    ("correct bla2", [
         Inst(op="TST", arg="correct", labels=[]),
         Inst(op="BT", arg="CORRECT", labels=[]),
         Inst(op="CL", arg="failure!", labels=[]),
         Inst(op="B", arg="OUTPUT", labels=[]),

         Inst(op="CL", arg="success!", labels=["CORRECT"]),

         Inst(op="OUT", arg=None, labels=["OUTPUT"]),
         Inst(op="END", arg=None, labels=[]),
     ], "        success!\n"),

    # Check a string, do not jump
    ("invalid bla2", [
         Inst(op="TST", arg="correct", labels=[]),
         Inst(op="BT", arg="CORRECT", labels=[]),
         Inst(op="CL", arg="failure!", labels=[]),
         Inst(op="B", arg="OUTPUT", labels=[]),

         Inst(op="CL", arg="success!", labels=["CORRECT"]),

         Inst(op="OUT", arg=None, labels=["OUTPUT"]),
         Inst(op="END", arg=None, labels=[]),
     ], "        failure!\n"),

    # Check an input str, make a call if correct
    ("correct bla2", [
         Inst(op="ADR", arg="START", labels=[]),

         Inst(op="TST", arg="correct", labels=["START"]),
         Inst(op="BF", arg="END", labels=[]),
         Inst(op="CLL", arg="FUNCTIONLABEL", labels=[]),
         Inst(op="CL", arg="after", labels=[]),
         Inst(op="OUT", arg=None, labels=[]),
         Inst(op="END", arg=None, labels=["END"]),

         Inst(op="CL", arg="function", labels=["FUNCTIONLABEL"]),
         Inst(op="R", arg=None, labels=[]),
     ], "        functionafter\n"),
])
def test_run(input_buf, code, output):
    output_file = io.StringIO()
    vm = VM(input_buf, output_file)
    vm.run(code)

    assert output == output_file.getvalue()


#
# Test reading opcodes from a file

@pytest.mark.parametrize("input_, instrs_want", [
    ("        ID\n", [Inst(op="ID", arg=None, labels=[])]),
    ("        ID ARG\n", [Inst(op="ID", arg="ARG", labels=[])]),
    ("        ID 'ARG BLA'\n", [Inst(op="ID", arg="ARG BLA", labels=[])]),
    ("        ID ''\n", [Inst(op="ID", arg="", labels=[])]),
    ("LBL\n        ID ARG\n", [Inst(op="ID", arg="ARG", labels=["LBL"])]),
    (
        "L01\nL02\n        ID ARG\n",
        [Inst(op="ID", arg="ARG", labels=["L01", "L02"])]
    ),
    ((
        "L2\n"
        "        CLL AS\n"
        "        BT L2\n"
        "        SET\n"
        "        BE"
    ),
     [
         Inst(op="CLL", arg="AS", labels=["L2"]),
         Inst(op="BT", arg="L2", labels=[]),
         Inst(op="SET", arg=None, labels=[]),
         Inst(op="BE", arg=None, labels=[]),
     ]),
])
def test_parse_file(input_, instrs_want):
    instrs_got = parse_code(io.StringIO(input_))

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
    vm.op_TST(op_arg)

    assert vm.switch == is_success
    assert vm.input() == vm_buf_end


@pytest.mark.parametrize("vm_buf_begin, token_found, vm_buf_end, is_success", [
    ("res:=5+6;", "res", ":=5+6;", True),
    ("id", "id", "", True),
    ("    id", "id", "", True),
    ("    id1", "id1", "", True),
    ("    1id", None, "1id", False),
    ("1id", None, "1id", False),
    ("", None, "", False),
])
def test_op_ID(vm_buf_begin, token_found, vm_buf_end, is_success):
    vm = VM(vm_buf_begin)
    vm.op_ID(None)

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
    vm.op_NUM(None)

    assert vm.switch == is_success
    assert vm.input() == vm_buf_end
    if is_success:
        assert vm.token_buf == token_found


@pytest.mark.parametrize("vm_buf_begin, token_found, vm_buf_end, is_success", [
    ("id", None, "id", False),
    ("    id", None, "id", False),
    ("    id1", None, "id1", False),
    ("    1id", None, "1id", False),
    ("'1id'", "'1id'", "", True),
    ("    '123id'", "'123id'", "", True),
    ("'123'id", "'123'", "id", True),
])
def test_op_SR(vm_buf_begin, token_found, vm_buf_end, is_success):
    vm = VM(vm_buf_begin)

    vm.token_buf is None
    vm.op_SR(None)

    assert vm.switch == is_success
    assert vm.token_buf == token_found
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

    vm.op_CLL(label_target)
    assert vm.pc == pc_target
    assert vm.label1() is None
    assert vm.label2() is None


@pytest.mark.parametrize("label_target, pc_target, is_done", [
    ("TARGET1", 10, False)
])
def test_op_R_call(label_target, pc_target, is_done):
    vm = VM("bla")
    pc_original = vm.pc
    vm.label_to_pc[label_target] = pc_target
    vm.label1_set("label1_orig")
    vm.label2_set("label2_orig")

    assert pc_original != pc_target
    assert vm.label1() == "label1_orig"
    assert vm.label2() == "label2_orig"

    vm.op_CLL(label_target)
    assert vm.pc == pc_target
    assert vm.label1() is None
    assert vm.label2() is None

    assert vm.is_done is False
    vm.op_R(None)
    assert vm.is_done is is_done
    assert pc_original + 1 == vm.pc
    assert vm.label1() == "label1_orig"
    assert vm.label2() == "label2_orig"


def test_op_R_done():
    # it's kinda unusual that calling R without a prior CLL call also halts the
    # VM - and that's the correct way to do it. Feels error prone. Oh, well...

    vm = VM("bla")

    assert vm.is_done is False
    vm.op_R(None)
    assert vm.is_done is True


@pytest.mark.parametrize("switch_orig", [
    (True), (False)
])
def test_op_SET(switch_orig):
    vm = VM("bla")
    vm.switch = switch_orig

    vm.op_SET(None)
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

    vm.op_B("TARGET")
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

    vm.op_BT("TARGET")
    if must_jump:
        assert vm.pc == pc_target
    else:
        assert vm.pc == vm_orig + 1


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

    vm.op_BF("TARGET")
    if must_jump:
        assert vm.pc == pc_target
    else:
        assert vm.pc == vm_orig + 1


@pytest.mark.parametrize("switch, must_err", [
    (True, False),
    (False, True),
])
def test_op_BE(switch, must_err):
    vm = VM("bla")
    vm.switch = switch

    assert not vm.is_err
    vm.op_BE(None)
    if must_err:
        assert vm.is_err
    else:
        assert not vm.is_err


def test_op_CL():
    vm = VM("bla")

    assert not vm.output_buf
    vm.op_CL("test")
    assert vm.output_buf[-1] == "test"


def test_op_CI():
    vm = VM("bla")
    vm.token_buf = "test"

    assert not vm.output_buf
    vm.op_CI(None)
    assert vm.output_buf[-1] == "test"


def test_op_GN1():
    vm = VM("bla")
    assert vm.label_counter == 1
    assert vm.label1() is None
    vm.op_GN1(None)
    assert vm.label1() == "L1"
    assert vm.output_buf[-1] == "L1"


def test_op_GN2():
    vm = VM("bla")
    assert vm.label_counter == 1
    assert vm.label2() is None
    vm.op_GN2(None)
    assert vm.label2() == "L1"
    assert vm.output_buf[-1] == "L1"


def test_op_LB():
    vm = VM("bla")
    vm.output_col = 10
    vm.op_LB(None)
    assert vm.output_col == 0


def test_op_OUT():
    output = io.StringIO()
    vm = VM("bla", output_file=output)
    vm.output_col = 0
    vm.output_buf = ["teststr", "teststr2"]

    vm.op_OUT(None)
    assert len(vm.output_buf) == 0
    assert vm.output_col == 8
    assert output.getvalue() == "teststrteststr2\n"


def test_op_ADR():
    # TODO: Should be a metaop? Just a starting pc?
    vm = VM("bla")
    vm.label_to_pc["START"] = 100

    assert vm.pc == 0
    vm.op_ADR("START")
    assert vm.pc == 100


def test_op_END():
    # dummy op, end of input
    pass
