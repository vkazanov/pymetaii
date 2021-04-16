#!/usr/bin/env python3
import re


class VM:

    def __init__(self, input_buf):
        self.input_buf_index = 0
        self.input_buf = input_buf

        self.token_buf = None

        self.label1_stack = [None]
        self.label2_stack = [None]
        self.call_stack = []
        self.pc = 0

        self.switch = False
        self.is_err = False

        self.label_to_pc = {}

    def label1(self):
        return self.label1_stack[-1]

    def label1_push(self, label):
        self.label1_stack.append(label)

    def label1_pop(self):
        return self.label1_stack.pop()

    def label1_set(self, label):
        self.label1_stack[-1] = label

    def label2(self):
        return self.label2_stack[-1]

    def label2_push(self, label):
        self.label2_stack.append(label)

    def label2_pop(self):
        return self.label2_stack.pop()

    def label2_set(self, label):
        self.label2_stack[-1] = label

    def pc_set_push(self, new_pc):
        self.call_stack.append(self.pc)
        self.pc = new_pc

    def pc_pop_set(self):
        self.pc = self.call_stack.pop()

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

    # TODO: single quote quoting: ('this is a string ''with'' a quote')
    input_ = vm.input()
    if (match := re.match(r"^'[^']*'", input_)):
        vm.input_buf_index += len(match.group())
        vm.switch = True
    else:
        vm.switch = False


def op_CLL(vm, label):
    vm.label1_push(None)
    vm.label2_push(None)
    vm.pc_set_push(vm.label_to_pc[label])


def op_R(vm):
    vm.label1_pop()
    vm.label2_pop()
    vm.pc_pop_set()


def op_SET(vm):
    vm.switch = True


def op_B(vm, label):
    vm.pc = vm.label_to_pc[label]


def op_BT(vm, label):
    if vm.switch:
        vm.pc = vm.label_to_pc[label]


def op_BF(vm, label):
    if not vm.switch:
        vm.pc = vm.label_to_pc[label]


def op_BE(vm):
    if not vm.switch:
        vm.is_err = True
