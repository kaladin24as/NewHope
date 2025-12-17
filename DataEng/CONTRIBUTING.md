# Contributing to AntiGravity

Thank you for your interest in contributing to AntiGravity! This document provides guidelines and instructions for contributing.

---

## 🚀 Getting Started

### Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/yourusername/antigravity.git
   cd antigravity/DataEng
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # Linux/Mac:
   source .venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r backend/requirements.txt
   ```

4. **Run Tests**
   ```bash
   pytest
   ```

---

## 📝 Code Style

### Python

We follow **PEP 8** with some modifications:

- **Line Length**: 100 characters (not 79)
- **Formatter**: Black
- **Linter**: Flake8
- **Type Hints**: Required for public functions

**Run formatters:**
```bash
black backend/ tests/
flake8 backend/ tests/
```

### Naming Conventions

- **Classes**: `PascalCase` (e.g., `TemplateEngine`)
- **Functions/Methods**: `snake_case` (e.g., `generate_project`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `DEFAULT_PORT`)
- **Private Methods**: `_leading_underscore` (e.g., `_render_template`)

### Docstrings

Use Google-style docstrings:

```python
def generate_project(name: str, stack: dict) -> VirtualFileSystem:
    """
    Generate a data engineering project.
    
    Args:
        name: Name of the project
        stack: Dictionary of selected tools by category
        
    Returns:
        VirtualFileSystem containing all generated files
        
    Raises:
        ValueError: If project name is invalid
    """
    pass
```

---

## 🧪 Testing

### Test Requirements

- **Coverage**: Minimum 80% for new code
- **Test Types**: Unit tests required, integration tests encouraged
- **Naming**: `test_*.py` files, `test_*` functions

### Writing Tests

```python
# tests/core/test_example.py
import pytest
from core.engine import TemplateEngine

def test_template_engine_initialization():
    """Test that TemplateEngine initializes correctly."""
    engine = TemplateEngine()
    assert engine.template_dir is not None

def test_vfs_add_file():
    """Test VirtualFileSystem file addition."""
    vfs = VirtualFileSystem()
    vfs.add_file("test.txt", "content")
    assert vfs.get_file("test.txt") == "content"
```

### Running Tests

```bash
# All tests
pytest

# Specific file
pytest tests/core/test_engine.py

# With coverage
pytest --cov=backend --cov-report=html

# Watch mode (requires pytest-watch)
ptw
```

---

## 🔌 Adding a New Provider

### Step 1: Create Provider Class

Create a new class in `backend/core/providers/<category>.py`:

```python
# backend/core/providers/ingestion.py
from core.interfaces import ComponentGenerator
from core.registry import ProviderRegistry

class MyToolGenerator(ComponentGenerator):
    def generate(self, output_dir: str, config: dict) -> None:
        """Generate files for MyTool."""
        context = config.get("project_context")
        # Generate files here
        
    def get_docker_service_definition(self, context) -> dict:
        """Return Docker Compose service config."""
        return {
            "mytool": {
                "image": "mytool:latest",
                "environment": self.get_env_vars(context),
                "ports": ["8080:8080"]
            }
        }
    
    def get_env_vars(self, context) -> dict:
        """Return environment variables."""
        return {
            "MYTOOL_API_KEY": context.get_or_create_secret("mytool_key")
        }

# Register the provider
ProviderRegistry.register("ingestion", "MyTool", MyToolGenerator)
```

### Step 2: Create Templates

Add Jinja2 templates to `backend/templates/<category>/`:

```jinja2
{# templates/ingestion/mytool_config.yml.j2 #}
api_key: {{ api_key }}
endpoint: {{ endpoint }}
```

### Step 3: Write Tests

```python
# tests/providers/test_mytool.py
from core.providers.ingestion import MyToolGenerator
from core.manifest import ProjectContext

def test_mytool_generator():
    context = ProjectContext(project_name="test", stack={"ingestion": "MyTool"})
    generator = MyToolGenerator(env=mock_jinja_env)
    
    service = generator.get_docker_service_definition(context)
    assert "mytool" in service
```

### Step 4: Update Registry

The provider auto-registers when imported. Ensure it's imported in:
```python
# backend/core/providers/__init__.py
from . import ingestion  # This triggers registration
```

---

## 🌿 Git Workflow

### Branching

- `main` - Production-ready code
- `feature/your-feature` - New features
- `fix/issue-number` - Bug fixes
- `docs/topic` - Documentation updates

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add Snowflake provider
fix: resolve template rendering bug
docs: update README with new providers
test: add tests for ProjectContext
refactor: simplify engine.generate() logic
```

### Pull Request Process

1. **Create Branch**
   ```bash
   git checkout -b feature/my-feature
   ```

2. **Make Changes**
   - Write code
   - Add tests
   - Update docs

3. **Test Locally**
   ```bash
   pytest
   black backend/ tests/
   flake8 backend/ tests/
   ```

4. **Commit**
   ```bash
   git add .
   git commit -m "feat: add my feature"
   ```

5. **Push**
   ```bash
   git push origin feature/my-feature
   ```

6. **Create Pull Request**
   - Provide clear description
   - Reference related issues
   - Ensure CI passes

---

## 📋 PR Checklist

Before submitting, ensure:

- [ ] Tests pass (`pytest`)
- [ ] Code formatted (`black`)
- [ ] Linting passes (`flake8`)
- [ ] Documentation updated
- [ ] Commit messages follow conventions
- [ ] No merge conflicts with `main`

---

## 🐛 Reporting Bugs

Use [GitHub Issues](https://github.com/yourusername/antigravity/issues) with:

**Template:**
```markdown
### Description
Brief description of the bug

### Steps to Reproduce
1. Run command X
2. Select option Y
3. Error occurs

### Expected Behavior
What should happen

### Actual Behavior
What actually happens

### Environment
- OS: Windows 10 / Ubuntu 22.04 / macOS 13
- Python: 3.11
- AntiGravity version: 0.5.0
```

---

## 💡 Feature Requests

We welcome feature requests! Please:

1. Check existing issues first
2. Provide clear use case
3. Explain expected behavior
4. Consider implementation complexity

---

## 📞 Getting Help

- **Questions**: [GitHub Discussions](https://github.com/yourusername/antigravity/discussions)
- **Bugs**: [GitHub Issues](https://github.com/yourusername/antigravity/issues)
- **Chat**: (if applicable)

---

## 🙏 Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on collaboration
- Help newcomers

---

**Thank you for contributing to AntiGravity!** 🚀
