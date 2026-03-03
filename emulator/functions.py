"""
BASIC Functions module for TRS-80 Color Computer BASIC Emulator

This module contains all BASIC function implementations as standalone functions,
making them easily extensible and maintainable. Functions are registered with
the FunctionRegistry and called during expression evaluation.

ARCHITECTURE OWNERSHIP:
The function registry system in this module is the SINGLE authoritative source
for all BASIC functions. All function calls in BASIC programs are dispatched
through this registry. No BASIC functions should be implemented elsewhere in
the codebase - this prevents duplication and ensures consistent behavior.

Function implementations must be registered at the bottom of this file to be
available in BASIC programs.
"""

import math
import random
from typing import Any, List, Union
from .error_context import ErrorContextManager


def _check_args(evaluator, func_name, args, expected, syntax_example):
    """Validate argument count. Raises ValueError with formatted error if wrong."""
    if len(args) != expected:
        error = evaluator.error_context.syntax_error(
            f"{func_name} requires exactly {expected} argument{'s' if expected != 1 else ''}, got {len(args)}",
            suggestions=[f"Correct syntax: {syntax_example}"]
        )
        raise ValueError(error.format_detailed())


def _to_float(evaluator, value, func_name):
    """Convert value to float with a nice type error on failure."""
    try:
        return float(value)
    except (ValueError, TypeError):
        error = evaluator.error_context.type_error(
            f"{func_name} argument must be a number", "number",
            f"{type(value).__name__}")
        raise ValueError(error.format_detailed())


def _to_int(evaluator, value, func_name):
    """Convert value to int with a nice type error on failure."""
    try:
        return int(value)
    except (ValueError, TypeError):
        error = evaluator.error_context.type_error(
            f"{func_name} argument must be a number", "integer",
            f"{type(value).__name__}")
        raise ValueError(error.format_detailed())


# ============================================================================
# String Functions
# ============================================================================

def fn_left(evaluator, args: List[Any]) -> str:
    """LEFT$(string, n) - return leftmost n characters"""
    _check_args(evaluator, 'LEFT$', args, 2, 'LEFT$(string, count)')
    string_val = str(args[0])
    n_val = _to_int(evaluator, args[1], 'LEFT$')
    if n_val < 0:
        error = evaluator.error_context.runtime_error(
            f"LEFT$ count cannot be negative: {n_val}",
            suggestions=["Use a positive number or zero",
                         'Example: LEFT$("HELLO", 3) not LEFT$("HELLO", -1)',
                         "Zero returns empty string"])
        raise ValueError(error.format_detailed())
    return string_val[:n_val]


def fn_right(evaluator, args: List[Any]) -> str:
    """RIGHT$(string, n) - return rightmost n characters"""
    _check_args(evaluator, 'RIGHT$', args, 2, 'RIGHT$(string, count)')
    string_val = str(args[0])
    n_val = _to_int(evaluator, args[1], 'RIGHT$')
    if n_val < 0:
        error = evaluator.error_context.runtime_error(
            f"RIGHT$ count cannot be negative: {n_val}",
            suggestions=["Use a positive number or zero",
                         'Example: RIGHT$("HELLO", 3) not RIGHT$("HELLO", -1)',
                         "Zero returns empty string"])
        raise ValueError(error.format_detailed())
    return string_val[-n_val:] if n_val > 0 else ""


def fn_mid(evaluator, args: List[Any]) -> str:
    """MID$(string, start, [length]) - return substring"""
    if len(args) < 2 or len(args) > 3:
        error = evaluator.error_context.syntax_error(
            f"MID$ requires 2 or 3 arguments, got {len(args)}",
            suggestions=["Correct syntax: MID$(string, start[, length])"])
        raise ValueError(error.format_detailed())
    string_val = str(args[0])
    start_val = _to_int(evaluator, args[1], 'MID$')
    if start_val < 1:
        error = evaluator.error_context.runtime_error(
            f"MID$ start position must be 1 or greater: {start_val}",
            suggestions=["BASIC uses 1-based string indexing",
                         "First character is at position 1",
                         'Example: MID$("HELLO", 1, 2) returns "HE"'])
        raise ValueError(error.format_detailed())
    start_index = start_val - 1
    if len(args) == 3:
        length_val = _to_int(evaluator, args[2], 'MID$')
        if length_val < 0:
            error = evaluator.error_context.runtime_error(
                f"MID$ length cannot be negative: {length_val}",
                suggestions=["Use a positive length or omit for rest of string",
                             'Example: MID$("HELLO", 2, 3) not MID$("HELLO", 2, -1)'])
            raise ValueError(error.format_detailed())
        return string_val[start_index:start_index + length_val]
    else:
        return string_val[start_index:]


