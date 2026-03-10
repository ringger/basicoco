#!/usr/bin/env python3
"""Empirically determine corner insertion algorithms for BFR slot."""
import sys
sys.path.insert(0, '.')
from emulator.core import CoCoBasic

def make_emulator():
    basic = CoCoBasic()
    basic.process_command('NEW')
    basic.process_command('5 SAFETY OFF')
    basic.process_command('10 PMODE 4: SCREEN 1')
    basic.process_command('20 MERGE "rubiks_engine"')
    basic.process_command('30 GOSUB InitCube')
    basic.process_command('40 END')
    basic.process_command('RUN')
    # Wait for completion
    while basic.waiting_for_pause_continuation:
        basic.waiting_for_pause_continuation = False
        basic.running = True
        basic.continue_program_execution()
    return basic

def get_cl(basic, ix, iy, iz, f):
    """Read CL(ix,iy,iz,f) from emulator."""
    arr = basic.arrays.get('CL')
    if arr is None:
        return None
    return arr[ix][iy][iz][f]

def do_moves(basic, moves_str):
    """Apply moves to cube."""
    # Set MS$ and call DoMoves
    basic.variables['MS$'] = moves_str
    # We need to GOSUB DoMoves - use immediate mode won't work
    # Instead, load a mini program
    basic.process_command('NEW')
    basic.process_command('5 SAFETY OFF')
    basic.process_command('10 PMODE 4: SCREEN 1')
    basic.process_command('20 MERGE "rubiks_engine"')
    basic.process_command('30 GOSUB InitCube')
    basic.process_command(f'40 MS$="{moves_str}": GOSUB DoMoves')
    basic.process_command('50 END')
    result = basic.process_command('RUN')
    while basic.waiting_for_pause_continuation:
        basic.waiting_for_pause_continuation = False
        basic.running = True
        basic.continue_program_execution()
    return basic

def init_and_apply(moves_str):
    """Initialize solved cube, apply moves, return emulator."""
    basic = CoCoBasic()
    basic.process_command('NEW')
    basic.process_command('5 SAFETY OFF')
    basic.process_command('10 PMODE 4: SCREEN 1')
    basic.process_command('20 MERGE "rubiks_engine"')
    basic.process_command('25 AN=0')
    basic.process_command('30 GOSUB InitCube')
    if moves_str:
        basic.process_command(f'40 MS$="{moves_str}": GOSUB DoMoves')
    basic.process_command('50 END')
    result = basic.process_command('RUN')
    while basic.waiting_for_pause_continuation:
        basic.waiting_for_pause_continuation = False
        basic.running = True
        basic.continue_program_execution()
    return basic

def find_corner(basic, tc1, tc2, tc3):
    """Find corner with given colors. Returns (cp, co)."""
    # Corner positions and their sticker faces
    corners = [
        # (ix,iy,iz, face_a, face_b, face_c) - face_a=Y, face_b=Z, face_c=X
        (2,2,0, 5,0,2),  # CP=0 BFR: F5(bottom), F0(front), F2(right)
        (0,2,0, 5,0,3),  # CP=1 BFL: F5(bottom), F0(front), F3(left)
        (2,2,2, 5,1,2),  # CP=2 BBR: F5(bottom), F1(back), F2(right)
        (0,2,2, 5,1,3),  # CP=3 BBL: F5(bottom), F1(back), F3(left)
        (2,0,0, 4,0,2),  # CP=4 TFR: F4(top), F0(front), F2(right)
        (0,0,0, 4,0,3),  # CP=5 TFL: F4(top), F0(front), F3(left)
        (2,0,2, 4,1,2),  # CP=6 TBR: F4(top), F1(back), F2(right)
        (0,0,2, 4,1,3),  # CP=7 TBL: F4(top), F1(back), F3(left)
    ]
    for cp, (ix,iy,iz,fa,fb,fc) in enumerate(corners):
        ca = get_cl(basic, ix,iy,iz,fa)
        cb = get_cl(basic, ix,iy,iz,fb)
        cc = get_cl(basic, ix,iy,iz,fc)
        colors = {ca, cb, cc}
        if colors == {tc1, tc2, tc3}:
            if ca == tc1: co = 0  # TC1 on Y-face
            elif cb == tc1: co = 1  # TC1 on Z-face
            else: co = 2  # TC1 on X-face
            return cp, co
    return -1, -1

