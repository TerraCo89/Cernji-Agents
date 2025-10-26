# Sources and Documentation

This document lists all sources, documentation, and references used in the refactoring analysis research.

## Official Documentation

### Python AST (Abstract Syntax Trees)
- **Official Documentation**: https://docs.python.org/3/library/ast.html
- **Description**: Python's built-in module for parsing Python source code into an abstract syntax tree
- **Key Classes**: `ast.parse()`, `ast.NodeVisitor`, `ast.Import`, `ast.ImportFrom`

### Rope - Python Refactoring Library
- **GitHub Repository**: https://github.com/python-rope/rope
- **Official Documentation**: https://rope.readthedocs.io/en/latest/
- **Library Usage Guide**: https://rope.readthedocs.io/en/latest/library.html
- **PyPI Package**: https://pypi.org/project/rope/
- **Description**: Advanced Python refactoring library with preview capabilities
- **Current Version**: 1.14.0+

### PyDeps - Dependency Graph Visualization
- **GitHub Repository**: https://github.com/thebjorn/pydeps
- **Official Documentation**: https://pydeps.readthedocs.io/en/latest/
- **PyPI Package**: https://pypi.org/project/pydeps/
- **Description**: Python module dependency visualization tool using Graphviz
- **Current Version**: 1.12.0+

### import-linter - Import Architecture Rules
- **GitHub Repository**: https://github.com/seddonym/import-linter
- **Official Documentation**: https://import-linter.readthedocs.io/
- **PyPI Package**: https://pypi.org/project/import-linter/
- **Description**: Define and enforce architectural boundaries in Python projects
- **Current Version**: 2.5.2+ (as of 2025)

## Key Articles and Tutorials

### Refactoring Best Practices
1. **"Python Refactoring: Techniques, Tools, and Best Practices"**
   - Source: CodeSee Learning Center
   - URL: https://www.codesee.io/learning-center/python-refactoring
   - Topics: Refactoring techniques, tool comparisons, workflow best practices

2. **"Refactoring Python Applications for Simplicity"**
   - Source: Real Python
   - URL: https://realpython.com/python-refactoring/
   - Topics: Code smells, refactoring patterns, testing strategies

3. **"8 Python Code Refactoring Techniques: Tools & Practices"**
   - Source: Qodo.ai
   - URL: https://www.qodo.ai/blog/8-python-code-refactoring-techniques-tools-practices/
   - Topics: Specific refactoring techniques and their implementation

### AST-Based Analysis
4. **"Using Python AST to resolve dependencies"**
   - Author: Gaurav Sarma
   - Source: Medium
   - URL: https://gauravsarma1992.medium.com/using-python-ast-to-resolve-dependencies-c849bd184020
   - Topics: Programmatic dependency resolution using Python's AST module

5. **"Analyzing Python Code with Python"**
   - Author: Rotem Tamir
   - URL: https://rotemtam.com/2020/08/13/python-ast/
   - Topics: AST fundamentals, code analysis patterns

6. **"Learn Python ASTs by building your own linter"**
   - Source: DeepSource Blog
   - URL: https://deepsource.com/blog/python-asts-by-building-your-own-linter
   - Topics: Practical AST usage, building static analysis tools

### Dependency Visualization
7. **"Visualize dependencies between Python Modules"**
   - Author: Sambasivarao. K
   - Source: Medium (ILLUMINATION)
   - URL: https://medium.com/illumination/visualize-dependencies-between-python-modules-d6e8e9a92c50
   - Topics: PyDeps usage, dependency graph interpretation

8. **"Pydeps — See your Python Dependency Graph"**
   - Source: Medium (Short Bits)
   - URL: https://medium.com/short-bits/pydeps-see-your-python-dependency-graph-b285ef840375
   - Topics: PyDeps installation, command-line usage

9. **"pydeps: Python Module Dependency Visualization"**
   - Source: CodeCut.ai
   - URL: https://codecut.ai/pydeps-python-module-dependency-visualization/
   - Topics: Automated documentation with dependency graphs

### Import Architecture
10. **"6 ways to improve the architecture of your Python project (using import-linter)"**
    - Author: Piglei
    - URL: https://www.piglei.com/articles/en-6-ways-to-improve-the-arch-of-you-py-project/
    - Topics: Architectural patterns, import rules, contract types

11. **"Meet Import Linter"**
    - Author: David Seddon
    - URL: https://seddonym.me/2019/05/20/meet-import-linter/
    - Topics: Introduction to import-linter, use cases