def fn_chr(evaluator, args: List[Any]) -> str:
    """CHR$(n) - return character from ASCII code"""
    _check_args(evaluator, 'CHR$', args, 1, 'CHR$(code)')
    n = _to_int(evaluator, args[0], 'CHR$')
    if n < 0 or n > 255:
        error = evaluator.error_context.runtime_error(
            f"CHR$ code {n} out of valid ASCII range (0-255)",
            suggestions=["Use codes 0-255 for valid ASCII characters",
                         "Common codes: 65='A', 97='a', 48='0', 32=' '",
                         "Use ASC() to get the code of a character"])
        raise ValueError(error.format_detailed())
    return chr(n)


def fn_str(evaluator, args: List[Any]) -> str:
    """STR$(n) - convert number to string"""
    _check_args(evaluator, 'STR$', args, 1, 'STR$(number)')
    n = _to_float(evaluator, args[0], 'STR$')
    if isinstance(args[0], int) or (isinstance(args[0], float) and args[0].is_integer()):
        n = int(n)
    # BASIC adds leading space for positive numbers
    return f" {n}" if n >= 0 else str(n)


# ============================================================================
# Numeric Functions
# ============================================================================

def fn_len(evaluator, args: List[Any]) -> int:
    """LEN(string) - return string length"""
    _check_args(evaluator, 'LEN', args, 1, 'LEN(string)')
        
    return len(str(args[0]))


def fn_abs(evaluator, args: List[Any]) -> float:
    """ABS(n) - return absolute value"""
    _check_args(evaluator, 'ABS', args, 1, 'ABS(number)')
    return abs(_to_float(evaluator, args[0], 'ABS'))


def fn_int(evaluator, args: List[Any]) -> int:
    """INT(n) - return integer part (floor)"""
    _check_args(evaluator, 'INT', args, 1, 'INT(number)')
    return int(_to_float(evaluator, args[0], 'INT'))


def fn_rnd(evaluator, args: List[Any]) -> float:
    """RND(n) - return random number between 0 and 1.

    CoCo semantics:
      RND(n) where n > 0: new random number (0 < x < 1)
      RND(0): repeat last random number
      RND(-n): reseed with n, then return new random number
    """
    _check_args(evaluator, 'RND', args, 1, 'RND(n)')
    n = _to_float(evaluator, args[0], 'RND')
    if n == 0:
        return evaluator.last_rnd
    if n < 0:
        random.seed(int(n))
    result = random.random()
    evaluator.last_rnd = result
    return result


def fn_sgn(evaluator, args: List[Any]) -> int:
    """SGN(n) - return sign of number (-1, 0, or 1)"""
    _check_args(evaluator, 'SGN', args, 1, 'SGN(number)')
    n = _to_float(evaluator, args[0], 'SGN')
    if n > 0:
        return 1
    elif n < 0:
        return -1
    else:
        return 0


def fn_sqr(evaluator, args: List[Any]) -> float:
    """SQR(n) - return square root"""
    _check_args(evaluator, 'SQR', args, 1, 'SQR(number)')
    n = _to_float(evaluator, args[0], 'SQR')
    if n < 0:
        error = evaluator.error_context.arithmetic_error(
            f"Cannot calculate square root of negative number: {n}",
            "SQR(n)",
            suggestions=["Square root is only defined for non-negative numbers",
                         "Use ABS() if you want the square root of the absolute value",
                         "Example: SQR(ABS(-9)) returns 3"])
        raise ValueError(error.format_detailed())
    return math.sqrt(n)


# ============================================================================
# Trigonometric Functions
# ============================================================================

def fn_sin(evaluator, args: List[Any]) -> float:
    """SIN(n) - return sine of angle in radians"""
    _check_args(evaluator, 'SIN', args, 1, 'SIN(angle)')
    return math.sin(_to_float(evaluator, args[0], 'SIN'))


def fn_cos(evaluator, args: List[Any]) -> float:
    """COS(n) - return cosine of angle in radians"""
    _check_args(evaluator, 'COS', args, 1, 'COS(angle)')
    return math.cos(_to_float(evaluator, args[0], 'COS'))


