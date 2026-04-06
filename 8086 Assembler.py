import json
import tkinter as tk
from tkinter import scrolledtext, font

# ---------------- LOAD OPCODES ----------------
with open("instruction.json") as f:
    OPCODES = json.load(f)

# ---------------- CPU STATE ----------------
registers = {r: 0 for r in
    ["AX","BX","CX","DX","AH","AL","BH","BL","CH","CL","DH","DL"]}

FLAGS = {
    "CF": 0,
    "ZF": 0,
    "SF": 0,
    "OF": 0,
    "PF": 0,
    "AF": 0
}

PC = 0
program = []

# ---------------- HELPERS ----------------
def parse_value(val):
    val = val.upper()
    if val.endswith("H"):
        return int(val[:-1], 16)
    return int(val)

def to_hex(val, width=4):
    return f"{val & 0xFFFF:0{width}X}H"

def parity(val):
    return bin(val & 0xFF).count("1") % 2 == 0

def update_flags(result, op1=None, op2=None, operation=None):
    result16 = result & 0xFFFF

    FLAGS["ZF"] = int(result16 == 0)
    FLAGS["SF"] = int((result16 & 0x8000) != 0)
    FLAGS["PF"] = int(parity(result16))

    if operation == "ADD":
        FLAGS["CF"] = int(result > 0xFFFF)
        FLAGS["OF"] = int(((op1 ^ result) & (op2 ^ result) & 0x8000) != 0)
        FLAGS["AF"] = int(((op1 & 0xF) + (op2 & 0xF)) > 0xF)

    elif operation == "SUB":
        FLAGS["CF"] = int(op1 < op2)
        FLAGS["OF"] = int(((op1 ^ op2) & (op1 ^ result) & 0x8000) != 0)
        FLAGS["AF"] = int(((op1 & 0xF) - (op2 & 0xF)) < 0)

def log(text, tag=None):
    output.config(state=tk.NORMAL)
    output.insert(tk.END, text + "\n", tag)
    output.config(state=tk.DISABLED)
    output.see(tk.END)

# ---------------- RESET FUNCTION ----------------
def reset_cpu():
    global PC
    
    # Reset registers
    for r in registers:
        registers[r] = 0

    # Reset flags
    for f in FLAGS:
        FLAGS[f] = 0

    # Reset program counter
    PC = 0

    # Clear output window
    output.config(state=tk.NORMAL)
    output.delete(1.0, tk.END)
    output.config(state=tk.DISABLED)

    log("🔄 CPU RESET SUCCESSFULLY", "success")

    refresh_panels()

# ---------------- EXECUTION ----------------
def execute(step=True):
    global PC

    if PC >= len(program):
        log("✔ PROGRAM COMPLETED", "success")
        return

    instr = program[PC]
    parts = instr.replace(",", " ").split()
    opcode = parts[0]
    ops = parts[1:]

    log(f"▶ [{PC:02}] {instr}", "opcode")

    try:
        if opcode == "MOV":
            dest, src = ops
            registers[dest] = parse_value(src) if src not in registers else registers[src]

        elif opcode == "ADD":
            op1 = registers[ops[0]]
            op2 = registers[ops[1]]
            result = op1 + op2
            registers[ops[0]] = result & 0xFFFF
            update_flags(result, op1, op2, "ADD")

        elif opcode == "SUB":
            op1 = registers[ops[0]]
            op2 = registers[ops[1]]
            result = op1 - op2
            registers[ops[0]] = result & 0xFFFF
            update_flags(result, op1, op2, "SUB")

        elif opcode == "INC":
            op1 = registers[ops[0]]
            result = op1 + 1
            registers[ops[0]] = result & 0xFFFF
            update_flags(result, op1, 1, "ADD")

        elif opcode == "DEC":
            op1 = registers[ops[0]]
            result = op1 - 1
            registers[ops[0]] = result & 0xFFFF
            update_flags(result, op1, 1, "SUB")

        elif opcode == "CMP":
            op1 = registers[ops[0]]
            op2 = registers[ops[1]]
            result = op1 - op2
            update_flags(result, op1, op2, "SUB")

        PC += 1
        refresh_panels()

        if not step:
            root.after(400, lambda: execute(False))

    except Exception as e:
        log(f"❌ ERROR : {e}", "error")

# ---------------- UI ----------------
def load_program():
    global program, PC
    program = code_editor.get("1.0", tk.END).strip().upper().splitlines()
    PC = 0
    output.config(state=tk.NORMAL)
    output.delete(1.0, tk.END)
    output.config(state=tk.DISABLED)
    log("✔ PROGRAM LOADED SUCCESSFULLY", "success")
    refresh_panels()

def refresh_panels():
    reg_list.delete(0, tk.END)
    flag_list.delete(0, tk.END)

    for r in ["AX", "BX", "CX", "DX"]:
        reg_list.insert(tk.END, f"{r} = {to_hex(registers[r])}")

    for f in FLAGS:
        flag_list.insert(tk.END, f"{f} = {FLAGS[f]}")

# ---------------- GUI ----------------
root = tk.Tk()
root.title("MIC Instruction Debugger")
root.geometry("1200x720")
root.configure(bg="#1e1e1e")

FONT_MAIN = font.Font(family="Consolas", size=13)
FONT_HEAD = font.Font(family="Consolas", size=14, weight="bold")

left = tk.Frame(root, bg="#1e1e1e")
left.pack(side=tk.LEFT, fill=tk.Y, padx=12)

tk.Label(left, text="Program Code",
         fg="#dcdcaa", bg="#1e1e1e", font=FONT_HEAD).pack(anchor="w")

code_editor = scrolledtext.ScrolledText(
    left, width=40, height=32,
    bg="#252526", fg="#9cdcfe",
    insertbackground="white",
    font=FONT_MAIN
)
code_editor.pack(pady=6)

tk.Button(left, text="Load Program", command=load_program,
          bg="#0e639c", fg="white").pack(fill=tk.X, pady=4)

tk.Button(left, text="Step ▶", command=lambda: execute(True),
          bg="#3c3c3c", fg="white").pack(fill=tk.X)

tk.Button(left, text="Run ▶▶", command=lambda: execute(False),
          bg="#3c3c3c", fg="white").pack(fill=tk.X, pady=4)

# 🔥 RESET BUTTON ADDED HERE
tk.Button(left, text="Reset ⟳", command=reset_cpu,
          bg="#aa3333", fg="white").pack(fill=tk.X, pady=4)

center = tk.Frame(root, bg="#1e1e1e")
center.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

output = scrolledtext.ScrolledText(
    center, bg="#1e1e1e", fg="#d4d4d4",
    font=FONT_MAIN, state=tk.DISABLED
)
output.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

right = tk.Frame(root, bg="#1e1e1e")
right.pack(side=tk.RIGHT, fill=tk.Y, padx=12)

tk.Label(right, text="Registers",
         fg="#4ec9b0", bg="#1e1e1e", font=FONT_HEAD).pack(anchor="w")

reg_list = tk.Listbox(right, width=20, height=8,
                      bg="#252526", fg="#4ec9b0",
                      font=FONT_MAIN)
reg_list.pack(pady=5)

tk.Label(right, text="Flags",
         fg="#c586c0", bg="#1e1e1e", font=FONT_HEAD).pack(anchor="w")

flag_list = tk.Listbox(right, width=20, height=8,
                       bg="#252526", fg="#c586c0",
                       font=FONT_MAIN)
flag_list.pack()

output.tag_config("opcode", foreground="#569cd6")
output.tag_config("success", foreground="#6a9955")
output.tag_config("error", foreground="#f44747")

root.mainloop()