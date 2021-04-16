#!/usr/bin/env python3
import re
import sys


class VM:

    def __init__(self, input_buf, output_file=sys.stdout):
        self.output_file = output_file

        self.input_buf_index = 0
        self.input_buf = input_buf

        self.token_buf = None
        self.output_buf = []
        self.output_col = 0

        self.label_counter = 0
        self.label1_stack = [None]
        self.label2_stack = [None]
        self.call_stack = []
        self.pc = 0

        self.switch = False
        self.is_err = False

        self.label_to_pc = {}

    def label_generate(self):
        label = "L{}".format(self.label_counter)
        self.label_counter += 1
        return label

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

    def dump_output(self):
        for _ in range(self.output_col):
            print(" ", file=self.output_file)

        for s in self.output_buf:
            print(s, file=self.output_file)

        self.output_buf = []
        self.output_col = 8


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


def op_CL(vm, str_):
    vm.output_buf.append(str_)


def op_CI(vm):
    vm.output_buf.append(vm.token_buf)


def op_GN1(vm):
    label = vm.label1()
    if vm.label1() is None:
        label = vm.label_generate()
        vm.label1_set(label)
    vm.output_buf.append(label)


def op_GN2(vm):
    label = vm.label2()
    if vm.label2() is None:
        label = vm.label_generate()
        vm.label2_set(label)
    vm.output_buf.append(label)


def op_LB(vm):
    vm.output_column = 0


def op_OUT(vm):
    vm.dump_output()
    vm.output_column == 8


def op_ADR(vm, start_label):
    vm.pc = vm.label_to_pc[start_label]


def op_END(vm):
    pass
