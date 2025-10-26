"""Module A - Will be moved to demonstrate impact analysis"""
from typing import List


class ClassA:
    """A sample class to demonstrate refactoring"""

    def method_one(self, items: List[str]) -> str:
        """Concatenate items"""
        return ", ".join(items)

    def method_two(self, value: int) -> int:
        """Double a value"""
        return value * 2


def function_a(name: str) -> str:
    """A standalone function"""
    return f"Hello, {name}!"


CONSTANT_A = "This is a constant in module A"
