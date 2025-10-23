# Astral UV - Python Package and Project Manager Documentation

**Source:** Context7 - `/astral-sh/uv`
**Trust Score:** 9.4
**Code Snippets:** 771
**Generated:** 2025-10-18

## Overview

uv is an extremely fast Python package and project manager written in Rust, designed to replace tools like pip, pip-tools, pipx, poetry, and more, offering 10-100x faster performance.

---

## Quick Start

### Manage Python Project Dependencies and Environments

Source: https://github.com/astral-sh/uv/blob/main/docs/index.md

This example demonstrates a typical project workflow using uv, including initializing a new project, adding dependencies, running project-specific commands, and managing lockfiles.

```console
$ uv init example
Initialized project `example` at `/home/user/example`

$ cd example

$ uv add ruff
Creating virtual environment at: .venv
Resolved 2 packages in 170ms
   Built example @ file:///home/user/example
Prepared 2 packages in 627ms
Installed 2 packages in 1ms
 + example==0.1.0 (from file:///home/user/example)
 + ruff==0.5.4

$ uv run ruff check
All checks passed!

$ uv lock
Resolved 2 packages in 0.33ms

$ uv sync
Resolved 2 packages in 0.70ms
Audited 1 package in 0.02ms
```

---

## Project Initialization

### Initialize New Python Project

```bash
# Create new project with complete structure
uv init hello-world
cd hello-world
```

```bash
# Initialize in existing directory
mkdir my-project && cd my-project
uv init
```

```bash
# Initialize with specific Python version
uv init --python 3.11 my-app
```

### Initialize a Packaged Application Project

```console
uv init --package example-pkg
```

Creates a new packaged application project with:
- `src` directory structure
- `__init__.py` file
- Configured build system in `pyproject.toml`

---

## Dependency Management

### Add Dependencies

```bash
# Add dependencies (updates pyproject.toml, uv.lock, and .venv)
uv add requests
uv add 'flask>=2.0'
uv add 'django>=4.0,<5.0'
```

```bash
# Add development dependencies
uv add --dev pytest pytest-cov black
```

```bash
# Add optional dependency groups
uv add --group docs sphinx sphinx-rtd-theme
```

### Add from Git Repository

```bash
# Add from Git repository
uv add git+https://github.com/psf/requests
uv add git+https://github.com/pallets/flask@main
uv add git+ssh://git@github.com/user/repo.git@v1.0.0
```

```console
# With specific branch
$ uv add git+https://github.com/encode/httpx --branch main
```

```console
# With specific tag
$ uv add git+https://github.com/encode/httpx --tag 0.27.0
```

```console
# With subdirectory
$ uv add git+https://github.com/langchain-ai/langchain#subdirectory=libs/langchain
```

### Add from Local Path

```bash
# Add from local path
uv add --editable ./local-package
uv add ../another-project
```

```console
# Editable local path dependency
$ uv add --editable ../projects/bar/
```

### Add from URL

```bash
# Add from URL
uv add https://files.pythonhosted.org/packages/.../requests-2.31.0.tar.gz
```

### Remove Dependencies

```bash
# Remove dependencies
uv remove requests flask
```

### Migrate from requirements.txt

```bash
# Migrate from requirements.txt
uv add -r requirements.txt
```

---

## Lockfiles and Syncing

### Lock Dependencies

```bash
# Lock without installing (CI/CD)
uv lock
```

```bash
# Lock with upgraded package
uv lock --upgrade-package requests
uv lock --upgrade
```

### Sync Environment

```bash
# Sync environment to lockfile
uv sync
uv sync --frozen  # Don't update lockfile
uv sync --locked  # Error if lockfile out of date
```

---

## pip-compatible Interface

### Install Packages

```console
# Single package
$ uv pip install flask

# Multiple packages
$ uv pip install flask ruff

# From requirements.txt
$ uv pip install -r requirements.txt

# From pyproject.toml
$ uv pip install -r pyproject.toml

# With specific extra
$ uv pip install -r pyproject.toml --extra foo

# With all extras
$ uv pip install -r pyproject.toml --all-extras
```

