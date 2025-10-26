"""Module D - Depends on Module B"""
from demo_project.module_b import ClassB


class ClassD:
    """Indirectly depends on Module A through Module B"""

    def __init__(self):
        self.processor = ClassB()

    def run(self, items: list):
        """Run processing"""
        return self.processor.process_data(items)
