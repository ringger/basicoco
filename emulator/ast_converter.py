"""
Single-line control-structure expansion for the TRS-80 Color Computer BASIC
emulator.

A stored or immediate line such as

    IF A=1 THEN PRINT "ONE": B=2 ELSE PRINT "OTHER"

is expanded into sublines the executor runs like a multi-line block:

    IF A=1 THEN / PRINT "ONE" / B=2 / ELSE / PRINT "OTHER" / ENDIF

The expansion works on the SOURCE TEXT: statements are split on colons and
kept verbatim, so expressions are never regenerated (an earlier AST-to-text
round trip dropped parentheses, e.g. 10-(5-2) became 10 - 5 - 2).

Semantics follow Color BASIC:

- Everything after THEN (or ELSE) to the end of the line belongs to that
  branch, including later colon-separated statements and a later NEXT.
- ELSE binds to the nearest unmatched IF.
- THEN may be crunched against the condition (IF A$="X"THEN ..., IF A=0THEN).
- ``IF cond GOTO n`` and ``THEN n`` / ``ELSE n`` (implicit GOTO) are accepted.
- REM ends the line; colons after it are part of the comment.

FOR/WHILE/DO lines need no special handling: the executor runs a FOR on
subline 0 and its NEXT on subline 3 of the same line just as it would across
lines, so those are simply split on colons.
"""

import re
from typing import List, Optional

from .text_utils import StatementSplitter

_CONTROL_PREFIXES = ('IF', 'FOR', 'WHILE', 'DO')


def _scan_keywords(text: str, keywords):
    """Yield (index, KEYWORD) for each keyword occurrence outside quotes.

    A keyword must not directly follow a letter, so crunched forms such as
    ``"X"THEN`` or ``0THEN`` are found, while ``LENGTHEN`` is not. Scanning
    stops at a comment: a REM that starts a statement, or a ' anywhere.
    """
    upper = text.upper()
    in_quotes = False
    at_statement_start = True
    i = 0
    while i < len(text):
        char = text[i]
        if char == '"':
            in_quotes = not in_quotes
            at_statement_start = False
        elif not in_quotes:
            if char == "'":
                return
            if char == ':':
                at_statement_start = True
            elif not char.isspace():
                if at_statement_start and upper.startswith('REM', i):
                    return  # REM by prefix, as on the CoCo (REMARK)
                at_statement_start = False
                if i == 0 or not upper[i - 1].isalpha():
                    for keyword in keywords:
                        if upper.startswith(keyword, i):
                            yield i, keyword
                            i += len(keyword) - 1
                            break
        i += 1


def find_keyword(text: str, keyword: str) -> int:
    """Index of the first *keyword* outside quotes and comments, or -1."""
    return next((i for i, _ in _scan_keywords(text, (keyword,))), -1)


def _own_else_index(text: str) -> int:
    """Index of the ELSE belonging to this IF's THEN-part, or -1.

    That is the first ELSE not claimed by an inner IF (ELSE binds to the
    nearest unmatched IF). Quote- and REM-aware.
    """
    pending_inner_ifs = 0
    for index, keyword in _scan_keywords(text, ('IF', 'ELSE')):
        if keyword == 'IF':
            pending_inner_ifs += 1
        elif pending_inner_ifs:
            pending_inner_ifs -= 1
        else:
            return index
    return -1


def _split_else(text: str):
    """Split an IF's THEN-part into (then_text, else_text or None)."""
    index = _own_else_index(text)
    if index < 0:
        return text, None
    return text[:index].rstrip().rstrip(':').rstrip(), text[index + 4:].strip()


def _find_else_outside_quotes(text: str) -> int:
    """Position just before the ELSE belonging to this clause, or -1."""
    index = _own_else_index(text)
    return index - 1 if index > 0 and text[index - 1] == ' ' else index


def _starts_with_keyword(statement: str, keyword: str) -> bool:
    """True if *statement* begins with *keyword* as a whole word
    (so an assignment like IFLAG=1 is not an IF)."""
    upper = statement.upper()
    return upper.startswith(keyword) and (
        len(upper) == len(keyword) or not upper[len(keyword)].isalnum())


def _is_jump_target(text: str, commands) -> bool:
    """True if a branch is an implicit GOTO target rather than a statement:
    a line number, a label, or a line-number expression (THEN A*B).

    A statement starts with a command/keyword word, or assigns (top-level
    '='), or has top-level commas (SOUND F, 1).
    """
    if text.isdigit():
        return True
    if StatementSplitter.is_rem_line(text):
        return False
    first_word = re.match(r'[A-Za-z_]+\$?', text)
    if first_word and first_word.group(0).upper() in commands:
        return False
    depth, in_quotes = 0, False
    for char in text:
        if char == '"':
            in_quotes = not in_quotes
        elif in_quotes:
            continue
        elif char == '(':
            depth += 1
        elif char == ')':
            depth -= 1
        elif depth == 0 and char in '=,;':
            return False
    return not in_quotes and '"' not in text


def _branch_statements(text: str, commands) -> List[str]:
    """Sublines for one IF branch (the text after THEN or ELSE)."""
    text = text.strip()
    if not text:
        return []
    parts = StatementSplitter.split_on_delimiter(text)
    if len(parts) == 1 and _is_jump_target(parts[0].strip(), commands):
        return [f'GOTO {parts[0].strip()}']  # THEN 100 / THEN A*B / ELSE Fin
    return expand_statements(text, commands)


