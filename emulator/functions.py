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


# ============================================================================
# String Functions
# ============================================================================

def fn_left(evaluator, args: List[Any]) -> str:
    """LEFT$(string, n) - return leftmost n characters"""
    _check_args(evaluator, 'LEFT$', args, 2, 'LEFT$(string, count)')
        
    try:
        string_val = str(args[0])
        n_val = int(args[1])
        
        if n_val < 0:
            error = evaluator.error_context.runtime_error(
                f"LEFT$ count cannot be negative: {n_val}",
                suggestions=[
                    "Use a positive number or zero",
                    'Example: LEFT$("HELLO", 3) not LEFT$("HELLO", -1)',
                    "Zero returns empty string"
                ]
            )
            raise ValueError(error.format_detailed())
            
        return string_val[:n_val]
        
    except (ValueError, TypeError) as e:
        if "invalid literal" in str(e).lower():
            error = evaluator.error_context.type_error(
                "LEFT$ second argument must be a number",
                "integer",
                f"{type(args[1]).__name__}",
                suggestions=[
                    "Second argument must be numeric",
                    'Example: LEFT$("HELLO", 3) not LEFT$("HELLO", "ABC")',
                    "Use a variable containing a number if needed"
                ]
            )
            raise ValueError(error.format_detailed())
        raise


def fn_right(evaluator, args: List[Any]) -> str:
    """RIGHT$(string, n) - return rightmost n characters"""
    _check_args(evaluator, 'RIGHT$', args, 2, 'RIGHT$(string, count)')
        
    try:
        string_val = str(args[0])
        n_val = int(args[1])
        
        if n_val < 0:
            error = evaluator.error_context.runtime_error(
                f"RIGHT$ count cannot be negative: {n_val}",
                suggestions=[
                    "Use a positive number or zero",
                    'Example: RIGHT$("HELLO", 3) not RIGHT$("HELLO", -1)',
                    "Zero returns empty string"
                ]
            )
            raise ValueError(error.format_detailed())
            
        return string_val[-n_val:] if n_val > 0 else ""
        
    except (ValueError, TypeError) as e:
        if "invalid literal" in str(e).lower():
            error = evaluator.error_context.type_error(
                "RIGHT$ second argument must be a number",
                "integer",
                f"{type(args[1]).__name__}",
                suggestions=[
                    "Second argument must be numeric",
                    'Example: RIGHT$("HELLO", 3) not RIGHT$("HELLO", "ABC")',
                    "Use a variable containing a number if needed"
                ]
            )
            raise ValueError(error.format_detailed())
        raise


def fn_mid(evaluator, args: List[Any]) -> str:
    """MID$(string, start, [length]) - return substring"""
    if len(args) < 2 or len(args) > 3:
        error = evaluator.error_context.syntax_error(
            f"MID$ requires 2 or 3 arguments, got {len(args)}",
            suggestions=["Correct syntax: MID$(string, start[, length])"]
        )
        raise ValueError(error.format_detailed())
        
    try:
        string_val = str(args[0])
        start_val = int(args[1])
        
        if start_val < 1:
            error = evaluator.error_context.runtime_error(
                f"MID$ start position must be 1 or greater: {start_val}",
                suggestions=[
                    "BASIC uses 1-based string indexing",
                    "First character is at position 1",
                    'Example: MID$("HELLO", 1, 2) returns "HE"'
                ]
            )
            raise ValueError(error.format_detailed())
        
        # Convert to 0-based for Python
        start_index = start_val - 1
        
        if len(args) == 3:
            length_val = int(args[2])
            
            if length_val < 0:
                error = evaluator.error_context.runtime_error(
                    f"MID$ length cannot be negative: {length_val}",
                    suggestions=[
                        "Use a positive length or omit for rest of string",
                        'Example: MID$("HELLO", 2, 3) not MID$("HELLO", 2, -1)'
                    ]
                )
                raise ValueError(error.format_detailed())
                
            return string_val[start_index:start_index + length_val]
        else:
            return string_val[start_index:]
            
    except (ValueError, TypeError) as e:
        if "invalid literal" in str(e).lower():
            error = evaluator.error_context.type_error(
                "MID$ numeric arguments must be integers",
                "integer",
                "string",
                suggestions=[
                    "Start position must be a number",
                    "Length (if provided) must be a number",
                    'Example: MID$("HELLO", 2, 3) not MID$("HELLO", "X", "Y")'
                ]
            )
            raise ValueError(error.format_detailed())
        raise