12. **"Enforce import rules using the Python import linter"**
    - Source: The Rubber Ducker's Guide to Computing
    - URL: https://921kiyo.com/python-import-linter/
    - Topics: Configuration, contract types, CI/CD integration

## Stack Overflow References

### AST Analysis
13. **"Simple example of how to use ast.NodeVisitor?"**
    - URL: https://stackoverflow.com/questions/1515357/simple-example-of-how-to-use-ast-nodevisitor
    - Topics: Basic NodeVisitor patterns, visitor methods

14. **"Return a list of imported Python modules used in a script?"**
    - URL: https://stackoverflow.com/questions/2572582/return-a-list-of-imported-python-modules-used-in-a-script
    - Topics: Extracting imports programmatically

15. **"Python easy way to read all import statements from py module"**
    - URL: https://stackoverflow.com/questions/9008451/python-easy-way-to-read-all-import-statements-from-py-module
    - Topics: Import parsing techniques

### Dependency Analysis
16. **"Build a dependency graph in python"**
    - URL: https://stackoverflow.com/questions/14242295/build-a-dependency-graph-in-python
    - Topics: Graph construction, dependency tracking

17. **"Analyse python project imports"**
    - URL: https://stackoverflow.com/questions/8063309/analyse-python-project-imports
    - Topics: Project-wide import analysis

### Reverse Dependencies
18. **"How to find reverse dependency on python package"**
    - URL: https://stackoverflow.com/questions/28214608/how-to-find-reverse-dependency-on-python-package
    - Topics: Finding what imports a module, pipdeptree usage

19. **"show reverse dependencies with pip?"**
    - URL: https://stackoverflow.com/questions/21336323/show-reverse-dependencies-with-pip
    - Topics: Package-level reverse dependencies

### Rope Usage
20. **"How to Refactor Module using python rope?"**
    - URL: https://stackoverflow.com/questions/59117255/how-to-refactor-module-using-python-rope
    - Topics: Rope API usage, common refactoring operations

21. **"What refactoring tools do you use for Python?"**
    - URL: https://stackoverflow.com/questions/28796/what-refactoring-tools-do-you-use-for-python
    - Topics: Tool comparisons, community recommendations

## Alternative Tools and Libraries

### Refactoring Tools
22. **Bowler - Safe Code Refactoring**
    - Website: https://pybowler.io/
    - GitHub: https://github.com/facebookincubator/Bowler
    - Description: Safe, large-scale refactoring with query syntax
    - Best for: Command-line batch refactorings

23. **Sourcery - AI-Powered Refactoring**
    - Website: https://sourcery.ai/
    - Blog: https://sourcery.ai/blog/sourcery-vscode
    - Description: Real-time refactoring suggestions in VS Code
    - Best for: IDE integration, automated suggestions

24. **refactor - AST-based Toolkit**
    - GitHub: https://github.com/isidentical/refactor
    - Description: Fragmental source code refactoring toolkit
    - Best for: Custom refactoring scripts

### Static Analysis
25. **findimports - Import Analysis**
    - GitHub: https://github.com/mgedmin/findimports
    - PyPI: https://pypi.org/project/findimports/
    - Description: Static analysis of Python import statements
    - Note: Maintainer recommends Pyflakes and pydeps for production use

26. **Pyflakes - Unused Import Detection**
    - GitHub: https://github.com/PyCQA/pyflakes
    - Description: Fast, simple static analysis for common errors

27. **pipdeptree - Package Dependencies**
    - GitHub: https://github.com/tox-dev/pipdeptree
    - PyPI: https://pypi.org/project/pipdeptree/
    - Description: Display package dependencies as a tree

## GitHub Resources

28. **Python Linters and Code Analysis - Curated List**
    - URL: https://github.com/vintasoftware/python-linters-and-code-analysis
    - Description: Comprehensive list of Python analysis tools

29. **Refactoring Tools - GitHub Topic**
    - URL: https://github.com/topics/refactoring-tools?l=python
    - Description: Collection of Python refactoring tools

## External Dependencies

### Graphviz
- **Website**: https://graphviz.org/
- **Download**: https://graphviz.org/download/
- **Description**: Graph visualization software (required for PyDeps)
- **Installation**:
  - macOS: `brew install graphviz`
  - Ubuntu/Debian: `sudo apt-get install graphviz`
  - Windows: Download installer from website

