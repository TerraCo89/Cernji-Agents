# validate-changes.ps1 - Run after code changes
# Part of the test-after-changes skill

$ErrorActionPreference = "Stop"

Write-Host "🔍 Post-Change Validation" -ForegroundColor Cyan
Write-Host "========================" -ForegroundColor Cyan

# Determine project root
if (Test-Path "pyproject.toml") {
    $ProjectRoot = "."
} elseif (Test-Path "..\pyproject.toml") {
    $ProjectRoot = ".."
} elseif (Test-Path "..\..\pyproject.toml") {
    $ProjectRoot = "..\.."
} else {
    $ProjectRoot = "."
}

Write-Host "Project root: $ProjectRoot"

# 1. Syntax Check
Write-Host "`n1️⃣  Checking Python syntax..." -ForegroundColor Yellow
try {
    $result = python -m compileall -q $ProjectRoot 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Syntax check passed" -ForegroundColor Green
    } else {
        Write-Host "❌ Syntax errors found" -ForegroundColor Red
        Write-Host $result
        exit 1
    }
} catch {
    Write-Host "❌ Syntax check failed: $_" -ForegroundColor Red
    exit 1
}

# 2. Import Analysis (Static)
Write-Host "`n2️⃣  Checking imports with ruff..." -ForegroundColor Yellow
if (Get-Command ruff -ErrorAction SilentlyContinue) {
    try {
        ruff check --select F401,F811,F821,E999 $ProjectRoot --quiet
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Import analysis passed" -ForegroundColor Green
        } else {
            Write-Host "❌ Import issues found" -ForegroundColor Red
            ruff check --select F401,F811,F821,E999 $ProjectRoot
            exit 1
        }
    } catch {
        Write-Host "❌ Import analysis failed: $_" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "⚠️  ruff not installed, skipping static import analysis" -ForegroundColor Yellow
}

# 3. Test Collection (Dynamic Import Check)
Write-Host "`n3️⃣  Testing imports with pytest collection..." -ForegroundColor Yellow
if (Get-Command pytest -ErrorAction SilentlyContinue) {
    try {
        $testOutput = pytest --collect-only -q 2>&1
        if ($testOutput -match "error|Error|ERROR") {
            Write-Host "❌ Test collection failed (import errors)" -ForegroundColor Red
            Write-Host $testOutput
            exit 1
        } else {
            Write-Host "✅ Test collection passed" -ForegroundColor Green
        }
    } catch {
        Write-Host "⚠️  Test collection encountered issues" -ForegroundColor Yellow
    }
} else {
    Write-Host "⚠️  pytest not installed, skipping collection check" -ForegroundColor Yellow
}

# 4. Critical Module Imports
Write-Host "`n4️⃣  Testing critical module imports..." -ForegroundColor Yellow

$currentDir = Get-Location

# Check if we're in resume-agent-langgraph
if (Test-Path "apps\resume-agent-langgraph\graph_registry.py") {
    Set-Location "apps\resume-agent-langgraph"
    try {
        $importTest = python -c "from graph_registry import list_graphs; print('Available graphs:', list_graphs())" 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Graph registry imports OK" -ForegroundColor Green
            Write-Host $importTest
        } else {
            Write-Host "❌ Graph registry import failed" -ForegroundColor Red
            Write-Host $importTest
            Set-Location $currentDir
            exit 1
        }
    } catch {
        Write-Host "❌ Graph registry import failed: $_" -ForegroundColor Red
        Set-Location $currentDir
        exit 1
    }
    Set-Location $currentDir
} elseif (Test-Path "graph_registry.py") {
    try {
        $importTest = python -c "from graph_registry import list_graphs; print('Available graphs:', list_graphs())" 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Graph registry imports OK" -ForegroundColor Green
            Write-Host $importTest
        } else {
            Write-Host "❌ Graph registry import failed" -ForegroundColor Red
            Write-Host $importTest
            exit 1
        }
    } catch {
        Write-Host "❌ Graph registry import failed: $_" -ForegroundColor Red
        exit 1
    }
}

# 5. Run Tests
Write-Host "`n5️⃣  Running test suite..." -ForegroundColor Yellow
if (Get-Command pytest -ErrorAction SilentlyContinue) {
    try {
        pytest -q --tb=short
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ All tests passed" -ForegroundColor Green
        } else {
            Write-Host "❌ Some tests failed" -ForegroundColor Red
            exit 1
        }
    } catch {
        Write-Host "❌ Test execution failed: $_" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "⚠️  pytest not installed, skipping test execution" -ForegroundColor Yellow
}

Write-Host "`n========================" -ForegroundColor Cyan
Write-Host "✅ All validations passed!" -ForegroundColor Green
Write-Host "========================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Changes are safe to commit." -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  git add ." -ForegroundColor White
Write-Host "  git commit -m `"your commit message`"" -ForegroundColor White