def fn_chr(evaluator, args: List[Any]) -> str:
    """CHR$(n) - return character from ASCII code"""
    _check_args(evaluator, 'CHR$', args, 1, 'CHR$(code)')
        
    try:
        n = int(args[0])
        
        if n < 0 or n > 255:
            error = evaluator.error_context.runtime_error(
                f"CHR$ code {n} out of valid ASCII range (0-255)",
                suggestions=[
                    "Use codes 0-255 for valid ASCII characters",
                    "Common codes: 65='A', 97='a', 48='0', 32=' '",
                    "Use ASC() to get the code of a character"
                ]
            )
            raise ValueError(error.format_detailed())
            
        return chr(n)
        
    except (ValueError, TypeError) as e:
        if "invalid literal" in str(e).lower():
            error = evaluator.error_context.type_error(
                "CHR$ argument must be a number",
                "integer",
                f"{type(args[0]).__name__}",
                suggestions=[
                    "Provide an ASCII code (0-255)",
                    'Example: CHR$(65) not CHR$("A")',
                    "Use ASC() to convert character to code first"
                ]
            )
            raise ValueError(error.format_detailed())
        raise


def fn_str(evaluator, args: List[Any]) -> str:
    """STR$(n) - convert number to string"""
    _check_args(evaluator, 'STR$', args, 1, 'STR$(number)')
        
    try:
        n = float(args[0])  # Convert to number to validate
        
        # Convert back to original type for proper formatting
        if isinstance(args[0], int) or (isinstance(args[0], float) and args[0].is_integer()):
            n = int(n)
        
        # BASIC adds leading space for positive numbers
        return f" {n}" if n >= 0 else str(n)
        
    except (ValueError, TypeError) as e:
        error = evaluator.error_context.type_error(
            "STR$ argument must be a number",
            "number",
            f"{type(args[0]).__name__}",
            suggestions=[
                "Provide a numeric value to convert",
                'Example: STR$(42) not STR$("hello")',
                "Use string concatenation for non-numeric strings"
            ]
        )
        raise ValueError(error.format_detailed())


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
        
    try:
        return abs(float(args[0]))
    except (ValueError, TypeError) as e:
        error = evaluator.error_context.type_error(
            "ABS argument must be a number",
            "number",
            f"{type(args[0]).__name__}",
            suggestions=[
                "Provide a numeric value",
                'Example: ABS(-3.14) not ABS("text")',
                "Use VAL() to convert string to number if needed"
            ]
        )
        raise ValueError(error.format_detailed())


def fn_int(evaluator, args: List[Any]) -> int:
    """INT(n) - return integer part (floor)"""
    _check_args(evaluator, 'INT', args, 1, 'INT(number)')
        
    try:
        return int(float(args[0]))
    except (ValueError, TypeError) as e:
        error = evaluator.error_context.type_error(
            "INT argument must be a number",
            "number",
            f"{type(args[0]).__name__}",
            suggestions=[
                "Provide a numeric value to truncate",
                'Example: INT(3.7) not INT("hello")',
                "Use VAL() to convert string to number first"
            ]
        )
        raise ValueError(error.format_detailed())


def fn_rnd(evaluator, args: List[Any]) -> float:
    """RND(n) - return random number between 0 and 1"""
    _check_args(evaluator, 'RND', args, 1, 'RND(seed)')
        
    try:
        n = float(args[0])
        # In BASIC, RND(n) behavior:
        # n > 0: returns next random number
        # n = 0: returns last random number (we'll just return a new one)
        # n < 0: seeds with n and returns random (simplified here)
        return random.random()
    except (ValueError, TypeError) as e:
        error = evaluator.error_context.type_error(
            "RND argument must be a number",
            "number",
            f"{type(args[0]).__name__}",
            suggestions=[
                "Provide a numeric seed value",
                'Example: RND(1) not RND("random")',
                "Use any number as seed (positive, negative, or zero)"
            ]
        )
        raise ValueError(error.format_detailed())


