"""Module B - Depends on Module A"""
from demo_project.module_a import ClassA, function_a, CONSTANT_A


class ClassB:
    """Uses ClassA"""

    def __init__(self):
        self.helper = ClassA()

    def process_data(self, data: list) -> str:
        """Process data using ClassA"""
        result = self.helper.method_one(data)
        return f"Processed: {result}"


def use_function_a():
    """Uses function_a from module_a"""
    greeting = function_a("World")
    print(greeting)
    print(CONSTANT_A)