### Install Dependency Groups

```console
# Specific dependency group
$ uv pip install --group foo

# Multiple groups from current project
$ uv pip install --group foo --group bar

# From specified project path
$ uv pip install --project some/path/ --group foo --group bar

# With explicit pyproject.toml paths
$ uv pip install --group some/path/pyproject.toml:foo --group other/pyproject.toml:bar
```

### Uninstall Packages

```console
# Single package
$ uv pip uninstall flask

# Multiple packages
$ uv pip uninstall flask ruff
```

---

## Compile Requirements

### uv pip compile

```bash
# Compile from pyproject.toml
uv pip compile pyproject.toml -o requirements.txt

# Compile from requirements.in
uv pip compile requirements.in -o requirements.txt

# Universal requirements (cross-platform)
uv pip compile requirements.in --universal

# From setup.py (legacy)
uv pip compile setup.py -o requirements.txt

# Multiple dependency groups from specified project
uv pip compile --project some/path/ --group foo --group bar
```

---

## Running Commands

### uv run

Execute commands within the project's virtual environment:

```console
$ uv run pytest
```

### Run with Temporary Dependencies

```console
# Override dependency versions temporarily
uv run --with httpx==0.26.0 python -c "import httpx; print(httpx.__version__)"
0.26.0
uv run --with httpx==0.25.0 python -c "import httpx; print(httpx.__version__)"
0.25.0
```

---

## Single-File Script Dependencies

### Manage Script Dependencies

```console
$ echo 'import requests; print(requests.get("https://astral.sh"))' > example.py

$ uv add --script example.py requests
Updated `example.py`

$ uv run example.py
Reading inline script metadata from: example.py
Installed 5 packages in 12ms
<Response [200]>
```

---

## Workspaces

### Manage Workspace Packages

```bash
# Build specific workspace package
uv build --package my-package

# Run in workspace context
uv run --package my-package python script.py

# Add dependency to workspace member
cd packages/my-package
uv add requests
```

---

## Cache Management

### Control uv Cache

```bash
# Show cache directory
uv cache dir

# Clean cache
uv cache clean
uv cache clean requests
uv cache clean --force

# Prune unreachable cache entries
uv cache prune
uv cache prune --ci  # Optimize for CI (keep built wheels, remove downloads)

# Cache location:
# Unix: ~/.cache/uv
# macOS: ~/Library/Caches/uv
# Windows: %LOCALAPPDATA%\uv\cache

# Disable cache
uv --no-cache pip install requests

# Custom cache directory
uv --cache-dir /tmp/uv-cache pip install requests
```

---

## pyproject.toml Configuration

### Basic Project Metadata

```toml
[project]
name = "hello-world"
version = "0.1.0"
description = "Add your description here"
readme = "README.md"
dependencies = []
```

### Project Dependencies

```toml
[project]
name = "example"
version = "0.1.0"
dependencies = [
    "fastapi",
    "pydantic>2"
]

[dependency-groups]
dev = ["pytest"]
```

### Build System Dependencies

```toml
[build-system]
requires = ["setuptools"]
build-backend = "setuptools.build_meta"
```

---

## Advanced Configuration

### Package Indexes

Define custom package indexes (PEP 503 compliant):

```toml
[[tool.uv.index]]
name = "pytorch"
url = "https://download.pytorch.org/whl/cu121"
explicit = true

[tool.uv.sources]
torch = { index = "pytorch" }
```

### Dependency Sources

#### Git Sources

```toml
[project]
dependencies = ["httpx"]

[tool.uv.sources]
httpx = { git = "https://github.com/encode/httpx" }
# Or with branch
httpx = { git = "https://github.com/encode/httpx", branch = "main" }
# Or with tag
httpx = { git = "https://github.com/encode/httpx", tag = "0.27.0" }
# Or with subdirectory
langchain = { git = "https://github.com/langchain-ai/langchain", subdirectory = "libs/langchain" }
```

#### URL Sources

