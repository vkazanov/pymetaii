#!/usr/bin/env python3
import re
import sys
from collections import namedtuple


LINE_RE = re.compile(r"^\s+([A-Za-z]\w*)\s*([A-Za-z]\w+|'[^']*')?$")


Inst = namedtuple("Inst", ["op", "arg", "labels"])


def parse_file(file_object):
    instructions = []
    labels = []
    for line in file_object:
        if not line:
            continue

        if line[0].isspace():
            match = LINE_RE.match(line)

            # Op itself
            op = match[1]

            # an argument can be a string literal
            arg = match[2]
            if arg and arg.startswith("'"):
                arg = arg[1:-1]

            instr = Inst(op=op, arg=arg, labels=labels)
            labels = []
            instructions.append(instr)
        else:
            labels.append(line.strip())

    return instructions


class VM:

    OPCODE_TO_HANDLER = {}

    def __init__(self, input_buf, output_file=sys.stdout):
        self.output_file = output_file

        self.reset(input_buf)

    def reset(self, input_buf):
        self.input_buf = input_buf
        self.input_buf_index = 0

        self.token_buf = None
        self.output_buf = []
        self.output_col = 8

        self.label_counter = 0
        self.label1_stack = [None]
        self.label2_stack = [None]
        self.call_stack = []
        self.pc = 0

        self.switch = False
        self.is_err = False
        self.is_done = False

        self.label_to_pc = {}

    def run(self, code, trace=False):
        # setup labels
        for i, instr in enumerate(code):
            for label in instr.labels:
                self.label_to_pc[label] = i

        while not self.is_err and not self.is_done:
            instr = code[self.pc]
            handler = self.OPCODE_TO_HANDLER[instr.op]
            if trace:
                input_buf = self.input_buf[self.input_buf_index:]
                print(instr,
                      ", input_buf='{}'".format(input_buf),
                      ", token_buf='{}'".format(self.token_buf),
                      ", call_stack='{}'".format(self.call_stack),
                      ", output_buf='{}'".format(self.output_buf),
                      file=sys.stderr)
            handler(self, instr.arg)

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
        buf = self.input_buf
        buf_len = len(self.input_buf)
        buf_index = self.input_buf_index
        while buf_index < buf_len and buf[buf_index].isspace():
            buf_index += 1
        self.input_buf_index = buf_index

    def dump_output(self):
        for _ in range(self.output_col):
            print(" ", file=self.output_file, end="")

        for s in self.output_buf:
            print(s, file=self.output_file, end="")

        print(file=self.output_file)

        self.output_buf = []
        self.output_col = 8


def op_TST(vm, str_):
    """After skipping initial whitespace in the input string compare it to the
    string given as argument. If the comparison is met, skip over the string in
    the input and set switch. If not met, reset switch.
    """
    vm.skip_space()

    input_ = vm.input()
    if input_.startswith(str_):
        vm.input_buf_index += len(str_)
        vm.switch = True
    else:
        vm.switch = False

    vm.pc += 1
VM.OPCODE_TO_HANDLER["TST"] = op_TST


def op_ID(vm, _):
    """After skipping initial whitespace in the input string, test if it begins
    with an identifier, i.e., a letter followed by a sequence of letters and/or
    digits. If so, copy the identifier to the token buffer; skip over it in the
    input; and set switch. If not, reset switch.
    """
    vm.skip_space()

    input_ = vm.input()
    if (match := re.match(r"^([A-Za-z]\w+)", input_)):
        vm.token_buf = match.group(1)
        vm.input_buf_index += len(vm.token_buf)
        vm.switch = True
    else:
        vm.switch = False

    vm.pc += 1
VM.OPCODE_TO_HANDLER["ID"] = op_ID


def op_NUM(vm, _):
    """After deleting initial whitespace in the input string, test if it begins
    with an number, i.e., a sequence of digits. If so, copy the number to the
    token buffer; skip over it in the input; and set switch. If not, reset
    switch.
    """
    vm.skip_space()

    input_ = vm.input()
    if (match := re.match(r"^(\d+)", input_)):
        vm.token_buf = match.group(1)
        vm.input_buf_index += len(vm.token_buf)
        vm.switch = True
    else:
        vm.switch = False

    vm.pc += 1
VM.OPCODE_TO_HANDLER["NUM"] = op_NUM


