import pytest

from metaiivm import VM
from metaiivm import op_TST, op_ID, op_NUM, op_SR


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
    op_ID(vm)

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
    op_NUM(vm)

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
    op_SR(vm)

    assert vm.switch == is_success
    assert vm.input() == vm_buf_end