```toml
[project]
dependencies = ["httpx"]

[tool.uv.sources]
httpx = { url = "https://files.pythonhosted.org/packages/.../httpx-0.27.0.tar.gz" }
```

#### Path Sources

```toml
[project]
dependencies = ["foo"]

[tool.uv.sources]
foo = { path = "/example/foo-0.1.0-py3-none-any.whl" }
# Or editable
bar = { path = "../projects/bar", editable = true }
```

### Override Dependencies

Force specific package versions:

```toml
[tool.uv]
# Always install Werkzeug 2.3.0, regardless of other requirements
override-dependencies = ["werkzeug==2.3.0"]
```

### Constraint Dependencies

Apply version restrictions:

```toml
[tool.uv]
# Ensure grpcio is always less than 1.65 if requested
constraint-dependencies = ["grpcio<1.65"]
```

### Build Constraint Dependencies

```toml
[tool.uv]
# Ensure setuptools v60.0.0 is used for build dependencies
build-constraint-dependencies = ["setuptools==60.0.0"]
```

### Extra Build Dependencies

```toml
[tool.uv]
extra-build-dependencies = { pytest = ["setuptools"] }
```

```toml
[tool.uv.extra-build-dependencies]
cchardet = ["cython"]
```

### Dependency Metadata

Provide pre-defined static metadata:

```toml
[tool.uv]
dependency-metadata = [
    { name = "flask", version = "1.0.0", "requires-dist" = ["werkzeug"], "requires-python" = ">=3.6" },
]
```

### Development Dependencies

```toml
[tool.uv]
dev-dependencies = ["ruff==0.5.0"]
```

Note: `dependency-groups.dev` is now the recommended standard.

### Package Configuration

Mark project as non-package (virtual):

```toml
[tool.uv]
package = false
```

### Disable Build Isolation

```toml
[tool.uv]
no-build-isolation-package = ["package1", "package2"]
```

### Resolution Strategy

```toml
[tool.uv]
resolution = "lowest-direct"
# Options: "highest" (default), "lowest", "lowest-direct"
```

### Config Settings per Package

```toml
[tool.uv]
config-settings-package = { numpy = { editable_mode = "compat" } }
```

### Cache Keys

```toml
[tool.uv]
cache-keys = [{ file = "pyproject.toml" }, { file = "requirements.txt" }]
```

### Exclude Newer Packages

```toml
[tool.uv]
exclude-newer-package = { tqdm = "2022-04-04T00:00:00Z" }
```

---

## Workspaces Configuration

### Path Dependencies

```toml
[project]
name = "albatross"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = ["bird-feeder", "tqdm>=4,<5"]

[tool.uv.sources]
bird-feeder = { path = "packages/bird-feeder" }

[build-system]
requires = ["uv_build>=0.9.2,<0.10.0"]
build-backend = "uv_build"
```

### Workspace Members

```toml
[project]
name = "uv-aws-lambda-example"
version = "0.1.0"
requires-python = ">=3.13"
dependencies = [
    "fastapi",
    "library",
    "mangum",
]

[dependency-groups]
dev = [
    "fastapi[standard]",
]

[tool.uv.workspace]
members = ["library"]

[tool.uv.sources]
lib = { workspace = true }
```

---

## pip-specific Settings

### Include Extras

```toml
[tool.uv.pip]
extra = ["dev", "docs"]
```

### Include All Extras

```toml
[tool.uv.pip]
all-extras = true
```

### Dependency Groups

```toml
[tool.uv.pip]
group = ["dev", "docs"]
```

### No Dependencies

```toml
[tool.uv.pip]
no-deps = true
```

### No Build Isolation

```toml
[tool.uv.pip]
no-build-isolation-package = ["package1", "package2"]
```

### Extra Build Dependencies

```toml
[tool.uv.pip]
extra-build-dependencies = { pytest = ["setuptools"] }
```

---

## Advanced Build Configuration

### Disable Build Isolation with Manual Dependencies

```toml
[project]
name = "project"
version = "0.1.0"
description = "..."
readme = "README.md"
requires-python = ">=3.12"
dependencies = ["cchardet", "cython", "setuptools"]

[tool.uv]
no-build-isolation-package = ["cchardet"]
```

