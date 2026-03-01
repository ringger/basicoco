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


# ============================================================================
# String Functions
# ============================================================================

def fn_left(evaluator, args: List[Any]) -> str:
    """LEFT$(string, n) - return leftmost n characters"""
    if len(args) != 2:
        error = evaluator.error_context.syntax_error(
            f"LEFT$ requires exactly 2 arguments, got {len(args)}",
            suggestions=[
                "Correct syntax: LEFT$(string, count)",
                'Example: LEFT$("HELLO", 3) returns "HEL"',
                "First argument: string to extract from",
                "Second argument: number of characters to extract"
            ]
        )
        raise ValueError(error.format_detailed())
        
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
    if len(args) != 2:
        error = evaluator.error_context.syntax_error(
            f"RIGHT$ requires exactly 2 arguments, got {len(args)}",
            suggestions=[
                "Correct syntax: RIGHT$(string, count)",
                'Example: RIGHT$("HELLO", 3) returns "LLO"',
                "First argument: string to extract from",
                "Second argument: number of characters to extract"
            ]
        )
        raise ValueError(error.format_detailed())
        
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
            suggestions=[
                "Two argument form: MID$(string, start)",
                "Three argument form: MID$(string, start, length)",
                'Example: MID$("HELLO", 2, 3) returns "ELL"',
                "Start position is 1-based (first character is position 1)"
            ]
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
    if len(args) != 1:
        error = evaluator.error_context.syntax_error(
            f"CHR$ requires exactly 1 argument, got {len(args)}",
            suggestions=[
                "Correct syntax: CHR$(code)",
                "Example: CHR$(65) returns 'A'",
                "Argument: ASCII code (0-255)"
            ]
        )
        raise ValueError(error.format_detailed())
        
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
    if len(args) != 1:
        error = evaluator.error_context.syntax_error(
            f"STR$ requires exactly 1 argument, got {len(args)}",
            suggestions=[
                "Correct syntax: STR$(number)",
                "Example: STR$(42) returns ' 42'",
                "Converts number to string with leading space for positive numbers"
            ]
        )
        raise ValueError(error.format_detailed())
        
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
    if len(args) != 1:
        error = evaluator.error_context.syntax_error(
            f"LEN requires exactly 1 argument, got {len(args)}",
            suggestions=[
                "Correct syntax: LEN(string)",
                'Example: LEN("HELLO") returns 5',
                "Works with any string or string variable"
            ]
        )
        raise ValueError(error.format_detailed())
        
    return len(str(args[0]))


