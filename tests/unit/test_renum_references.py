"""RENUM line-reference rewriting (task #74): only real jump targets change;
strings and comments are left alone; crunched targets are handled."""

import pytest

from emulator.core import CoCoBasic

MAPPING = {10: 100, 20: 110, 30: 120}


@pytest.mark.parametrize('code,expected', [
    ('GOTO 10', 'GOTO 100'),
    ('GOSUB 20', 'GOSUB 110'),
    ('ON X GOSUB 10,20, 30', 'ON X GOSUB 100,110, 120'),
    ('IF A THEN 20 ELSE 30', 'IF A THEN 110 ELSE 120'),
    ('RESTORE 20: GOTO 40', 'RESTORE 110: GOTO 40'),
    ('RESUME 30', 'RESUME 120'),
    ('GOTO10', 'GOTO100'),
    ('IFX=1THEN20', 'IFX=1THEN110'),
    ('PRINT "GOTO 10"', 'PRINT "GOTO 10"'),
    ('PRINT "ON Y GOSUB 20,30"', 'PRINT "ON Y GOSUB 20,30"'),
    ('REM SEE GOSUB 20', 'REM SEE GOSUB 20'),
    ('A=1: REM GOTO 10', 'A=1: REM GOTO 10'),
    ("PRINT 1 ' GOTO 10", "PRINT 1 ' GOTO 10"),
    ('XGOTO 10', 'XGOTO 10'),
    ('THEN 10,20', 'THEN 100,20'),
])
def test_update_line_references(code, expected):
    assert CoCoBasic._update_line_references(code, MAPPING) == expected


def test_renum_end_to_end_leaves_strings_alone(basic, helpers):
    basic.process_command('NEW')
    basic.process_command('10 PRINT "GOTO 10"')
    basic.process_command('20 GOTO 30')
    basic.process_command('30 END')
    basic.process_command('RENUM 100,10')
    assert basic.program == {100: 'PRINT "GOTO 10"', 110: 'GOTO 120', 120: 'END'}