### Isolate Build Dependencies using Optional Dependencies

```toml
[project]
name = "project"
version = "0.1.0"
description = "..."
readme = "README.md"
requires-python = ">=3.12"
dependencies = ["cchardet"]

[project.optional-dependencies]
build = ["setuptools", "cython"]

[tool.uv]
no-build-isolation-package = ["cchardet"]
```

Then sync with:

```console
uv sync --extra build
 + cchardet==2.1.7
 + cython==3.1.3
 + setuptools==80.9.0
uv sync
 - cython==3.1.3
 - setuptools==80.9.0
```

### Provide Upfront Metadata

```toml
[[tool.uv.dependency-metadata]]
name = "flash-attn"
version = "2.6.3"
requires-dist = ["torch", "einops"]
```

### Configure for Axolotl with Specific Torch Version

```toml
[project]
name = "project"
version = "0.1.0"
description = "..."
readme = "README.md"
requires-python = ">=3.12"
dependencies = ["axolotl[deepspeed, flash-attn]", "torch==2.6.0"]

[tool.uv.extra-build-dependencies]
axolotl = ["torch==2.6.0"]
deepspeed = ["torch==2.6.0"]
flash-attn = ["torch==2.6.0"]
```

### Match Runtime Build Dependencies

```toml
[project]
name = "project"
version = "0.1.0"
description = "..."
readme = "README.md"
requires-python = ">=3.12"
dependencies = ["deep_gemm", "torch"]

[tool.uv.sources]
deep_gemm = { git = "https://github.com/deepseek-ai/DeepGEMM" }

[tool.uv.extra-build-dependencies]
deep_gemm = [{ requirement = "torch", match-runtime = true }]
```

---

## Docker Integration

### Dockerfile with uv

```dockerfile
# Dockerfile with uv
FROM python:3.11-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml uv.lock ./
COPY src/ ./src/

# Install dependencies
RUN uv sync --frozen --no-dev --no-install-project

# Copy application code
COPY . .

# Install project
RUN uv sync --frozen --no-dev

# Run application
CMD ["uv", "run", "python", "-m", "app"]
```

---

## Jupyter & Marimo Integration

### Add uv as Dev Dependency for Notebooks

```console
uv add --dev uv
```

This allows direct manipulation of dependencies from within notebooks using `!uv` commands.

### Manage Marimo Notebook Dependencies

```console
# Add dependency to notebook
uv add --script my_notebook.py numpy

# Edit in sandboxed environment
uvx marimo edit --sandbox my_notebook.py

# Run notebook as script
uv run my_notebook.py
```

---

## Migration from pip

### Basic Migration Steps

1. Initialize uv project:
```console
uv init
```

2. Add dependencies from requirements.txt:
```console
uv add -r requirements.txt
```

3. Add development dependencies:
```console
uv add -r requirements-dev.txt --dev
```

4. Add custom group dependencies:
```console
uv add -r requirements-docs.in -c requirements-docs.txt --group docs
```

5. Run commands:
```console
uv run pytest
```

---

## Legacy Installation (Without Build Isolation)

```console
uv venv
uv pip install cython setuptools
uv pip install cchardet --no-build-isolation
```

---

## Key Concepts

### Resolution Strategies

- **highest** (default): Select the highest compatible version
- **lowest**: Select the lowest compatible version
- **lowest-direct**: Select lowest for direct dependencies, highest for transitive

### Package Types

- **Regular package**: Has `build-system`, built and installed
- **Virtual project** (`package = false`): Only dependencies installed, project itself not built

### Build Isolation

By default, uv builds packages in isolation. You can disable this for specific packages that need access to environment dependencies during build.

---

## Performance

- **10-100x faster** than pip
- Written in Rust for speed
- Optimized dependency resolution
- Smart caching strategy

---

## References

- GitHub: https://github.com/astral-sh/uv
- Documentation: https://docs.astral.sh/uv/
- Context7 ID: `/astral-sh/uv`
