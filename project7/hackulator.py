import argparse
import sys
from typing import Literal, NamedTuple, Sequence
import dataclasses

# Commands:
#
# @vvv...            set A register
#
# dest=comp;jump     do stuff

def parse_instruction(instruction: str):
    """
    Determine the opcode and arguments for a hack instruction.

    Args:
        instruction: a trimmed string like "@101110010110100",
            "M=M-1", etc.
    Returns:
        (opcode, *args)
    """

    instruction = instruction.strip()
    parts = instruction.split("//")
    command = parts[0].strip()
    if not command:
        return None
    comment = parts[1].strip() if len(parts) > 1 else ""

    if command[0] == "(" and command[-1] == ")":
        # Label
        return ("L", command[1:-1], comment)

    elif command[0] == "@":
        # A-instruction
        addr = command[1:]

        try:
            addr = int(addr)
        except ValueError as exc:
            # it's a string, fine
            pass
        return ("A", addr, comment)

    else:
        # C-instruction

        parts = command.split("=")
        if len(parts) == 1:
            dest = None
            comp_jump = parts[0]
        else:
            assert len(parts) == 2
            dest, comp_jump = parts

        parts = comp_jump.split(";")
        if len(parts) == 1:
            comp = parts[0]
            jump = None
        else:
            assert len(parts) == 2
            comp, jump = parts

        return ("C", dest, comp, jump, comment)


def test_parse():
    assert parse_instruction("@44") == ("A", 44, "")
    assert parse_instruction(" @SP") == ("A", "SP", "")
    assert parse_instruction("M=M-1 //") == ("C", "M", "M-1", None, "")
    assert parse_instruction("D|A") == ("C", None, "D|A", None, "")
    assert parse_instruction("!D;JGE    // yes") == ("C", None, "!D", "JGE", "yes")
    assert parse_instruction("(LOOP)") == ("L", "LOOP", "")


def init_symbol_table() -> dict[str, int]:
    """
    Initialize a symbol table, with the registers R0, ... R15,
    and SP, LCL, ARG, THIS, THAT, SCREEN and KBD.
    """

    symbol_table: dict[str, int] = {}

    # Bound to numbers 0 through 15
    for ii in range(16):
        symbol_table[f"R{ii}"] = ii

    # Bound to numbers 0 through 4
    for (ii,sym) in enumerate(("SP", "LCL", "ARG", "THIS", "THAT")):
        symbol_table[sym] = ii

    # temp segment is 5 through 12, inclusive.

    # Memory-map
    symbol_table["SCREEN"] = 16384
    symbol_table["KBD"] = 24576

    return symbol_table


@dataclasses.dataclass
class Parser:
    symbol_table: dict[str, int] = dataclasses.field(default_factory=dict)
    parsed_instructions: list[tuple[str, ...]] = dataclasses.field(default_factory=list)

    def __post_init__(self):
        self.symbol_table = init_symbol_table()

        # import rich 
        # rich.print(self.symbol_table)

    def parse(self, lines: Sequence[str]):
        """
        Parse raw lines of assembly, add to symbol table, and store
        parsed instructions with all symbols resolved.
        """
        # First pass: add labels to symbol table

        insts = []

        for line in lines:
            parsed = parse_instruction(line)
            if parsed is None:
                continue

            opcode = parsed[0]

            cur_line_number = len(insts)

            if opcode == "L":
                # label
                self.symbol_table[parsed[1]] = cur_line_number
            else:
                insts.append(parsed)

        # Second pass: put other variables in symbol table and
        # replace them with ints in the instructions

        idx_next_symbol = 16

        self.parsed_instructions = []
        for instruction in insts:
            opcode = instruction[0]

            if opcode == "A":
                assert len(instruction) == 3
                addr, comment = instruction[1:]

                if isinstance(addr, str):
                    if addr in self.symbol_table:
                        addr = self.symbol_table[addr]
                    else:
                        self.symbol_table[addr] = idx_next_symbol
                        addr = idx_next_symbol
                        idx_next_symbol += 1

                    instruction = (opcode, addr, comment)

                self.parsed_instructions.append(instruction)

            else:
                assert opcode == "C"
                assert len(instruction) == 5
                self.parsed_instructions.append(instruction)

