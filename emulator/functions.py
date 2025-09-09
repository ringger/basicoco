"""
BASIC Functions module for TRS-80 Color Computer BASIC Emulator

This module contains all BASIC function implementations as standalone functions,
making them easily extensible and maintainable. Functions are registered with
the FunctionRegistry and called during expression evaluation.
"""

import math
import random
from typing import Any, List, Union


# ============================================================================
# String Functions
# ============================================================================

def fn_left(evaluator, args: List[str]) -> str:
    """LEFT$(string, n) - return leftmost n characters"""
    if len(args) != 2:
        raise ValueError("LEFT$ requires 2 arguments")
    string_val = str(evaluator.evaluate(args[0]))
    n_val = int(evaluator.evaluate(args[1]))
    return string_val[:n_val]


def fn_right(evaluator, args: List[str]) -> str:
    """RIGHT$(string, n) - return rightmost n characters"""
    if len(args) != 2:
        raise ValueError("RIGHT$ requires 2 arguments")
    string_val = str(evaluator.evaluate(args[0]))
    n_val = int(evaluator.evaluate(args[1]))
    return string_val[-n_val:] if n_val > 0 else ""


def fn_mid(evaluator, args: List[str]) -> str:
    """MID$(string, start, [length]) - return substring"""
    if len(args) < 2 or len(args) > 3:
        raise ValueError("MID$ requires 2 or 3 arguments")
    string_val = str(evaluator.evaluate(args[0]))
    start_val = int(evaluator.evaluate(args[1])) - 1  # BASIC is 1-based
    
    if len(args) == 3:
        length_val = int(evaluator.evaluate(args[2]))
        return string_val[start_val:start_val + length_val]
    else:
        return string_val[start_val:]


def fn_chr(evaluator, args: List[str]) -> str:
    """CHR$(n) - return character from ASCII code"""
    if len(args) != 1:
        raise ValueError("CHR$ requires 1 argument")
    n = int(evaluator.evaluate(args[0]))
    if n < 0 or n > 255:
        raise ValueError("CHR$ argument out of range")
    return chr(n)


def fn_str(evaluator, args: List[str]) -> str:
    """STR$(n) - convert number to string"""
    if len(args) != 1:
        raise ValueError("STR$ requires 1 argument")
    n = evaluator.evaluate(args[0])
    # BASIC adds leading space for positive numbers
    return f" {n}" if n >= 0 else str(n)


# ============================================================================
# Numeric Functions
# ============================================================================

def fn_len(evaluator, args: List[str]) -> int:
    """LEN(string) - return string length"""
    if len(args) != 1:
        raise ValueError("LEN requires 1 argument")
    return len(str(evaluator.evaluate(args[0])))


def fn_abs(evaluator, args: List[str]) -> float:
    """ABS(n) - return absolute value"""
    if len(args) != 1:
        raise ValueError("ABS requires 1 argument")
    return abs(float(evaluator.evaluate(args[0])))


def fn_int(evaluator, args: List[str]) -> int:
    """INT(n) - return integer part (floor)"""
    if len(args) != 1:
        raise ValueError("INT requires 1 argument")
    return int(float(evaluator.evaluate(args[0])))


def fn_rnd(evaluator, args: List[str]) -> float:
    """RND(n) - return random number between 0 and 1"""
    if len(args) != 1:
        raise ValueError("RND requires 1 argument")
    n = float(evaluator.evaluate(args[0]))
    # In BASIC, RND(n) behavior:
    # n > 0: returns next random number
    # n = 0: returns last random number (we'll just return a new one)
    # n < 0: seeds with n and returns random (simplified here)
    return random.random()


def fn_sqr(evaluator, args: List[str]) -> float:
    """SQR(n) - return square root"""
    if len(args) != 1:
        raise ValueError("SQR requires 1 argument")
    n = float(evaluator.evaluate(args[0]))
    if n < 0:
        raise ValueError("SQR of negative number")
    return math.sqrt(n)


# ============================================================================
# Trigonometric Functions
# ============================================================================

