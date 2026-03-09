# Bitwise Operators in CoCo BASIC

## Overview

In Color Computer BASIC (and all Microsoft BASIC variants), AND, OR, and NOT
are **bitwise integer operators**, not purely logical operators.  They convert
operands to integers and operate bit-by-bit.

## Semantics

| Operator | Description | Example | Result |
|----------|-------------|---------|--------|
| `AND` | Bitwise AND | `82 AND 223` | `82` |
| `OR` | Bitwise OR | `5 OR 3` | `7` |
| `NOT` | Bitwise complement | `NOT 0` | `-1` |

## Comparison Results

CoCo BASIC comparisons return **-1 for true** and **0 for false**.  This is
because -1 in two's complement has all bits set (`0xFFFF` for 16-bit), so
bitwise AND/OR/NOT work correctly as logical operators when applied to
comparison results:

```basic
' Logical use (works because -1 AND -1 = -1, -1 AND 0 = 0)
IF (A > 5) AND (B < 10) THEN PRINT "BOTH TRUE"

' Bitwise use
PRINT 82 AND 223        ' 82 (mask bits)
PRINT CHR$(ASC("r") AND 223)  ' "R" (uppercase conversion)
```

## NOT

`NOT X` computes the one's complement: `NOT X = -(X + 1)`.

| Expression | Result |
|-----------|--------|
| `NOT 0` | `-1` |
| `NOT -1` | `0` |
| `NOT 1` | `-2` |
| `NOT 255` | `-256` |

## Range

Operands must be in 16-bit signed range (-32768 to 32767).  Values of 32768
or higher cause `?FC ERROR` on the real CoCo.

## Implementation

In BasiCoCo, AND/OR/NOT are implemented in `ast_evaluator.py`:

- `_to_basic_int()` converts Python booleans from comparisons to -1/0 and
  truncates floats to int before bitwise operations.
- GOSUB/RETURN save and restore if_stack and for_stack depth to prevent
  stale entries when RETURN exits from inside IF blocks or FOR loops.

## Sources

- [Color BASIC and 16-bits and AND and OR and NOT](https://subethasoftware.com/2022/09/18/color-basic-and-16-bits-and-and-and-or-and-not/) (Sub-Etha Software)
- [CoCopedia BASIC Reference](https://www.cocopedia.com/wiki/index.php/BASIC:BASIC)
- [QBasic Boolean Operators Manual](https://qbasic.net/en/qb-manual/Operators/Boolean.htm)