def parse(program: Sequence[str]) -> list[tuple[str,...]]:
    """
    Parse a Hack assembly program and return parsed instructions.
    """
    parser = Parser()
    parser.parse(program)
    return parser.parsed_instructions


def compute(comp: str, dd: int, aa: int, mm: int) -> int:
    if comp == "0":
        tmp = 0
    elif comp == "1":
        tmp = 1
    elif comp == "-1":
        tmp = 0xFFFF
    elif comp == "D":
        tmp = dd
    elif comp == "A":
        tmp = aa
    elif comp == "M":
        tmp = mm
    elif comp == "!D":
        tmp = (~dd)
    elif comp == "!A":
        tmp = (~aa)
    elif comp == "!M":
        tmp = (~mm)
    elif comp == "-D":
        tmp = (~dd + 1)
    elif comp == "-A":
        tmp = (~aa + 1)
    elif comp == "-M":
        tmp = (~mm + 1)
    elif comp == "D+1":
        tmp = (dd + 1)
    elif comp == "A+1":
        tmp = (aa + 1)
    elif comp == "M+1":
        tmp = (mm + 1)
    elif comp == "D-1":
        tmp = (dd + 0xFFFF) & 0xFFFF
    elif comp == "A-1":
        tmp = (aa + 0xFFFF)
    elif comp == "M-1":
        tmp = (mm + 0xFFFF)
    elif comp == "D+A":
        tmp = (aa + dd)
    elif comp == "D+M" or comp == "M+D":
        tmp = (dd + mm)
    elif comp == "D-A":
        tmp = (dd - aa)
    elif comp == "D-M":
        tmp = (dd - mm)
    elif comp == "A-D":
        tmp = (aa - dd)
    elif comp == "M-D":
        tmp = (mm - dd)
    elif comp == "D&A":
        tmp = (dd & aa)
    elif comp == "D&M":
        tmp = (dd & mm)
    elif comp == "D|A":
        tmp = (dd | aa)
    elif comp == "D|M":
        tmp = (dd | mm)
    else:
        raise ValueError(f"Unsupported command '{comp}'")

    tmp = tmp & 0xFFFF
    return tmp


