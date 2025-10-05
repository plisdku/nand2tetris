import argparse
import sys
from typing import NamedTuple, Sequence
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
    if instruction[0] == "(" and instruction[-1] == ")":
        # Label
        return ("L", instruction[1:-1])

    elif instruction[0] == "@":
        # A-instruction
        addr = instruction[1:]

        try:
            addr = int(addr)
        except ValueError as exc:
            # it's a string, fine
            pass
        return ("A", addr)

    else:
        # C-instruction

        parts = instruction.split("=")
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

        return ("C", dest, comp, jump)


def test_parse():
    assert parse_instruction("@44") == ("A", 44)
    assert parse_instruction("@SP") == ("A", "SP")
    assert parse_instruction("M=M-1") == ("C", "M", "M-1", None)
    assert parse_instruction("D|A") == ("C", None, "D|A", None)
    assert parse_instruction("!D;JGE") == ("C", None, "!D", "JGE")
    assert parse_instruction("(LOOP)") == ("L", "LOOP")


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
            parts = line.strip().split("//")
            command = parts[0].strip()
            if not command:
                continue
            parsed = parse_instruction(command)
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
                assert len(instruction) == 2
                addr = instruction[1]

                if isinstance(addr, str):
                    if addr in self.symbol_table:
                        addr = self.symbol_table[addr]
                    else:
                        self.symbol_table[addr] = idx_next_symbol
                        addr = idx_next_symbol
                        idx_next_symbol += 1

                    instruction = (opcode, addr)

                self.parsed_instructions.append(instruction)

            else:
                assert opcode == "C"
                assert len(instruction) == 4
                dest, comp, jump = instruction[1:]
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

        print("D =", dd)
        print("D-1 =", tmp)
        assert (tmp & 0xFFFF) == (dd - 1) & 0xFFFF
    elif comp == "A-1":
        tmp = (aa + 0xFFFF)
    elif comp == "M-1":
        tmp = (mm + 0xFFFF)
    elif comp == "D+A":
        tmp = (aa + dd)
    elif comp == "D+M":
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
        raise ValueError(f"Confusing command '{comp}'")

    tmp = tmp & 0xFFFF
    return tmp


class Compy386:

    def __init__(self, program: str):
        self.register_d: int = 0
        self.register_a: int = 0
        self.ram: list[int] = [0]*(2**15)
        self.pc: int = 0
        self.parsed_instructions: list[tuple[str,...]] = parse(program.splitlines())

    def step(self):
        """
        Carry out 
        """
        inst = self.parsed_instructions[self.pc]
        self.pc += 1

        if (opcode := inst[0]) == "A":
            addr = inst[1]
            assert isinstance(addr, int)
            self.register_a = addr
        else:
            assert opcode == "C"
            dest, comp, jump = inst[1:]

            result = compute(comp, self.register_d, self.register_a, self.ram[self.register_a])
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
