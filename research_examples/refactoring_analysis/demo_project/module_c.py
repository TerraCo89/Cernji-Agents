"""Module C - Also depends on Module A"""
from demo_project.module_a import ClassA


def create_instance() -> ClassA:
    """Factory function for ClassA"""
    return ClassA()


def transform_data(values: list) -> str:
    """Transform data using ClassA"""
    instance = create_instance()
    return instance.method_one(values)
