#!/bin/bash
# validate-changes.sh - Run after code changes
# Part of the test-after-changes skill

set -e  # Exit on first error

echo "🔍 Post-Change Validation"
echo "========================"

# Determine if we're in project root or subdirectory
if [ -f "pyproject.toml" ]; then
    PROJECT_ROOT="."
elif [ -f "../pyproject.toml" ]; then
    PROJECT_ROOT=".."
elif [ -f "../../pyproject.toml" ]; then
    PROJECT_ROOT="../.."
else
    PROJECT_ROOT="."
fi

echo "Project root: $PROJECT_ROOT"

# 1. Syntax Check
echo -e "\n1️⃣  Checking Python syntax..."
if python -m compileall -q "$PROJECT_ROOT"; then
    echo "✅ Syntax check passed"
else
    echo "❌ Syntax errors found"
    exit 1
fi

# 2. Import Analysis (Static)
echo -e "\n2️⃣  Checking imports with ruff..."
if command -v ruff &> /dev/null; then
    if ruff check --select F401,F811,F821,E999 "$PROJECT_ROOT" --quiet; then
        echo "✅ Import analysis passed"
    else
        echo "❌ Import issues found"
        ruff check --select F401,F811,F821,E999 "$PROJECT_ROOT"
        exit 1
    fi
else
    echo "⚠️  ruff not installed, skipping static import analysis"
fi

# 3. Test Collection (Dynamic Import Check)
echo -e "\n3️⃣  Testing imports with pytest collection..."
if command -v pytest &> /dev/null; then
    if pytest --collect-only -q 2>&1 | grep -q "error\|Error\|ERROR"; then
        echo "❌ Test collection failed (import errors)"
        pytest --collect-only -q
        exit 1
    else
        echo "✅ Test collection passed"
    fi
else
    echo "⚠️  pytest not installed, skipping collection check"
fi

# 4. Critical Module Imports
echo -e "\n4️⃣  Testing critical module imports..."

# Check if we're in resume-agent-langgraph
if [ -f "apps/resume-agent-langgraph/graph_registry.py" ]; then
    cd apps/resume-agent-langgraph
    if python -c "from graph_registry import list_graphs; print('Available graphs:', list_graphs())" 2>&1; then
        echo "✅ Graph registry imports OK"
    else
        echo "❌ Graph registry import failed"
        exit 1
    fi
    cd - > /dev/null
elif [ -f "graph_registry.py" ]; then
    if python -c "from graph_registry import list_graphs; print('Available graphs:', list_graphs())" 2>&1; then
        echo "✅ Graph registry imports OK"
    else
        echo "❌ Graph registry import failed"
        exit 1
    fi
fi

# 5. Run Tests
echo -e "\n5️⃣  Running test suite..."
if command -v pytest &> /dev/null; then
    if pytest -q --tb=short; then
        echo "✅ All tests passed"
    else
        echo "❌ Some tests failed"
        exit 1
    fi
else
    echo "⚠️  pytest not installed, skipping test execution"
fi

echo -e "\n========================"
echo "✅ All validations passed!"
echo "========================"
echo ""
echo "Changes are safe to commit."
echo ""
echo "Next steps:"
echo "  git add ."
echo "  git commit -m \"your commit message\""
