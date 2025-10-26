"""
AST-based Dependency Analyzer
Analyzes import dependencies using Python's built-in AST module.
This script identifies all imports and can find reverse dependencies.
"""
import ast
import os
from pathlib import Path
from typing import Dict, List, Set
from dataclasses import dataclass, field


@dataclass
class ImportInfo:
    """Stores information about an import statement"""
    module: str
    names: List[str] = field(default_factory=list)
    is_from_import: bool = False
    line_number: int = 0


@dataclass
class ModuleDependencies:
    """Stores all dependencies for a module"""
    file_path: str
    imports: List[ImportInfo] = field(default_factory=list)

    @property
    def direct_dependencies(self) -> Set[str]:
        """Get unique set of modules this file imports"""
        return {imp.module for imp in self.imports}


class ImportVisitor(ast.NodeVisitor):
    """AST visitor that collects import information"""

    def __init__(self):
        self.imports: List[ImportInfo] = []

    def visit_Import(self, node: ast.Import):
        """Handle 'import module' statements"""
        for alias in node.names:
            self.imports.append(ImportInfo(
                module=alias.name,
                names=[alias.asname or alias.name],
                is_from_import=False,
                line_number=node.lineno
            ))
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Handle 'from module import name' statements"""
        if node.module:  # Can be None for relative imports like 'from . import foo'
            imported_names = [alias.name for alias in node.names]
            self.imports.append(ImportInfo(
                module=node.module,
                names=imported_names,
                is_from_import=True,
                line_number=node.lineno
            ))
        self.generic_visit(node)


class DependencyAnalyzer:
    """Analyzes dependencies across a Python project"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.module_deps: Dict[str, ModuleDependencies] = {}

    def analyze_file(self, file_path: Path) -> ModuleDependencies:
        """Analyze a single Python file for imports"""
        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                tree = ast.parse(f.read(), filename=str(file_path))
                visitor = ImportVisitor()
                visitor.visit(tree)

                return ModuleDependencies(
                    file_path=str(file_path),
                    imports=visitor.imports
                )
            except SyntaxError as e:
                print(f"Syntax error in {file_path}: {e}")
                return ModuleDependencies(file_path=str(file_path))

    def analyze_project(self) -> Dict[str, ModuleDependencies]:
        """Analyze all Python files in the project"""
        for py_file in self.project_root.rglob("*.py"):
            if "__pycache__" not in str(py_file):
                module_name = self._get_module_name(py_file)
                self.module_deps[module_name] = self.analyze_file(py_file)

        return self.module_deps

    def _get_module_name(self, file_path: Path) -> str:
        """Convert file path to module name"""
        rel_path = file_path.relative_to(self.project_root)
        parts = list(rel_path.parts[:-1])

        if rel_path.name != "__init__.py":
            parts.append(rel_path.stem)

        return ".".join(parts) if parts else rel_path.stem

    def find_reverse_dependencies(self, target_module: str) -> Dict[str, List[ImportInfo]]:
        """
        Find all modules that import the target module (reverse dependencies).

        This is critical for refactoring - shows what will break if you move/rename a module.
        """
        reverse_deps = {}

        for module_name, deps in self.module_deps.items():
            imports_target = [
                imp for imp in deps.imports
                if imp.module == target_module or imp.module.startswith(f"{target_module}.")
            ]

            if imports_target:
                reverse_deps[module_name] = imports_target

        return reverse_deps

    def generate_impact_report(self, target_module: str) -> str:
        """
        Generate a detailed impact report for moving/refactoring a module.

        This shows:
        - Who imports this module
        - What they import from it
        - Line numbers for easy updating
        """
        reverse_deps = self.find_reverse_dependencies(target_module)

        if not reverse_deps:
            return f"No modules import '{target_module}' - safe to move!"

        report = [f"Impact Analysis for '{target_module}'"]
        report.append("=" * 60)
        report.append(f"\n{len(reverse_deps)} module(s) will be affected:\n")

        for module, imports in sorted(reverse_deps.items()):
            report.append(f"\n* {module}")
            report.append(f"   File: {self.module_deps[module].file_path}")

            for imp in imports:
                import_type = "from-import" if imp.is_from_import else "import"
                if imp.is_from_import:
                    names = ", ".join(imp.names)
                    report.append(f"   Line {imp.line_number}: from {imp.module} import {names}")
                else:
                    report.append(f"   Line {imp.line_number}: import {imp.module}")

        report.append("\n" + "=" * 60)
        report.append("\nWARNING: All listed imports will need updating if you move this module!")

        return "\n".join(report)

    def get_dependency_tree(self, module: str, max_depth: int = 3) -> Dict:
        """Get the full dependency tree for a module"""
        def _get_deps(mod: str, depth: int = 0) -> Dict:
            if depth >= max_depth or mod not in self.module_deps:
                return {}

            deps = {}
            for imp in self.module_deps[mod].imports:
                deps[imp.module] = _get_deps(imp.module, depth + 1)

            return deps

        return {module: _get_deps(module)}


def main():
    """Demonstrate the AST-based dependency analyzer"""

    # Analyze the demo project
    demo_path = Path(__file__).parent / "demo_project"

    if not demo_path.exists():
        print(f"Demo project not found at {demo_path}")
        return

    print("Analyzing Python project dependencies using AST...\n")

    analyzer = DependencyAnalyzer(demo_path)
    analyzer.analyze_project()

    # Show all modules found
    print("Modules found:")
    for module in sorted(analyzer.module_deps.keys()):
        deps = analyzer.module_deps[module]
        print(f"  - {module} ({len(deps.imports)} imports)")

    print("\n" + "=" * 60)

    # Impact analysis: What happens if we move module_a?
    target = "demo_project.module_a"
    print(f"\nImpact Analysis: Moving '{target}'\n")

    report = analyzer.generate_impact_report(target)
    print(report)

    # Show direct dependencies
    print("\n" + "=" * 60)
    print("\nDirect Dependencies by Module:\n")

    for module, deps in sorted(analyzer.module_deps.items()):
        if deps.direct_dependencies:
            print(f"{module}:")
            for dep in sorted(deps.direct_dependencies):
                print(f"  -> {dep}")
            print()


if __name__ == "__main__":
    main()
