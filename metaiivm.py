#!/usr/bin/env python3
import re


class VM:

    def __init__(self, input_buf):
        self.input_buf_index = 0
        self.input_buf = input_buf

        self.token_buf = None
        self.switch = False

    def input(self):
        return self.input_buf[self.input_buf_index:]

    def skip_space(self):
        while self.input_buf[self.input_buf_index].isspace():
            self.input_buf_index += 1


def op_TST(vm, str_):
    vm.skip_space()

    input_ = vm.input()
    if input_.startswith(str_):
        vm.input_buf_index += len(str_)
        vm.switch = True
    else:
        vm.switch = False


def op_ID(vm):
    vm.skip_space()

    input_ = vm.input()
    if (match := re.match(r"^([A-Za-z]\w+)", input_)):
        vm.token_buf = match.group(1)
        vm.input_buf_index += len(vm.token_buf)
        vm.switch = True
    else:
        vm.switch = False


def op_NUM(vm):
    vm.skip_space()

    input_ = vm.input()
    if (match := re.match(r"^(\d+)", input_)):
        vm.token_buf = match.group(1)
        vm.input_buf_index += len(vm.token_buf)
        vm.switch = True
    else:
        vm.switch = False


def op_SR(vm):
    vm.skip_space()

    input_ = vm.input()
    if (match := re.match(r"^'[^']*'", input_)):
        vm.input_buf_index += len(match.group())
        vm.switch = True
    else:
        vm.switch = False