def op_SR(vm, _):
    """After deleting initial whitespace in the input string, test if it begins
    with an string, i.e., a single quote followed by a sequence of any
    characters other than a single quote followed by another single quote. If
    so, copy the string (including enclosing quotes) to the token buffer; skip
    over it in the input; and set switch. If not, reset switch.
    """
    vm.skip_space()

    input_ = vm.input()
    if (match := re.match(r"^'[^']*'", input_)):
        vm.input_buf_index += len(match.group())
        vm.switch = True
    else:
        vm.switch = False

    vm.pc += 1
VM.OPCODE_TO_HANDLER["SR"] = op_SR


def op_CLL(vm, label):
    """Enter the subroutine beginning at label AAA. Push a stackframe of three
    cells on the stack containing:

        1. label 1 cell, initialized to blank

        2. label 2 cell, initialized to blank

        3. location cell, set to the return from call location
    """
    vm.label1_push(None)
    vm.label2_push(None)
    vm.pc_set_push(vm.label_to_pc[label])
VM.OPCODE_TO_HANDLER["CLL"] = op_CLL


def op_R(vm, _):
    """Return from CLL call to location on the top of the stack and pop the
    stackframe of three cells.
    """
    if vm.call_stack:
        vm.label1_pop()
        vm.label2_pop()
        vm.pc_pop_set()

        vm.pc += 1
    else:
        vm.is_done = True
VM.OPCODE_TO_HANDLER["R"] = op_R


def op_SET(vm, _):
    """Set the switch to true.
    """
    vm.switch = True

    vm.pc += 1
VM.OPCODE_TO_HANDLER["SET"] = op_SET


def op_B(vm, label):
    """Branch unconditionally to the label AAA.
    """
    vm.pc = vm.label_to_pc[label]
VM.OPCODE_TO_HANDLER["B"] = op_B


def op_BT(vm, label):
    """If the switch is true, branch to label AAA.
    """
    if vm.switch:
        vm.pc = vm.label_to_pc[label]
    else:
        vm.pc += 1
VM.OPCODE_TO_HANDLER["BT"] = op_BT


def op_BF(vm, label):
    """If the switch is false, branch to label AAA.
    """
    if not vm.switch:
        vm.pc = vm.label_to_pc[label]
    else:
        vm.pc += 1
VM.OPCODE_TO_HANDLER["BF"] = op_BF


def op_BE(vm, _):
    """If the switch is false, report error status and halt.
    """
    if not vm.switch:
        vm.is_err = True
    else:
        vm.pc += 1
VM.OPCODE_TO_HANDLER["BE"] = op_BE


def op_CL(vm, str_):
    """Copy the variable length string (without enclosing quotes) given as
    argument to the output buffer.
    """
    vm.output_buf.append(str_)

    vm.pc += 1
VM.OPCODE_TO_HANDLER["CL"] = op_CL


def op_CI(vm, _):
    """Copy the token buffer to the output buffer.
    """
    vm.output_buf.append(vm.token_buf)

    vm.pc += 1
VM.OPCODE_TO_HANDLER["CI"] = op_CI


def op_GN1(vm, _):
    """If the label 1 cell in the top stackframe is blank, then generate a
    unique label and save it in the label 1 cell. In either case output the
    label.
    """
    label = vm.label1()
    if vm.label1() is None:
        label = vm.label_generate()
        vm.label1_set(label)
    vm.output_buf.append(label)

    vm.pc += 1
VM.OPCODE_TO_HANDLER["GN1"] = op_GN1


def op_GN2(vm, _):
    """Same as for GN1 except acting on the label 2 cell.
    """
    label = vm.label2()
    if vm.label2() is None:
        label = vm.label_generate()
        vm.label2_set(label)
    vm.output_buf.append(label)

    vm.pc += 1
VM.OPCODE_TO_HANDLER["GN2"] = op_GN2


def op_LB(vm, _):
    """Set the output buffer column to the first column.
    """
    vm.output_column = 0

    vm.pc += 1
VM.OPCODE_TO_HANDLER["LB"] = op_LB


def op_OUT(vm, _):
    """Output the output buffer with line terminator; clear it; and set the
    output buffer column to the eighth column.
    """
    vm.dump_output()
    vm.output_col = 8

    vm.pc += 1
VM.OPCODE_TO_HANDLER["OUT"] = op_OUT


def op_ADR(vm, start_label):
    """Pseudo operation that specifies the starting label to call.
    """
    vm.pc = vm.label_to_pc[start_label]
VM.OPCODE_TO_HANDLER["ADR"] = op_ADR


def op_END(vm, _):
    """Pseudo operation that specifies the end of input.
    """
    vm.is_done = True
VM.OPCODE_TO_HANDLER["END"] = op_END
