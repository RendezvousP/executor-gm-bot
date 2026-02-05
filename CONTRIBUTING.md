# CONTRIBUTING TO EXECUTOR GM BOT

Thank you for your interest in contributing to EXECUTOR! This document provides guidelines for contributing to the project.

---

## 🚀 Quick Start

1. **Fork the repository**
2. **Clone your fork**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/executor-gm-bot.git
   cd executor-gm-bot
   ```
3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Create a branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

---

## 📋 Development Guidelines

### Code Style

- Follow **PEP 8** for Python code
- Use **type hints** for all function parameters
- Add **docstrings** for all classes and public methods
- Keep functions **small and focused** (single responsibility)

### Anti-Patterns to Avoid

**❌ NO PLACEHOLDERS:**
```python
def process_task(task):
    # TODO: implement this later
    pass
```

**✅ COMPLETE IMPLEMENTATIONS:**
```python
def process_task(task: Dict) -> Dict:
    """Process a task and return result."""
    result = {
        "status": "completed",
        "output": task.get("data", "")
    }
    return result
```

---

## 🏗️ Project Structure

```
executor/
├── core/              # Core modules
│   ├── orchestrator.py
│   ├── model_router.py
│   ├── skill_injector.py
│   └── power_recovery.py
├── agents/            # Agent connectors
├── config/            # Configuration templates
├── state/             # Runtime state (gitignored)
├── tests/             # Unit tests
└── main.py            # Entry point
```

---

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_model_router.py

# Run with coverage
pytest --cov=core tests/
```

### Writing Tests

- Use `pytest` framework
- Aim for **80%+ code coverage**
- Mock external API calls
- Test both **happy path** and **error cases**

Example:
```python
def test_select_model_fallback():
    router = ModelRouter(config_path)
    
    # Mock API failure
    with patch('requests.post', side_effect=ServiceUnavailable):
        result = router.select_with_fallback("claude-4.5-opus")
    
    # Should fallback to sonnet
    assert result["model"] == "claude-4.5-sonnet"
```

---

## 🐛 Bug Reports

When reporting bugs, include:

1. **Environment**: OS, Python version, dependency versions
2. **Steps to reproduce**: Exact commands/code
3. **Expected behavior**: What should happen
4. **Actual behavior**: What actually happens
5. **Logs**: Relevant error messages or stack traces

---

## ✨ Feature Requests

For new features:

1. **Open an issue** first to discuss
2. **Describe the use case**: Why is this needed?
3. **Propose a solution**: How would it work?
4. **Consider alternatives**: Other ways to solve the problem

---

## 📝 Pull Request Process

1. **Update documentation** if needed (README, ARCHITECTURE)
2. **Add tests** for new functionality
3. **Run linters**:
   ```bash
   flake8 core/ agents/
   mypy core/ agents/
   ```
4. **Write a clear PR description**:
   - What does this PR do?
   - Why is this change needed?
   - Any breaking changes?

5. **Reference issues**: Use "Fixes #123" or "Closes #456"

---

## 🎯 Priority Areas

We're especially interested in contributions for:

1. **Agent Templates**: New Project Agent types (DevOps, Designer, etc.)
2. **Model Providers**: Support for more LLM APIs (Gemini, Local models)
3. **Monitoring**: Dashboard for agent health metrics
4. **Documentation**: Tutorials, examples, diagrams
5. **Testing**: Increase test coverage

---

## 📜 Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on the code, not the person
- Help newcomers get started

---

## 🙏 Recognition

Contributors will be added to the README under "Contributors" section.

---

**Questions?** Open an issue or reach out to the maintainers!