def fn_sqr(evaluator, args: List[Any]) -> float:
    """SQR(n) - return square root"""
    _check_args(evaluator, 'SQR', args, 1, 'SQR(number)')
        
    try:
        n = float(args[0])
        
        if n < 0:
            error = evaluator.error_context.arithmetic_error(
                f"Cannot calculate square root of negative number: {n}",
                "SQR(n)",
                suggestions=[
                    "Square root is only defined for non-negative numbers",
                    "Use ABS() if you want the square root of the absolute value",
                    "Example: SQR(ABS(-9)) returns 3"
                ]
            )
            raise ValueError(error.format_detailed())
            
        return math.sqrt(n)
        
    except (ValueError, TypeError) as e:
        if "square root of negative number" not in str(e).lower():
            error = evaluator.error_context.type_error(
                "SQR argument must be a number",
                "number",
                f"{type(args[0]).__name__}"
            )
            raise ValueError(error.format_detailed())
        raise


# ============================================================================
# Trigonometric Functions
# ============================================================================

def fn_sin(evaluator, args: List[Any]) -> float:
    """SIN(n) - return sine of angle in radians"""
    _check_args(evaluator, 'SIN', args, 1, 'SIN(angle)')
        
    try:
        return math.sin(float(args[0]))
    except (ValueError, TypeError) as e:
        error = evaluator.error_context.type_error(
            "SIN argument must be a number",
            "number",
            f"{type(args[0]).__name__}",
            suggestions=[
                "Provide an angle in radians",
                'Example: SIN(1.57) not SIN("ninety")',
                "To convert degrees: angle_radians = degrees * 3.14159 / 180"
            ]
        )
        raise ValueError(error.format_detailed())


def fn_cos(evaluator, args: List[Any]) -> float:
    """COS(n) - return cosine of angle in radians"""
    _check_args(evaluator, 'COS', args, 1, 'COS(angle)')
        
    try:
        return math.cos(float(args[0]))
    except (ValueError, TypeError) as e:
        error = evaluator.error_context.type_error(
            "COS argument must be a number",
            "number",
            f"{type(args[0]).__name__}",
            suggestions=[
                "Provide an angle in radians",
                'Example: COS(3.14159) not COS("180")',
                "To convert degrees: angle_radians = degrees * 3.14159 / 180"
            ]
        )
        raise ValueError(error.format_detailed())


def fn_tan(evaluator, args: List[Any]) -> float:
    """TAN(n) - return tangent of angle in radians"""
    _check_args(evaluator, 'TAN', args, 1, 'TAN(angle)')
        
    try:
        angle = float(args[0])
        result = math.tan(angle)
        
        # Check for very large results (approaching infinity)
        if abs(result) > 1e15:
            error = evaluator.error_context.arithmetic_error(
                f"TAN result too large at angle {angle}",
                "TAN(n)",
                suggestions=[
                    "TAN approaches infinity near odd multiples of π/2",
                    "Try a different angle value",
                    "π/2 ≈ 1.5708, 3π/2 ≈ 4.7124, etc."
                ]
            )
            raise ValueError(error.format_detailed())
            
        return result
        
    except (ValueError, TypeError) as e:
        if "too large" not in str(e).lower():
            error = evaluator.error_context.type_error(
                "TAN argument must be a number",
                "number",
                f"{type(args[0]).__name__}",
                suggestions=[
                    "Provide an angle in radians",
                    'Example: TAN(0.785) not TAN("45")',
                    "To convert degrees: angle_radians = degrees * 3.14159 / 180"
                ]
            )
            raise ValueError(error.format_detailed())
        raise