def _expand_if(statement: str, commands=frozenset()) -> Optional[List[str]]:
    """Expand a one-line IF into block sublines.

    A block IF (``IF cond THEN`` with nothing but perhaps a comment after
    it) is returned normalised as the single subline ``IF cond THEN``, which
    the executor runs as a multi-line IF; ``IF(A=1)THEN`` works too.
    Returns None if the text isn't a well-formed IF.
    """
    body_start = statement[2:]
    then_index = find_keyword(body_start, 'THEN')
    if then_index >= 0:
        condition = body_start[:then_index].strip()
        rest = body_start[then_index + 4:].strip()
    else:
        goto_index = find_keyword(body_start, 'GOTO')
        if goto_index < 0:
            return None
        condition = body_start[:goto_index].strip()
        rest = body_start[goto_index:].strip()  # IF cond GOTO n

    rest = rest.lstrip(':').strip()  # "THEN: ' note" after comment splitting
    if not condition:
        return None
    if not rest or StatementSplitter.is_rem_line(rest):
        return [f'IF {condition} THEN'] if then_index >= 0 else None

    then_text, else_text = _split_else(rest)
    then_lines = _branch_statements(then_text, commands)
    else_lines = _branch_statements(else_text, commands) if else_text is not None else []

    # When every branch is just a GOTO, keep one single-line IF subline: the
    # evaluator runs it directly, with no if_stack entry to leak each time
    # the jump is taken (e.g. a polling loop: IF A$="" THEN 10).
    def jump_only(lines):
        return len(lines) == 1 and _starts_with_keyword(lines[0], 'GOTO')

    if jump_only(then_lines) and (else_text is None or jump_only(else_lines)):
        line = f'IF {condition} THEN {then_lines[0]}'
        if else_text is not None:
            line += f' ELSE {else_lines[0]}'
        return [line]

    lines = [f'IF {condition} THEN'] + then_lines
    if else_text is not None:
        lines += ['ELSE'] + else_lines
    lines.append('ENDIF')
    return lines


_LOOP_CLOSERS = {'FOR': 'NEXT', 'WHILE': 'WEND', 'DO': 'LOOP'}


def _is_self_contained_loop(parts) -> bool:
    """True if the line opens a FOR/WHILE/DO and closes it on the same line."""
    for opener, closer in _LOOP_CLOSERS.items():
        if _starts_with_keyword(parts[0], opener):
            return any(_starts_with_keyword(p, closer) for p in parts[1:])
    return False


def starts_control_structure(statement: str) -> bool:
    """True if a subline is IF/FOR/WHILE/DO (whole-word match)."""
    return any(_starts_with_keyword(statement.strip(), kw) for kw in _CONTROL_PREFIXES)


def expand_statements(code: str, commands=frozenset()) -> List[str]:
    """Split a line into sublines, expanding one-line IFs.

    *commands* is the set of command/keyword words (used to tell an implicit
    GOTO target like ``THEN A*B`` from a statement like ``THEN CLS``).

    An IF takes the rest of the line as its body, as in Color BASIC —
    except inside a loop that opens and closes on the same line
    (``FOR I=1 TO 3: IF I=2 THEN PRINT "TWO": NEXT I``), where each IF's
    body is just its own statement. That exception is a deliberate
    BasiCoCo convention (kept from earlier versions) so the loop's NEXT is
    not swallowed by the IF.
    """
    parts = [p.strip() for p in StatementSplitter.split_on_delimiter(code) if p.strip()]
    if not parts:
        return []
    in_loop_line = _is_self_contained_loop(parts)
    result = []
    for i, part in enumerate(parts):
        if _starts_with_keyword(part, 'IF'):
            if_code = part if in_loop_line else ': '.join(parts[i:])
            expanded = _expand_if(if_code, commands)
            if not in_loop_line:
                result.extend(expanded if expanded is not None else parts[i:])
                return result
            result.extend(expanded if expanded is not None else [part])
        else:
            result.append(part)
    return result


def parse_and_convert_single_line(statement: str, parser=None) -> Optional[List[str]]:
    """Expand a single-line control structure into sublines.

    Returns None when *statement* is not a control structure needing
    expansion (so callers fall back to plain statement handling). If
    *parser* is given, its statement and registry keywords are used to
    recognise implicit GOTO targets.
    """
    stripped = statement.strip()
    if not starts_control_structure(stripped):
        return None
    commands = command_words(parser) if parser is not None else frozenset()
    if _starts_with_keyword(stripped, 'IF'):
        return _expand_if(stripped, commands)
    if ':' not in stripped:
        return None
    return expand_statements(stripped, commands)


def command_words(parser) -> frozenset:
    """Words that begin a statement: registry commands plus the AST
    parser's statement keywords."""
    words = set(getattr(parser, 'registry_commands', ()) or ())
    words |= {'PRINT', 'GOTO', 'GOSUB', 'RETURN', 'END', 'STOP', 'LET', 'INPUT',
              'LINE', 'IF', 'FOR', 'NEXT', 'WHILE', 'WEND', 'DO', 'LOOP', 'EXIT',
              'ON', 'REM', 'ELSE', 'ENDIF', 'RESUME', 'CLS', 'DATA', 'READ'}
    return frozenset(words)