def bfr_solved(basic):
    """Check if BFR corner is solved (magenta bottom, red front, blue right)."""
    return (get_cl(basic, 2,2,0,5) == 7 and
            get_cl(basic, 2,2,0,0) == 4 and
            get_cl(basic, 2,2,0,2) == 3)

# TC1=7 (magenta/bottom), TC2=4 (red/front), TC3=3 (blue/right)
TC1, TC2, TC3 = 7, 4, 3

print("=== EXTRACTION TESTS ===")
print("Starting from solved BFR, apply moves, find where corner goes")
print()

extractions = ['ruR', 'FUf', 'fuF', 'rUR', 'Rur', 'RUr', 'Fuf', 'fUF']
for ext in extractions:
    basic = init_and_apply(ext)
    cp, co = find_corner(basic, TC1, TC2, TC3)
    solved = bfr_solved(basic)
    label = f"{ext:6s}"
    print(f"  {label}: CP={cp} CO={co}  BFR_solved={solved}")
    if cp >= 4:
        ix,iy,iz = [(2,0,0),(0,0,0),(2,0,2),(0,0,2)][cp-4]
        f4 = get_cl(basic, ix,iy,iz,4)
        fz = get_cl(basic, ix,iy,iz, 0 if iz==0 else 1)
        fx = get_cl(basic, ix,iy,iz, 2 if ix==2 else 3)
        print(f"         stickers: top={f4} {'front' if iz==0 else 'back'}={fz} {'right' if ix==2 else 'left'}={fx}")

print()
print("=== EXTRACTION + ALIGN TO TFR + INSERTION TESTS ===")
print("For each extraction that puts corner in top layer,")
print("align to TFR, then try every 3-move insert.")
print()

# U-align: cycle is TFR(4) -> TBR(6) -> TBL(7) -> TFL(5) -> TFR(4)
# Actually U CW: TFR->TBR (based on plan), let me figure it out
# From AlignTop in solver: U CW cycle: 4(front)->7(left)->6(back)->5(right)->4
# So to get from CP=X to CP=4:
def align_moves(cp):
    """Return U moves to get from cp to TFR (cp=4)."""
    if cp == 4: return ''
    if cp == 5: return 'u'    # 5->4 needs U' (one CCW)
    if cp == 6: return 'UU'   # 6->4 needs U2
    if cp == 7: return 'U'    # 7->4 needs U (one CW)
    return None  # bottom corner

inserts_to_try = ['RUr', 'Rur', 'ruR', 'rUR', 'fuF', 'fUF', 'FUf', 'Fuf',
                  'RUUr', 'RuuruRUr', 'RUUruRUr', 'ruRURur', 'fuFUFuf']

# Test each extraction that moves corner to top
good_extractions = []
for ext in extractions:
    basic = init_and_apply(ext)
    cp, co = find_corner(basic, TC1, TC2, TC3)
    if cp >= 4 and not bfr_solved(basic):
        good_extractions.append((ext, cp, co))

# For each unique CO found, test insertions
cos_found = {}
for ext, cp, co in good_extractions:
    if co not in cos_found:
        cos_found[co] = (ext, cp)

print(f"Unique orientations found: {sorted(cos_found.keys())}")
for co_val in sorted(cos_found.keys()):
    ext, orig_cp = cos_found[co_val]
    print(f"\n--- CO={co_val} (from extraction '{ext}', lands at CP={orig_cp}) ---")

    for ins in inserts_to_try:
        # Reconstruct: init, extract, align, insert
        full_moves = ext + align_moves(orig_cp) + ins
        basic = init_and_apply(full_moves)
        cp, co = find_corner(basic, TC1, TC2, TC3)
        solved = bfr_solved(basic)
        marker = " <<<< SOLVED!" if solved else ""
        print(f"  {ins:15s}: CP={cp} CO={co}{marker}")

print()
print("=== DONE ===")
