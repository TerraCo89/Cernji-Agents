"""
Complete Refactoring Workflow - Combining All Tools
Demonstrates a comprehensive pre-refactoring analysis using AST, Rope, and PyDeps.

This is the GOLD STANDARD workflow for safe refactoring:
1. AST analysis - Quick dependency scan
2. PyDeps - Visual dependency graphs
3. Rope - Preview exact changes
4. Apply changes with confidence
"""
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional

# Import our analysis tools
sys.path.insert(0, str(Path(__file__).parent))

from ast_dependency_analyzer import DependencyAnalyzer
from rope.base.project import Project
from rope.refactor.move import MoveModule


@dataclass
class RefactoringPlan:
    """Represents a planned refactoring operation"""
    operation: str  # "move", "rename", "extract"
    source: str
    destination: str
    risk_level: str  # "low", "medium", "high"
    affected_modules: List[str]
    warnings: List[str]


class RefactoringWorkflow:
    """
    Comprehensive refactoring workflow that combines all analysis tools.
    """

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.ast_analyzer = DependencyAnalyzer(project_root)
        self.rope_project: Optional[Project] = None

    def __enter__(self):
        """Context manager entry"""
        self.rope_project = Project(str(self.project_root))
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup"""
        if self.rope_project:
            self.rope_project.close()

    def analyze_move_operation(self, module_path: str, new_location: str) -> RefactoringPlan:
        """
        Complete analysis of moving a module.

        Phase 1: Static Analysis (AST)
        Phase 2: Impact Assessment
        Phase 3: Risk Calculation
        Phase 4: Preview Generation
        """
        print("\n" + "=" * 80)
        print(f"🔍 COMPREHENSIVE REFACTORING ANALYSIS")
        print("=" * 80)
        print(f"\nOperation: Move module")
        print(f"Source:      {module_path}")
        print(f"Destination: {new_location}")

        # Phase 1: AST Analysis
        print("\n" + "-" * 80)
        print("📋 PHASE 1: Static Dependency Analysis (AST)")
        print("-" * 80)

        self.ast_analyzer.analyze_project()

        # Find reverse dependencies
        reverse_deps = self.ast_analyzer.find_reverse_dependencies(module_path)

        print(f"\n✓ Found {len(reverse_deps)} modules that import {module_path}")

        affected_modules = list(reverse_deps.keys())

        for module, imports in reverse_deps.items():
            print(f"  - {module} ({len(imports)} import(s))")

        # Phase 2: Impact Assessment
        print("\n" + "-" * 80)
        print("📊 PHASE 2: Impact Assessment")
        print("-" * 80)

        # Calculate impact metrics
        total_imports = sum(len(imports) for imports in reverse_deps.values())

        print(f"\nImpact Metrics:")
        print(f"  • Modules affected: {len(affected_modules)}")
        print(f"  • Import statements to update: {total_imports}")

        # Phase 3: Risk Assessment
        print("\n" + "-" * 80)
        print("⚠️  PHASE 3: Risk Assessment")
        print("-" * 80)

        warnings = []
        risk_level = "low"

        if len(affected_modules) == 0:
            risk_level = "low"
            print("\n✅ LOW RISK - No modules import this")

        elif len(affected_modules) <= 2:
            risk_level = "low"
            print("\n✅ LOW RISK - Few modules affected")

        elif len(affected_modules) <= 5:
            risk_level = "medium"
            print("\n⚠️  MEDIUM RISK - Several modules affected")
            warnings.append("Multiple modules need import updates")

        else:
            risk_level = "high"
            print("\n🚨 HIGH RISK - Many modules affected")
            warnings.append("Extensive refactoring required")
            warnings.append("Consider staged approach")

        # Check for circular dependencies
        for module in affected_modules:
            deps = self.ast_analyzer.module_deps.get(module, None)
            if deps:
                for imp in deps.imports:
                    if imp.module in affected_modules:
                        warnings.append(f"Circular dependency: {module} ↔ {imp.module}")
                        risk_level = "high"

        if warnings:
            print("\n⚠️  Warnings:")
            for warning in warnings:
                print(f"  • {warning}")
        else:
            print("\n✅ No warnings")

        # Phase 4: Rope Preview
        print("\n" + "-" * 80)
        print("🔬 PHASE 4: Detailed Change Preview (Rope)")
        print("-" * 80)

        try:
            self._preview_rope_changes(module_path, new_location)
        except Exception as e:
            print(f"\n⚠️  Could not generate Rope preview: {e}")
            warnings.append(f"Rope preview failed: {e}")

        # Generate plan
        plan = RefactoringPlan(
            operation="move",
            source=module_path,
            destination=new_location,
            risk_level=risk_level,
            affected_modules=affected_modules,
            warnings=warnings
        )

        return plan

    def _preview_rope_changes(self, module_path: str, new_location: str):
        """Generate Rope preview of changes"""
        if not self.rope_project:
            print("⚠️  Rope project not initialized")
            return

        # Convert module path to file
        module_file = module_path.replace(".", "/") + ".py"
        # Get just the filename
        module_name = module_path.split(".")[-1] + ".py"

        try:
            module = self.rope_project.root.get_child(module_name)

            # Create move refactoring
            mover = MoveModule(self.rope_project, module)
            changes = mover.get_changes(new_location)

            print("\n📝 Preview of changes:")
            print(changes.get_description())

            print("\n📄 Files to be modified:")
            for resource in changes.get_changed_resources():
                print(f"  • {resource.path}")

        except Exception as e:
            raise Exception(f"Failed to preview: {e}")

    def generate_execution_plan(self, plan: RefactoringPlan) -> str:
        """
        Generate step-by-step execution plan for the refactoring.
        """
        print("\n" + "=" * 80)
        print("📋 EXECUTION PLAN")
        print("=" * 80)

        steps = []

        # Pre-refactoring
        steps.append("PRE-REFACTORING:")
        steps.append("  1. Ensure all changes are committed")
        steps.append("  2. Create a new branch for refactoring")
        steps.append("  3. Run full test suite to establish baseline")
        steps.append("  4. Generate dependency graph snapshot")

        # Refactoring
        steps.append("\nREFACTORING:")
        steps.append(f"  5. Use Rope to move {plan.source} to {plan.destination}")
        steps.append("  6. Review ALL changes before applying")

        # Update imports
        if plan.affected_modules:
            steps.append("\nUPDATE IMPORTS:")
            for i, module in enumerate(plan.affected_modules, 7):
                steps.append(f"  {i}. Update imports in {module}")

        # Post-refactoring
        next_step = 7 + len(plan.affected_modules)
        steps.append("\nPOST-REFACTORING:")
        steps.append(f"  {next_step}. Run full test suite")
        steps.append(f"  {next_step + 1}. Verify all tests pass")
        steps.append(f"  {next_step + 2}. Generate new dependency graph")
        steps.append(f"  {next_step + 3}. Compare before/after graphs")
        steps.append(f"  {next_step + 4}. Commit changes")

        # Warnings
        if plan.warnings:
            steps.append("\n⚠️  CRITICAL WARNINGS:")
            for warning in plan.warnings:
                steps.append(f"  • {warning}")

        execution_plan = "\n".join(steps)
        print(execution_plan)

        return execution_plan

    def save_report(self, plan: RefactoringPlan, output_file: str = "refactoring_report.md"):
        """Save complete analysis report"""
        report = []

        report.append("# Refactoring Analysis Report")
        report.append(f"\n## Operation: {plan.operation.upper()}")
        report.append(f"- **Source**: `{plan.source}`")
        report.append(f"- **Destination**: `{plan.destination}`")
        report.append(f"- **Risk Level**: **{plan.risk_level.upper()}**")

        report.append("\n## Impact Analysis")
        report.append(f"- **Modules Affected**: {len(plan.affected_modules)}")

        if plan.affected_modules:
            report.append("\n### Affected Modules:")
            for module in plan.affected_modules:
                report.append(f"- `{module}`")

        if plan.warnings:
            report.append("\n## ⚠️ Warnings")
            for warning in plan.warnings:
                report.append(f"- {warning}")

        report.append("\n## Recommendations")

        if plan.risk_level == "low":
            report.append("✅ Safe to proceed with refactoring")
        elif plan.risk_level == "medium":
            report.append("⚠️  Proceed with caution - review all changes carefully")
        else:
            report.append("🚨 High risk - consider alternative approach or staged refactoring")

        report.append("\n## Next Steps")
        report.append("1. Review this report")
        report.append("2. Ensure test coverage is adequate")
        report.append("3. Create feature branch")
        report.append("4. Execute refactoring using Rope")
        report.append("5. Verify all tests pass")
        report.append("6. Code review")
        report.append("7. Merge")

        report_text = "\n".join(report)

        output_path = self.project_root.parent / output_file
        with open(output_path, "w") as f:
            f.write(report_text)

        print(f"\n📄 Report saved to: {output_path}")

        return report_text


def main():
    """Demonstrate the complete workflow"""
    demo_path = Path(__file__).parent / "demo_project"

    if not demo_path.exists():
        print(f"❌ Demo project not found at {demo_path}")
        return

    print("🚀 COMPLETE REFACTORING WORKFLOW DEMONSTRATION")
    print("=" * 80)

    # Example: Moving module_a to a new package
    module_to_move = "demo_project.module_a"
    new_location = "core"

    with RefactoringWorkflow(demo_path) as workflow:
        # Analyze the operation
        plan = workflow.analyze_move_operation(module_to_move, new_location)

        # Generate execution plan
        workflow.generate_execution_plan(plan)

        # Save report
        workflow.save_report(plan)

        # Summary
        print("\n" + "=" * 80)
        print("✅ ANALYSIS COMPLETE")
        print("=" * 80)
        print(f"\n📊 Risk Level: {plan.risk_level.upper()}")
        print(f"📦 Modules Affected: {len(plan.affected_modules)}")

        if plan.risk_level == "low":
            print("\n✅ You can proceed with confidence!")
        elif plan.risk_level == "medium":
            print("\n⚠️  Review the analysis carefully before proceeding")
        else:
            print("\n🚨 Consider breaking this into smaller refactorings")


if __name__ == "__main__":
    main()
