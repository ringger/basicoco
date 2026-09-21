"""Bundled graphics programs draw what they say they draw, checked through
PPOINT (the server's pixel record, which matches the canvas: see the
browser test test_ppoint_matches_the_canvas)."""

import pytest


@pytest.fixture(autouse=True)
def _sandbox(temp_programs_dir):
    pass   # LOAD finds the bundled programs; nothing is written to the repo


def run_menu_choice(basic, helpers, program, choice):
    basic.process_command(f'LOAD "{program}"')
    result = basic.process_command('RUN')
    assert any(r.get('type') == 'input_request' for r in result)
    basic.store_input_value(basic.input_variables[0], str(choice))
    basic.clear_input_state()
    output = basic.continue_program_execution()
    while any(r.get('type') == 'pause' for r in output):   # graphics auto-yields
        output = basic.continue_program_execution()
    assert 'PLOT COMPLETE' in helpers.get_text_output(output)


def ppoint(basic, x, y):
    return basic.evaluate_expression(f'PPOINT({x},{y})')


def test_math_plotter_star_is_closed_and_filled(basic, helpers):
    """#104: the star used to start wherever the DRAW pen happened to be
    (PSET doesn't move it) and wasn't a closed star."""
    run_menu_choice(basic, helpers, 'math_plotter', 6)
    # Sample points avoid the axes (x=128, y=96), which are always drawn
    assert ppoint(basic, 118, 104) == 1     # the centre is filled
    assert ppoint(basic, 131, 55) == 1      # inside the top arm
    assert ppoint(basic, 152, 64) == 0      # the notch between two arms is empty
    assert ppoint(basic, 10, 10) == 0 and ppoint(basic, 245, 180) == 0   # paint stayed inside