class Compy386:

    def __init__(self, program: str = ""): #, init_sp: bool = True):
        self.register_d: int = 0
        self.register_a: int = 0
        self.ram: list[int] = [0]*(2**15)
        self.pc: int = 0

        # if init_sp:
            # program = self.init_memory_segments_mapping() + "\n" + program

        parser = Parser()
        parser.parse(program.splitlines())
        self.parsed_instructions: list[tuple[str,...]] = parser.parsed_instructions
        self.symbol_table = parser.symbol_table

        self.stack_ptr: int = 256 # address of bottom of stack
        self.sp = self.stack_ptr

    @classmethod
    def init_memory_segments_mapping(cls) -> str:
        """
        Program to set stack pointer to 256.

        Other memory segments are set by function calls and such.
        """

        program = """
        // Set SP to 256
        @256
        D=A
        @SP
        M=D
        """

        return program

    def run(self, max_steps: int = 1000, print_line: bool = False, print_registers: bool = False, print_stack: bool = False):
        """
        Call step() until the pc is past the length of the program.
        """

        for s in range(max_steps):
            if self.pc >= len(self.parsed_instructions):
                break
            self.step(print_line, print_registers, print_stack)

    def step(self, print_line: bool = False, print_registers: bool = False, print_stack: bool = False):
        """
        Execute one hack instruction and update the program counter.
        """
        inst = self.parsed_instructions[self.pc]

        if print_line:
            print(f"{self.pc}: {inst}")

        self.pc += 1

        if (opcode := inst[0]) == "A":
            addr = inst[1]
            assert isinstance(addr, int)
            self.register_a = addr
        else:
            assert opcode == "C"
            dest, comp, jump, comment = inst[1:]

            if 0 <= self.register_a < len(self.ram):
                register_m = self.ram[self.register_a]
            else:
                register_m = 0
                assert "M" not in comp
            result = compute(comp, self.register_d, self.register_a, register_m)
            if dest is None:
                pass
            else:
                # careful: must write M before A
                if "M" in dest:
                    self.ram[self.register_a] = result
                if "A" in dest:
                    self.register_a = result
                if "D" in dest:
                    self.register_d = result

            signed_result = result if result < 0x8000 else result - 0x10000

            if ((jump == "JGT" and signed_result > 0) or
                (jump == "JEQ" and signed_result == 0) or
                (jump == "JGE" and signed_result >= 0) or
                (jump == "JLT" and signed_result < 0) or
                (jump == "JNE" and signed_result != 0) or
                (jump == "JLE" and signed_result <= 0) or
                (jump == "JMP")):
                self.pc = self.register_a

        if print_registers:
            print("  a:", self.register_a)
            print("  m:", self.ram[self.register_a] if 0 <= self.register_a < len(self.ram) else None)
            print("  d:", self.register_d)
        if print_stack:
            print("  ", self.get_stack())

    def set_segment_base(self, segment: Literal["LCL", "ARG", "THIS", "THAT"], base_addr: int):
        assert segment in ("LCL", "ARG", "THIS", "THAT")
        self.ram[self.symbol_table[segment]] = base_addr

    def get_stack(self) -> list[int]:
        return self.ram[self.stack_ptr:self.ram[self.symbol_table["SP"]]]

    def segment_base(self, segment: Literal["LCL", "ARG", "THIS", "THAT", "TEMP"]) -> int:
        """
        Get the base address for a given memory segment.

        Args:
            segment: LCL, ARG, THIS, THAT or TEMP

        Base addresses reside at fixed offsets in the RAM:
            0: SP
            1: LCL
            2: ARG
            3: THIS
            4: THAT

        and the TEMP segment is always words 5-12 (the offset cannot be changed).
        """
        assert segment in ("LCL", "ARG", "THIS", "THAT", "TEMP")
        if segment == "TEMP":
            idx = self.symbol_table["TEMP"]
        else:
            idx = self.ram[self.symbol_table[segment]]

        assert 0 <= idx < len(self.ram)

        return idx


    def get_in_segment(self, segment: Literal["LCL", "ARG", "THIS", "THAT", "TEMP"], addr: int) -> int:
        assert segment in ("LCL", "ARG", "THIS", "THAT", "TEMP")
        return self.ram[self.segment_base(segment) + addr]

    def set_in_segment(self, segment: Literal["LCL", "ARG", "THIS", "THAT", "TEMP"], addr: int, value: int):
        assert segment in ("LCL", "ARG", "THIS", "THAT", "TEMP")
        self.ram[self.segment_base(segment) + addr] = value


    @property
    def sp(self) -> int:
        """
        Get the stack pointer. It should be 256 when the stack is empty.
        """
        return self.ram[self.symbol_table["SP"]]

    @sp.setter
    def sp(self, value: int):
        """
        Set the stack pointer. It should be 256 when the stack is empty.
        """
        self.ram[self.symbol_table["SP"]] = value

    def push(self, value: int):
        self.ram[self.sp] = value
        self.sp += 1

    def pop(self) -> int:
        self.sp -= 1
        return self.ram[self.sp]

    def peek(self, depth: int = 0) -> int:
        """
        Look at the item on the top of the stack (at SP - 1).

        Args:
            depth: [OPTIONAL] number of entries below top of stack
        Return:
            value on top of stack (at SP - 1)
        """
        loc = self.sp - 1 - depth
        if loc < self.stack_ptr:
            raise ValueError(f"Underflow: cannot peek at stack[{loc - self.stack_ptr}]")
        return self.ram[loc]

    def depth(self) -> int:
        """Return number of items on stack"""
        return self.sp - self.stack_ptr


if __name__ == "__main__":
    p = argparse.ArgumentParser("hackulator", description="Hack program emulator")
    p.add_argument("file", action="store", help="Path to file with hack source code")
    args = p.parse_args()

    with open(args.file) as fh:
        lines = fh.readlines()

    # parser = Parser()
    # parser.parse(lines)

    # Execute the program

    compy = Compy386("\n".join(lines))

    for step in range(100):
        print(step, compy.pc, ":", compy.parsed_instructions[compy.pc])
        compy.step()
        print("a:", compy.register_a)
        print("d:", compy.register_d)
        print("pc:", compy.pc)
        print("m:", compy.ram[compy.register_a])

    print("DONE")
    print(compy.ram[:30])





#