def fn_sin(evaluator, args: List[str]) -> float:
    """SIN(n) - return sine of angle in radians"""
    if len(args) != 1:
        raise ValueError("SIN requires 1 argument")
    return math.sin(float(evaluator.evaluate(args[0])))


def fn_cos(evaluator, args: List[str]) -> float:
    """COS(n) - return cosine of angle in radians"""
    if len(args) != 1:
        raise ValueError("COS requires 1 argument")
    return math.cos(float(evaluator.evaluate(args[0])))


def fn_tan(evaluator, args: List[str]) -> float:
    """TAN(n) - return tangent of angle in radians"""
    if len(args) != 1:
        raise ValueError("TAN requires 1 argument")
    return math.tan(float(evaluator.evaluate(args[0])))


def fn_atn(evaluator, args: List[str]) -> float:
    """ATN(n) - return arctangent in radians"""
    if len(args) != 1:
        raise ValueError("ATN requires 1 argument")
    return math.atan(float(evaluator.evaluate(args[0])))


# ============================================================================
# Mathematical Functions
# ============================================================================

def fn_exp(evaluator, args: List[str]) -> float:
    """EXP(n) - return e raised to the power of n"""
    if len(args) != 1:
        raise ValueError("EXP requires 1 argument")
    return math.exp(float(evaluator.evaluate(args[0])))


def fn_log(evaluator, args: List[str]) -> float:
    """LOG(n) - return natural logarithm"""
    if len(args) != 1:
        raise ValueError("LOG requires 1 argument")
    n = float(evaluator.evaluate(args[0]))
    if n <= 0:
        raise ValueError("LOG of zero or negative number")
    return math.log(n)


# ============================================================================
# Conversion Functions
# ============================================================================

def fn_asc(evaluator, args: List[str]) -> int:
    """ASC(string) - return ASCII code of first character"""
    if len(args) != 1:
        raise ValueError("ASC requires 1 argument")
    s = str(evaluator.evaluate(args[0]))
    if not s:
        raise ValueError("ASC of empty string")
    return ord(s[0])


def fn_val(evaluator, args: List[str]) -> Union[int, float]:
    """VAL(string) - convert string to number"""
    if len(args) != 1:
        raise ValueError("VAL requires 1 argument")
    s = str(evaluator.evaluate(args[0])).strip()
    try:
        if '.' in s or 'E' in s.upper():
            return float(s)
        else:
            return int(s)
    except ValueError:
        return 0  # BASIC returns 0 for non-numeric strings


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
    
    # Numeric functions
    registry.register('LEN', fn_len)
    registry.register('ABS', fn_abs)
    registry.register('INT', fn_int)
    registry.register('RND', fn_rnd)
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


# ============================================================================
# Future Phase 2 Functions (Ready to implement)
# ============================================================================

def fn_instr(evaluator, args: List[str]) -> int:
    """INSTR(string, search) - find position of substring (1-based)"""
    if len(args) != 2:
        raise ValueError("INSTR requires 2 arguments")
    string_val = str(evaluator.evaluate(args[0]))
    search_val = str(evaluator.evaluate(args[1]))
    
    pos = string_val.find(search_val)
    return pos + 1 if pos >= 0 else 0  # BASIC uses 1-based indexing, 0 = not found


def fn_space(evaluator, args: List[str]) -> str:
    """SPACE$(n) - return string of n spaces"""
    if len(args) != 1:
        raise ValueError("SPACE$ requires 1 argument")
    n = int(evaluator.evaluate(args[0]))
    if n < 0:
        raise ValueError("SPACE$ argument must be non-negative")
    return " " * n


def fn_string(evaluator, args: List[str]) -> str:
    """STRING$(n, char) - return string of n repeated characters"""
    if len(args) != 2:
        raise ValueError("STRING$ requires 2 arguments")
    n = int(evaluator.evaluate(args[0]))
    char_arg = evaluator.evaluate(args[1])
    
    if n < 0:
        raise ValueError("STRING$ count must be non-negative")
    
    # Accept either ASCII code or string
    if isinstance(char_arg, (int, float)):
        char = chr(int(char_arg))
    else:
        char = str(char_arg)[0] if char_arg else ""
    
    return char * n