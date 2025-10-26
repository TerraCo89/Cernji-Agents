"""
Rope Library - Preview Refactoring Changes
Demonstrates how to preview changes before applying refactorings.

This is essential for "dry-run" refactoring - see what will change before committing.
"""
from pathlib import Path
from rope.base.project import Project
from rope.refactor.rename import Rename
from rope.refactor.move import MoveModule, create_move
from rope.base import libutils
import sys


def setup_demo_project() -> Path:
    """Get the demo project path"""
    demo_path = Path(__file__).parent / "demo_project"

    if not demo_path.exists():
        raise FileNotFoundError(f"Demo project not found at {demo_path}")

    return demo_path


def preview_rename_class(project: Project):
    """
    Preview renaming a class across the entire project.

    This shows all files that will be modified and the exact changes.
    """
    print("\n" + "=" * 70)
    print("📝 PREVIEW: Renaming ClassA to ClassAlpha")
    print("=" * 70)

    # Get the module and find the class
    module = project.root.get_child("module_a.py")

    # Find the offset of ClassA definition
    source = module.read()
    class_offset = source.index("class ClassA")

    # Create the rename refactoring
    renamer = Rename(project, module, class_offset)

    try:
        # Get changes WITHOUT applying them
        changes = renamer.get_changes("ClassAlpha")

        # Preview 1: Simple description
        print("\n📋 Change Description:")
        print(changes.get_description())

        # Preview 2: Detailed changes
        print("\n📄 Files that will be modified:")
        for resource in changes.get_changed_resources():
            print(f"  - {resource.path}")

        # Preview 3: Show actual diffs
        print("\n🔍 Detailed Changes:")
        print("-" * 70)
        for change in changes.changes:
            print(f"\nFile: {change.resource.path}")
            print(change.get_description())

        print("\n" + "=" * 70)
        print("✅ Preview complete - NO CHANGES APPLIED")
        print("=" * 70)

        return changes

    except Exception as e:
        print(f"❌ Error during preview: {e}")
        return None


def preview_move_function(project: Project):
    """
    Preview moving a function to another module.

    Shows what imports need updating.
    """
    print("\n" + "=" * 70)
    print("📦 PREVIEW: Moving function_a from module_a to module_c")
    print("=" * 70)

    try:
        # Get source module
        module_a = project.root.get_child("module_a.py")
        source = module_a.read()

        # Find the function definition
        func_offset = source.index("def function_a")

        # Get destination module
        module_c = project.root.get_child("module_c.py")

        # Create move refactoring
        mover = create_move(project, module_a, func_offset)

        # Get changes
        changes = mover.get_changes(module_c)

        # Preview the changes
        print("\n📋 Change Description:")
        print(changes.get_description())

        print("\n📄 Files that will be modified:")
        for resource in changes.get_changed_resources():
            print(f"  - {resource.path}")

        print("\n🔍 Detailed Changes:")
        print("-" * 70)
        for change in changes.changes:
            print(f"\nFile: {change.resource.path}")
            print(change.get_description())

        print("\n" + "=" * 70)
        print("✅ Preview complete - NO CHANGES APPLIED")
        print("=" * 70)

        return changes

    except Exception as e:
        print(f"❌ Error during preview: {e}")
        import traceback
        traceback.print_exc()
        return None


def preview_move_module(project: Project):
    """
    Preview moving an entire module to a new package.

    This is the most complex refactoring - affects all importers.
    """
    print("\n" + "=" * 70)
    print("🚚 PREVIEW: Moving module_a to a new package 'core'")
    print("=" * 70)

    try:
        # Get the module to move
        module_a = project.root.get_child("module_a.py")

        # Create destination directory path
        dest_path = "core"

        # Create MoveModule refactoring
        mover = MoveModule(project, module_a)

        # Get changes
        changes = mover.get_changes(dest_path)

        # Preview
        print("\n📋 Change Description:")
        print(changes.get_description())

        print("\n📄 Files that will be modified:")
        for resource in changes.get_changed_resources():
            print(f"  - {resource.path}")

        print("\n🔍 Impact Summary:")
        print(f"  - Module will move: module_a.py → {dest_path}/module_a.py")
        print(f"  - All imports of 'demo_project.module_a' will update")
        print(f"  - New import path: 'demo_project.core.module_a'")

        print("\n" + "=" * 70)
        print("✅ Preview complete - NO CHANGES APPLIED")
        print("=" * 70)

        return changes

    except Exception as e:
        print(f"❌ Error during preview: {e}")
        import traceback
        traceback.print_exc()
        return None