## Code Examples Used

### Template for Visiting All Python AST Nodes
- **GitHub Gist**: https://gist.github.com/jtpio/cb30bca7abeceae0234c9ef43eec28b4
- Description: Complete template showing all visit methods

### Python NodeVisitor Examples
- **ProgramCreek**: https://www.programcreek.com/python/example/53935/ast.NodeVisitor
- Description: Collection of real-world NodeVisitor examples

## Tutorials and Guides

### PyDeps Tutorials
30. **pydoit - Tutorial on Python imports graph**
    - URL: https://pydoit.org/tutorial-1.html
    - Topics: Building dependency graphs with pydoit and pydeps

31. **"A Simple Python NodeVisitor Example"**
    - Source: Code Monkey Tips Blog
    - URL: https://codemonkeytips.blogspot.com/2010/08/simple-python-nodevisitor-example.html
    - Topics: Basic AST visitor patterns

### Rope Tutorials
32. **"Rope - Python for Data Science"**
    - URL: https://www.python4data.science/en/24.3.0/productive/qa/rope.html
    - Topics: Rope integration in data science workflows

## IDE Integration

### VS Code
33. **"Linting Python in Visual Studio Code"**
    - URL: https://code.visualstudio.com/docs/python/linting
    - Topics: Configuring linters, refactoring tools in VS Code

### ropevim
34. **ropevim - Vim Integration**
    - GitHub: https://github.com/python-rope/ropevim
    - Description: Vim mode using Rope library

### ropemacs
35. **ropemacs - Emacs Integration**
    - GitHub: https://github.com/python-rope/ropemacs
    - Description: Emacs mode using Rope library

## Academic and Research Papers

### Abstract Syntax Trees
36. **"Working on the Tree" - Green Tree Snakes Documentation**
    - URL: https://greentreesnakes.readthedocs.io/en/latest/manipulating.html
    - Topics: AST manipulation, transformation patterns

## Issue Trackers and Discussions

37. **"Draw module internal dependencies" - PyDeps Issue #42**
    - URL: https://github.com/thebjorn/pydeps/issues/42
    - Topics: Internal vs external dependency visualization

## Package Registries

### PyPI Packages
- **rope**: https://pypi.org/project/rope/
- **pydeps**: https://pypi.org/project/pydeps/
- **import-linter**: https://pypi.org/project/import-linter/
- **findimports**: https://pypi.org/project/findimports/
- **pipdeptree**: https://pypi.org/project/pipdeptree/

## Additional Resources

### What is ast.NodeVisitor in Python?
38. **how.dev Tutorial**
    - URL: https://how.dev/answers/what-is-astnodevisitor-in-python
    - Topics: NodeVisitor fundamentals, common patterns

### Quick Python Refactoring Tips
39. **Python Engineer Blog**
    - URL: https://www.python-engineer.com/posts/python-refactoring-tips/
    - Topics: Quick refactoring wins, common patterns

## Version Information

All sources accessed and verified as of **January 2025**.

### Tool Versions Referenced
- Python: 3.8+ (AST features)
- rope: 1.14.0+
- pydeps: 1.12.0+
- import-linter: 2.5.2+ (Oct 2025 release)
- Graphviz: Latest stable

## Research Methodology

This research was conducted using:
1. **Web search** for current best practices and tools (2025)
2. **Official documentation** review for technical accuracy
3. **Stack Overflow** for real-world usage patterns
4. **GitHub repositories** for code examples and issue discussions
5. **Technical blogs** for practical tutorials
6. **Community recommendations** for tool selection

## Key Findings Summary

### Most Recommended Tools
1. **AST module** - Built-in, fast, no dependencies
2. **Rope** - Industry standard for refactoring
3. **PyDeps** - Best for visualization
4. **import-linter** - Best for architecture enforcement

### Common Workflow
1. Use AST for quick analysis
2. Use PyDeps for visualization
3. Use Rope for safe refactoring
4. Use import-linter for ongoing enforcement

### Alternatives Considered
- **Bowler**: Good for large-scale batch refactoring
- **Sourcery**: Good for IDE integration
- **findimports**: Less maintained, use Pyflakes instead
- **snakefood**: Not actively maintained

## License Information

All referenced tools are open source:
- **rope**: LGPL v3
- **pydeps**: BSD-2-Clause
- **import-linter**: BSD-2-Clause
- **AST module**: Python Software Foundation License

---

*Last Updated: January 2025*