def fn_atn(evaluator, args: List[Any]) -> float:
    """ATN(n) - return arctangent in radians"""
    _check_args(evaluator, 'ATN', args, 1, 'ATN(number)')
        
    try:
        return math.atan(float(args[0]))
    except (ValueError, TypeError) as e:
        error = evaluator.error_context.type_error(
            "ATN argument must be a number",
            "number",
            f"{type(args[0]).__name__}",
            suggestions=[
                "Provide a numeric value",
                'Example: ATN(1) not ATN("one")',
                "Result will be in radians (-π/2 to π/2)"
            ]
        )
        raise ValueError(error.format_detailed())


# ============================================================================
# Mathematical Functions
# ============================================================================

def fn_exp(evaluator, args: List[Any]) -> float:
    """EXP(n) - return e raised to the power of n"""
    _check_args(evaluator, 'EXP', args, 1, 'EXP(power)')
        
    try:
        power = float(args[0])
        
        # Check for potential overflow
        if power > 700:
            error = evaluator.error_context.arithmetic_error(
                f"EXP overflow: power {power} too large",
                "EXP(n)",
                suggestions=[
                    "EXP results become very large with high powers",
                    "Try smaller power values (less than 700)",
                    "Use LOG() for the inverse operation"
                ]
            )
            raise ValueError(error.format_detailed())
            
        return math.exp(power)
        
    except (ValueError, TypeError) as e:
        if "overflow" not in str(e).lower():
            error = evaluator.error_context.type_error(
                "EXP argument must be a number",
                "number",
                f"{type(args[0]).__name__}",
                suggestions=[
                    "Provide a numeric power value",
                    'Example: EXP(2) not EXP("two")',
                    "Use LOG() for the inverse operation"
                ]
            )
            raise ValueError(error.format_detailed())
        raise


def fn_log(evaluator, args: List[Any]) -> float:
    """LOG(n) - return natural logarithm"""
    _check_args(evaluator, 'LOG', args, 1, 'LOG(number)')
        
    try:
        n = float(args[0])
        
        if n <= 0:
            error = evaluator.error_context.arithmetic_error(
                f"Cannot calculate LOG of non-positive number: {n}",
                "LOG(n)",
                suggestions=[
                    "LOG is only defined for positive numbers",
                    "Use ABS() if you want LOG of absolute value",
                    "Example: LOG(ABS(-5)) instead of LOG(-5)",
                    "LOG(0) approaches negative infinity"
                ]
            )
            raise ValueError(error.format_detailed())
            
        return math.log(n)
        
    except (ValueError, TypeError) as e:
        if "log of non-positive number" not in str(e).lower():
            error = evaluator.error_context.type_error(
                "LOG argument must be a number",
                "number",
                f"{type(args[0]).__name__}",
                suggestions=[
                    "Provide a positive numeric value",
                    'Example: LOG(10) not LOG("ten")',
                    "Use EXP() for the inverse operation"
                ]
            )
            raise ValueError(error.format_detailed())
        raise


# ============================================================================
# Conversion Functions
# ============================================================================

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
# Additional String Functions
# ============================================================================

def fn_instr(evaluator, args: List[Any]) -> int:
    """INSTR(string, search) - find position of substring (1-based)"""
    _check_args(evaluator, 'INSTR', args, 2, 'INSTR(string, search)')
    string_val = str(args[0])
    search_val = str(args[1])
    
    pos = string_val.find(search_val)
    return pos + 1 if pos >= 0 else 0  # BASIC uses 1-based indexing, 0 = not found


def fn_space(evaluator, args: List[Any]) -> str:
    """SPACE$(n) - return string of n spaces"""
    _check_args(evaluator, 'SPACE$', args, 1, 'SPACE$(count)')
    n = int(args[0])
    if n < 0:
        raise ValueError("SPACE$ argument must be non-negative")
    return " " * n


def fn_string(evaluator, args: List[Any]) -> str:
    """STRING$(n, char) - return string of n repeated characters"""
    _check_args(evaluator, 'STRING$', args, 2, 'STRING$(count, char)')
    n = int(args[0])
    char_arg = args[1]
    
    if n < 0:
        raise ValueError("STRING$ count must be non-negative")
    
    # Accept either ASCII code or string
    if isinstance(char_arg, (int, float)):
        char = chr(int(char_arg))
    else:
        char = str(char_arg)[0] if char_arg else ""
    
    return char * n