def analyze_refactoring_impact(project: Project, changes):
    """
    Analyze the impact of proposed changes.

    This function shows additional metadata about the refactoring.
    """
    if not changes:
        print("No changes to analyze")
        return

    print("\n" + "=" * 70)
    print("📊 IMPACT ANALYSIS")
    print("=" * 70)

    # Count files affected
    affected_files = changes.get_changed_resources()
    print(f"\n✓ Files affected: {len(affected_files)}")

    # Categorize changes
    print("\n📁 Breakdown by file:")
    for resource in affected_files:
        # Get file extension
        ext = Path(resource.path).suffix
        print(f"  {resource.path} ({ext})")

    # Warning level
    if len(affected_files) > 5:
        print("\n⚠️  HIGH IMPACT: Many files affected - review carefully!")
    elif len(affected_files) > 2:
        print("\n⚠️  MEDIUM IMPACT: Multiple files affected")
    else:
        print("\n✅ LOW IMPACT: Few files affected")

    print("\n💡 Recommended next steps:")
    print("  1. Review all changes above")
    print("  2. Run tests in current state")
    print("  3. Apply changes: project.do(changes)")
    print("  4. Run tests again to verify")
    print("  5. Commit if all tests pass")


def interactive_preview_mode(project: Project):
    """
    Interactive mode - choose what to preview.
    """
    print("\n" + "=" * 70)
    print("🎯 ROPE REFACTORING PREVIEW TOOL")
    print("=" * 70)
    print("\nWhat would you like to preview?")
    print("  1. Rename ClassA → ClassAlpha")
    print("  2. Move function_a to module_c")
    print("  3. Move module_a to new package 'core'")
    print("  4. Show all (run all previews)")
    print("  0. Exit")

    choice = input("\nEnter choice (0-4): ").strip()

    changes = None

    if choice == "1":
        changes = preview_rename_class(project)
    elif choice == "2":
        changes = preview_move_function(project)
    elif choice == "3":
        changes = preview_move_module(project)
    elif choice == "4":
        preview_rename_class(project)
        preview_move_function(project)
        preview_move_module(project)
        return
    elif choice == "0":
        print("\n👋 Goodbye!")
        return
    else:
        print("\n❌ Invalid choice")
        return

    if changes:
        analyze_refactoring_impact(project, changes)

        # Ask if they want to apply
        apply = input("\n🚀 Apply these changes? (yes/no): ").strip().lower()
        if apply == "yes":
            try:
                project.do(changes)
                print("\n✅ Changes applied successfully!")
                print("⚠️  Remember to run tests!")
            except Exception as e:
                print(f"\n❌ Error applying changes: {e}")
        else:
            print("\n❌ Changes discarded - project unchanged")


def main():
    """Main demonstration"""
    try:
        demo_path = setup_demo_project()
        print(f"📂 Opening project: {demo_path}")

        # Create Rope project
        project = Project(str(demo_path))

        try:
            # Run in interactive mode if no arguments
            if len(sys.argv) == 1:
                interactive_preview_mode(project)
            else:
                # Run specific demo
                if sys.argv[1] == "rename":
                    changes = preview_rename_class(project)
                    analyze_refactoring_impact(project, changes)
                elif sys.argv[1] == "move-func":
                    changes = preview_move_function(project)
                    analyze_refactoring_impact(project, changes)
                elif sys.argv[1] == "move-module":
                    changes = preview_move_module(project)
                    analyze_refactoring_impact(project, changes)
                else:
                    print(f"Unknown command: {sys.argv[1]}")
                    print("Usage: python 02_rope_preview_refactoring.py [rename|move-func|move-module]")

        finally:
            project.close()

    except FileNotFoundError as e:
        print(f"❌ {e}")
        print("Make sure to run 01_ast_dependency_analyzer.py first to create demo project")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