def fn_tan(evaluator, args: List[Any]) -> float:
    """TAN(n) - return tangent of angle in radians"""
    _check_args(evaluator, 'TAN', args, 1, 'TAN(angle)')
    angle = _to_float(evaluator, args[0], 'TAN')
    result = math.tan(angle)
    if abs(result) > 1e15:
        error = evaluator.error_context.arithmetic_error(
            f"TAN result too large at angle {angle}",
            "TAN(n)",
            suggestions=["TAN approaches infinity near odd multiples of π/2",
                         "Try a different angle value",
                         "π/2 ≈ 1.5708, 3π/2 ≈ 4.7124, etc."])
        raise ValueError(error.format_detailed())
    return result


def fn_atn(evaluator, args: List[Any]) -> float:
    """ATN(n) - return arctangent in radians"""
    _check_args(evaluator, 'ATN', args, 1, 'ATN(number)')
    return math.atan(_to_float(evaluator, args[0], 'ATN'))


# ============================================================================
# Mathematical Functions
# ============================================================================

def fn_exp(evaluator, args: List[Any]) -> float:
    """EXP(n) - return e raised to the power of n"""
    _check_args(evaluator, 'EXP', args, 1, 'EXP(power)')
    power = _to_float(evaluator, args[0], 'EXP')
    if power > 700:
        error = evaluator.error_context.arithmetic_error(
            f"EXP overflow: power {power} too large",
            "EXP(n)",
            suggestions=["EXP results become very large with high powers",
                         "Try smaller power values (less than 700)",
                         "Use LOG() for the inverse operation"])
        raise ValueError(error.format_detailed())
    return math.exp(power)


def fn_log(evaluator, args: List[Any]) -> float:
    """LOG(n) - return natural logarithm"""
    _check_args(evaluator, 'LOG', args, 1, 'LOG(number)')
    n = _to_float(evaluator, args[0], 'LOG')
    if n <= 0:
        error = evaluator.error_context.arithmetic_error(
            f"Cannot calculate LOG of non-positive number: {n}",
            "LOG(n)",
            suggestions=["LOG is only defined for positive numbers",
                         "Use ABS() if you want LOG of absolute value",
                         "Example: LOG(ABS(-5)) instead of LOG(-5)"])
        raise ValueError(error.format_detailed())
    return math.log(n)


# ============================================================================
# Conversion Functions
# ============================================================================

def _fn_base_conversion(evaluator, args, func_name, fmt, examples):
    """Shared implementation for HEX$ and OCT$ base conversion functions."""
    _check_args(evaluator, func_name, args, 1, f'{func_name}(number)')
    n = _to_int(evaluator, args[0], func_name)
    if n < 0 or n > 65535:
        error = evaluator.error_context.runtime_error(
            f"{func_name} argument out of range (0-65535): {n}",
            suggestions=[f"{func_name} accepts integers from 0 to 65535"] + examples)
        raise ValueError(error.format_detailed())
    return format(n, fmt)


def fn_hex(evaluator, args: List[Any]) -> str:
    """HEX$(n) - return hexadecimal string representation of number"""
    return _fn_base_conversion(evaluator, args, 'HEX$', 'X',
                               ['Example: HEX$(255) returns "FF"',
                                'Example: HEX$(4096) returns "1000"'])


def fn_oct(evaluator, args: List[Any]) -> str:
    """OCT$(n) - return octal string representation of number"""
    return _fn_base_conversion(evaluator, args, 'OCT$', 'o',
                               ['Example: OCT$(255) returns "377"',
                                'Example: OCT$(8) returns "10"'])


def fn_asc(evaluator, args: List[Any]) -> int:
    """ASC(string) - return ASCII code of first character"""
    _check_args(evaluator, 'ASC', args, 1, 'ASC(string)')
        
    s = str(args[0])
    
    if not s:
        error = evaluator.error_context.runtime_error(
            "Cannot get ASCII code of empty string",
            suggestions=[
                "Provide a non-empty string",
                'Example: ASC("A") not ASC("")',
                "Use LEN() to check string length first if needed"
            ]
        )
        raise ValueError(error.format_detailed())
        
    return ord(s[0])


def fn_val(evaluator, args: List[Any]) -> Union[int, float]:
    """VAL(string) - convert string to number"""
    _check_args(evaluator, 'VAL', args, 1, 'VAL(string)')
        
    s = str(args[0]).strip()
    
    try:
        if '.' in s or 'E' in s.upper():
            return float(s)
        else:
            return int(s)
    except ValueError:
        # BASIC returns 0 for non-numeric strings - this is authentic behavior
        return 0


