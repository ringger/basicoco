"""
Function Registry for BasiCoCo BASIC Emulator

Provides the FunctionRegistry class used to register and look up
BASIC function handlers (LEFT$, ABS, LEN, etc.).
"""

from typing import Dict, List, Optional


class FunctionRegistry:
    """Registry for BASIC functions with extensible registration system"""

    def __init__(self):
        self.functions: Dict[str, callable] = {}

    def register(self, name: str, handler: callable):
        """Register a function handler"""
        self.functions[name.upper()] = handler

    def get_handler(self, name: str) -> Optional[callable]:
        """Get handler for a function"""
        return self.functions.get(name.upper())

    def list_functions(self) -> List[str]:
        """List all registered function names"""
        return sorted(self.functions.keys())

    def is_function(self, name: str) -> bool:
        """Check if a name is a registered function"""
        return name.upper() in self.functions