def fn_abs(evaluator, args: List[Any]) -> float:
    """ABS(n) - return absolute value"""
    if len(args) != 1:
        error = evaluator.error_context.syntax_error(
            f"ABS requires exactly 1 argument, got {len(args)}",
            suggestions=[
                "Correct syntax: ABS(number)",
                "Example: ABS(-5) returns 5",
                "Returns positive value regardless of input sign"
            ]
        )
        raise ValueError(error.format_detailed())
        
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
    if len(args) != 1:
        error = evaluator.error_context.syntax_error(
            f"INT requires exactly 1 argument, got {len(args)}",
            suggestions=[
                "Correct syntax: INT(number)",
                "Example: INT(3.7) returns 3",
                "Truncates decimal part (floor operation)"
            ]
        )
        raise ValueError(error.format_detailed())
        
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
    if len(args) != 1:
        error = evaluator.error_context.syntax_error(
            f"RND requires exactly 1 argument, got {len(args)}",
            suggestions=[
                "Correct syntax: RND(seed)",
                "Example: RND(1) returns random number 0.0 to 1.0",
                "Positive values generate new random numbers",
                "Negative values can be used to seed the generator"
            ]
        )
        raise ValueError(error.format_detailed())
        
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
    if len(args) != 1:
        error = evaluator.error_context.syntax_error(
            f"SQR requires exactly 1 argument, got {len(args)}",
            suggestions=[
                "Correct syntax: SQR(number)",
                "Example: SQR(9) returns 3",
                "Calculates square root of positive numbers"
            ]
        )
        raise ValueError(error.format_detailed())
        
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
    if len(args) != 1:
        error = evaluator.error_context.syntax_error(
            f"SIN requires exactly 1 argument, got {len(args)}",
            suggestions=[
                "Correct syntax: SIN(angle)",
                "Example: SIN(3.14159/2) returns 1 (90 degrees)",
                "Angle must be in radians, not degrees"
            ]
        )
        raise ValueError(error.format_detailed())
        
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
    if len(args) != 1:
        error = evaluator.error_context.syntax_error(
            f"COS requires exactly 1 argument, got {len(args)}",
            suggestions=[
                "Correct syntax: COS(angle)",
                "Example: COS(0) returns 1 (0 degrees)",
                "Angle must be in radians, not degrees"
            ]
        )
        raise ValueError(error.format_detailed())
        
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
    if len(args) != 1:
        error = evaluator.error_context.syntax_error(
            f"TAN requires exactly 1 argument, got {len(args)}",
            suggestions=[
                "Correct syntax: TAN(angle)",
                "Example: TAN(0.785) returns 1 (45 degrees)",
                "Angle must be in radians, not degrees",
                "Note: TAN is undefined at odd multiples of π/2"
            ]
        )
        raise ValueError(error.format_detailed())
        
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
    if len(args) != 1:
        error = evaluator.error_context.syntax_error(
            f"ATN requires exactly 1 argument, got {len(args)}",
            suggestions=[
                "Correct syntax: ATN(number)",
                "Example: ATN(1) returns 0.785 (45 degrees in radians)",
                "Returns angle in radians whose tangent is the argument"
            ]
        )
        raise ValueError(error.format_detailed())
        
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
    if len(args) != 1:
        error = evaluator.error_context.syntax_error(
            f"EXP requires exactly 1 argument, got {len(args)}",
            suggestions=[
                "Correct syntax: EXP(power)",
                "Example: EXP(1) returns 2.718 (e^1)",
                "Calculates e (2.718...) raised to the given power"
            ]
        )
        raise ValueError(error.format_detailed())
        
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
    if len(args) != 1:
        error = evaluator.error_context.syntax_error(
            f"LOG requires exactly 1 argument, got {len(args)}",
            suggestions=[
                "Correct syntax: LOG(number)",
                "Example: LOG(2.718) returns 1 (natural log of e)",
                "Calculates natural logarithm (base e)"
            ]
        )
        raise ValueError(error.format_detailed())
        
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
    if len(args) != 1:
        error = evaluator.error_context.syntax_error(
            f"ASC requires exactly 1 argument, got {len(args)}",
            suggestions=[
                "Correct syntax: ASC(string)",
                'Example: ASC("A") returns 65',
                "Returns ASCII code of first character in string"
            ]
        )
        raise ValueError(error.format_detailed())
        
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
    if len(args) != 1:
        error = evaluator.error_context.syntax_error(
            f"VAL requires exactly 1 argument, got {len(args)}",
            suggestions=[
                "Correct syntax: VAL(string)",
                'Example: VAL("123") returns 123',
                "Converts string representation to numeric value"
            ]
        )
        raise ValueError(error.format_detailed())
        
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
    # INKEY$ takes no arguments
    if len(args) != 0:
        raise ValueError("INKEY$ takes no arguments")
    
    # Get key from emulator's keyboard buffer
    if evaluator.emulator.keyboard_buffer:
        return evaluator.emulator.keyboard_buffer.pop(0)
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
    if len(args) != 2:
        raise ValueError("INSTR requires 2 arguments")
    string_val = str(args[0])
    search_val = str(args[1])
    
    pos = string_val.find(search_val)
    return pos + 1 if pos >= 0 else 0  # BASIC uses 1-based indexing, 0 = not found


def fn_space(evaluator, args: List[Any]) -> str:
    """SPACE$(n) - return string of n spaces"""
    if len(args) != 1:
        raise ValueError("SPACE$ requires 1 argument")
    n = int(args[0])
    if n < 0:
        raise ValueError("SPACE$ argument must be non-negative")
    return " " * n


def fn_string(evaluator, args: List[Any]) -> str:
    """STRING$(n, char) - return string of n repeated characters"""
    if len(args) != 2:
        raise ValueError("STRING$ requires 2 arguments")
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