# ============================================================================
# Special Functions
# ============================================================================

def fn_inkey(evaluator, args: List[Any]) -> str:
    """INKEY$ - return next key from keyboard buffer"""
    _check_args(evaluator, 'INKEY$', args, 0, 'INKEY$')

    # Get key from emulator's keyboard buffer
    if evaluator.keyboard_buffer:
        return evaluator.keyboard_buffer.pop(0)
    return ""


def fn_eof(evaluator, args: List[Any]) -> int:
    """EOF(file_number) - return -1 at end of file, 0 otherwise"""
    _check_args(evaluator, 'EOF', args, 1, 'EOF(file_number)')
    file_num = _to_int(evaluator, args[0], 'EOF')
    return evaluator.file_io.eof(file_num)

# ============================================================================
# Function Registration
# ============================================================================

def register_all_functions(registry):
    """Register all built-in BASIC functions with the given registry"""
    
    # String functions
    registry.register('LEFT$', fn_left)
    registry.register('RIGHT$', fn_right)
    registry.register('MID$', fn_mid)
    registry.register('CHR$', fn_chr)
    registry.register('STR$', fn_str)
    registry.register('INSTR', fn_instr)
    registry.register('SPACE$', fn_space)
    registry.register('STRING$', fn_string)
    registry.register('INKEY$', fn_inkey)
    
    # Numeric functions
    registry.register('LEN', fn_len)
    registry.register('ABS', fn_abs)
    registry.register('INT', fn_int)
    registry.register('RND', fn_rnd)
    registry.register('SGN', fn_sgn)
    registry.register('SQR', fn_sqr)
    
    # Trigonometric functions
    registry.register('SIN', fn_sin)
    registry.register('COS', fn_cos)
    registry.register('TAN', fn_tan)
    registry.register('ATN', fn_atn)
    
    # Mathematical functions
    registry.register('EXP', fn_exp)
    registry.register('LOG', fn_log)
    
    # Conversion functions
    registry.register('ASC', fn_asc)
    registry.register('VAL', fn_val)
    registry.register('HEX$', fn_hex)
    registry.register('OCT$', fn_oct)

    # File I/O functions
    registry.register('EOF', fn_eof)


# ============================================================================
# Additional String Functions
# ============================================================================

def fn_instr(evaluator, args: List[Any]) -> int:
    """INSTR([start,] string, search) - find position of substring (1-based)"""
    if len(args) == 2:
        start_pos = 1
        string_val = str(args[0])
        search_val = str(args[1])
    elif len(args) == 3:
        start_pos = _to_int(evaluator, args[0], 'INSTR')
        string_val = str(args[1])
        search_val = str(args[2])
    else:
        error = evaluator.error_context.syntax_error(
            f"INSTR requires 2 or 3 arguments, got {len(args)}",
            suggestions=["Correct syntax: INSTR([start,] string, search)"])
        raise ValueError(error.format_detailed())
    if start_pos < 1:
        start_pos = 1
    pos = string_val.find(search_val, start_pos - 1)
    return pos + 1 if pos >= 0 else 0  # BASIC uses 1-based indexing, 0 = not found


def fn_space(evaluator, args: List[Any]) -> str:
    """SPACE$(n) - return string of n spaces"""
    _check_args(evaluator, 'SPACE$', args, 1, 'SPACE$(count)')
    n = _to_int(evaluator, args[0], 'SPACE$')
    if n < 0:
        error = evaluator.error_context.runtime_error(
            f"SPACE$ count cannot be negative: {n}",
            suggestions=["Use a positive number or zero",
                         'Example: SPACE$(5) returns "     "'])
        raise ValueError(error.format_detailed())
    return " " * n


def fn_string(evaluator, args: List[Any]) -> str:
    """STRING$(n, char) - return string of n repeated characters"""
    _check_args(evaluator, 'STRING$', args, 2, 'STRING$(count, char)')
    n = _to_int(evaluator, args[0], 'STRING$')
    if n < 0:
        error = evaluator.error_context.runtime_error(
            f"STRING$ count cannot be negative: {n}",
            suggestions=["Use a positive number or zero",
                         'Example: STRING$(5, "*") returns "*****"'])
        raise ValueError(error.format_detailed())
    char_arg = args[1]
    if isinstance(char_arg, (int, float)):
        char = chr(int(char_arg))
    else:
        char = str(char_arg)[0] if char_arg else ""
    return char * n