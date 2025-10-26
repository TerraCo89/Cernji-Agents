"""
PyDeps Integration - Dependency Graph Visualization
Demonstrates using pydeps programmatically and via CLI for impact analysis.

Note: This requires 'pydeps' and 'graphviz' to be installed:
    pip install pydeps
    # Also install Graphviz from: https://graphviz.org/download/
"""
import subprocess
import sys
from pathlib import Path
from typing import List, Dict
import json


class PyDepsAnalyzer:
    """Wrapper for pydeps command-line tool"""

    def __init__(self, project_root: Path):
        self.project_root = project_root

    def check_installation(self) -> bool:
        """Check if pydeps and graphviz are installed"""
        try:
            result = subprocess.run(
                ["pydeps", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            pydeps_ok = result.returncode == 0

            dot_result = subprocess.run(
                ["dot", "-V"],
                capture_output=True,
                text=True,
                timeout=5
            )
            graphviz_ok = dot_result.returncode == 0

            return pydeps_ok and graphviz_ok

        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def generate_full_graph(self, output_file: str = "dependency_graph.svg") -> bool:
        """
        Generate a complete dependency graph visualization.

        This is useful for understanding overall project structure.
        """
        print(f"🎨 Generating full dependency graph: {output_file}")

        cmd = [
            "pydeps",
            str(self.project_root),
            "--max-bacon=0",  # Include all dependencies (infinite depth)
            "--cluster",       # Group external dependencies
            f"-o={output_file}",
            "-T=svg"          # SVG format (interactive)
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.project_root.parent,
                timeout=30
            )

            if result.returncode == 0:
                print(f"✅ Graph saved to: {output_file}")
                print(f"📊 Open {output_file} in a browser to view")
                return True
            else:
                print(f"❌ Error: {result.stderr}")
                return False

        except Exception as e:
            print(f"❌ Failed to generate graph: {e}")
            return False

    def generate_reverse_dependency_graph(self, target_module: str, output_file: str = "reverse_deps.svg") -> bool:
        """
        Generate a reverse dependency graph showing what imports the target module.

        CRITICAL FOR REFACTORING: Shows all files that will break if you move/change the module.
        """
        print(f"\n🔄 Generating reverse dependency graph for: {target_module}")

        cmd = [
            "pydeps",
            str(self.project_root),
            "--reverse",       # Show reverse dependencies
            "--only", target_module,  # Focus on target module
            "--max-bacon=0",   # Show all importers
            f"-o={output_file}",
            "-T=svg"
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.project_root.parent,
                timeout=30
            )

            if result.returncode == 0:
                print(f"✅ Reverse dependency graph saved to: {output_file}")
                print(f"📊 This shows ALL modules that import {target_module}")
                return True
            else:
                print(f"❌ Error: {result.stderr}")
                return False

        except Exception as e:
            print(f"❌ Failed to generate reverse graph: {e}")
            return False

    def generate_text_report(self, target_module: str = None) -> Dict:
        """
        Generate a text-based dependency report using pydeps.

        Returns structured data about dependencies.
        """
        print("\n📝 Generating text dependency report...")

        cmd = [
            "pydeps",
            str(self.project_root),
            "--show-deps",     # Show dependency list
            "--nodot",         # Don't generate graph
            "--no-output"      # Don't create output file
        ]

        if target_module:
            cmd.extend(["--only", target_module])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.project_root.parent,
                timeout=30
            )

            if result.returncode == 0:
                print("✅ Report generated")
                print("\n" + result.stdout)
                return {"success": True, "output": result.stdout}
            else:
                print(f"❌ Error: {result.stderr}")
                return {"success": False, "error": result.stderr}

        except Exception as e:
            print(f"❌ Failed to generate report: {e}")
            return {"success": False, "error": str(e)}

    def find_circular_dependencies(self) -> List[str]:
        """
        Detect circular dependencies in the project.

        Circular dependencies can break refactoring operations.
        """
        print("\n🔍 Checking for circular dependencies...")

        cmd = [
            "pydeps",
            str(self.project_root),
            "--show-cycles",   # Show circular dependencies
            "--nodot",
            "--no-output"
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.project_root.parent,
                timeout=30
            )

            output = result.stdout + result.stderr

            if "cycle" in output.lower():
                print("⚠️  Circular dependencies found!")
                print(output)
                return [line for line in output.split("\n") if "cycle" in line.lower()]
            else:
                print("✅ No circular dependencies detected")
                return []

        except Exception as e:
            print(f"❌ Failed to check cycles: {e}")
            return []


def generate_impact_analysis_workflow(project_root: Path, target_module: str):
    """
    Complete workflow for analyzing refactoring impact using pydeps.

    This demonstrates best practices for pre-refactoring analysis.
    """
    print("\n" + "=" * 70)
    print(f"🎯 IMPACT ANALYSIS WORKFLOW: {target_module}")
    print("=" * 70)

    analyzer = PyDepsAnalyzer(project_root)

    # Step 1: Verify installation
    print("\n📋 Step 1: Verifying tools...")
    if not analyzer.check_installation():
        print("❌ pydeps or graphviz not installed!")
        print("\nInstall with:")
        print("  pip install pydeps")
        print("  Download Graphviz: https://graphviz.org/download/")
        return

    print("✅ Tools installed")

    # Step 2: Check for circular dependencies
    print("\n📋 Step 2: Checking for circular dependencies...")
    cycles = analyzer.find_circular_dependencies()
    if cycles:
        print("⚠️  WARNING: Fix circular dependencies before refactoring!")

    # Step 3: Generate full project graph
    print("\n📋 Step 3: Generating full project dependency graph...")
    analyzer.generate_full_graph("before_refactoring_full.svg")

    # Step 4: Generate reverse dependency graph for target
    print("\n📋 Step 4: Generating reverse dependency graph...")
    analyzer.generate_reverse_dependency_graph(
        target_module,
        f"reverse_deps_{target_module.replace('.', '_')}.svg"
    )

    # Step 5: Generate text report
    print("\n📋 Step 5: Generating text report...")
    analyzer.generate_text_report(target_module)

    # Step 6: Summary
    print("\n" + "=" * 70)
    print("📊 ANALYSIS COMPLETE")
    print("=" * 70)
    print("\n✅ Generated files:")
    print("  1. before_refactoring_full.svg - Complete project graph")
    print(f"  2. reverse_deps_{target_module.replace('.', '_')}.svg - Who imports this module")
    print("\n💡 Next steps:")
    print("  1. Open SVG files in browser to visualize dependencies")
    print("  2. Review all modules that import your target")
    print("  3. Plan import statement updates")
    print("  4. Use Rope to preview actual changes")
    print("  5. Apply refactoring")
    print("  6. Generate new graph to verify changes")


def compare_before_after_graphs(project_root: Path):
    """
    Generate before/after dependency graphs to visualize refactoring impact.
    """
    print("\n" + "=" * 70)
    print("📊 BEFORE/AFTER COMPARISON WORKFLOW")
    print("=" * 70)

    analyzer = PyDepsAnalyzer(project_root)

    print("\n1️⃣ Generating BEFORE graph...")
    analyzer.generate_full_graph("before_refactoring.svg")

    print("\n⏸️  Now perform your refactoring...")
    input("Press Enter after completing refactoring to generate AFTER graph...")

    print("\n2️⃣ Generating AFTER graph...")
    analyzer.generate_full_graph("after_refactoring.svg")

    print("\n✅ Comparison ready!")
    print("  - Open before_refactoring.svg and after_refactoring.svg")
    print("  - Compare the graphs side-by-side")
    print("  - Verify dependency changes are as expected")


def main():
    """Main demonstration"""
    demo_path = Path(__file__).parent / "demo_project"

    if not demo_path.exists():
        print(f"❌ Demo project not found at {demo_path}")
        print("Run 01_ast_dependency_analyzer.py first to create the demo project")
        return

    print("🔍 PyDeps Integration for Refactoring Analysis")
    print("=" * 70)

    # Check if running specific command
    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "full":
            analyzer = PyDepsAnalyzer(demo_path)
            analyzer.generate_full_graph()

        elif command == "reverse":
            target = sys.argv[2] if len(sys.argv) > 2 else "demo_project.module_a"
            analyzer = PyDepsAnalyzer(demo_path)
            analyzer.generate_reverse_dependency_graph(target)

        elif command == "cycles":
            analyzer = PyDepsAnalyzer(demo_path)
            analyzer.find_circular_dependencies()

        elif command == "compare":
            compare_before_after_graphs(demo_path)

        else:
            print(f"❌ Unknown command: {command}")
            print("Usage: python 03_pydeps_integration.py [full|reverse|cycles|compare]")

    else:
        # Run full workflow
        target_module = "demo_project.module_a"
        generate_impact_analysis_workflow(demo_path, target_module)


if __name__ == "__main__":
    main()
