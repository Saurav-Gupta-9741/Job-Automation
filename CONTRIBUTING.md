# Contributing to Career OS

First off, thank you for considering contributing to Career OS! It's people like you that make Career OS such a great tool for job seekers.

## 🤝 Code of Conduct

This project and everyone participating in it is governed by respect, collaboration, and constructive feedback. By participating, you are expected to uphold this standard.

## 🐛 How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates. When you create a bug report, include as many details as possible:

- **Use a clear and descriptive title**
- **Describe the exact steps to reproduce the problem**
- **Provide specific examples** (URLs, screenshots, logs)
- **Describe the behavior you observed** and what you expected
- **Include your environment details** (OS, Python version, Chrome version)

**Bug Report Template:**
```markdown
### Description
A clear description of what the bug is.

### Steps to Reproduce
1. Go to '...'
2. Click on '...'
3. See error

### Expected Behavior
What you expected to happen.

### Actual Behavior
What actually happened.

### Environment
- OS: [e.g., Windows 11]
- Python Version: [e.g., 3.9.7]
- Chrome Version: [e.g., 120.0]
- Backend Version: [e.g., 1.0.0]

### Logs
```
Paste relevant logs here
```

### Screenshots
If applicable, add screenshots.
```

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, include:

- **Use a clear and descriptive title**
- **Provide a detailed description** of the proposed functionality
- **Explain why this enhancement would be useful**
- **List any alternative solutions** you've considered

**Enhancement Template:**
```markdown
### Feature Description
A clear description of the feature.

### Use Case
Why is this feature needed? What problem does it solve?

### Proposed Solution
How should this feature work?

### Alternatives Considered
What other approaches did you consider?

### Additional Context
Any mockups, examples, or references.
```

### Pull Requests

1. **Fork the repository** and create your branch from `main`
2. **Follow the coding style** used throughout the project
3. **Add tests** if you've added code that should be tested
4. **Update documentation** if you've changed APIs or functionality
5. **Ensure tests pass** before submitting
6. **Write a clear pull request description**

**Pull Request Template:**
```markdown
### Description
Brief description of changes.

### Type of Change
- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

### Testing
- [ ] All existing tests pass
- [ ] New tests added (if applicable)
- [ ] Manually tested on LinkedIn Easy Apply
- [ ] Tested on [Platform Name]

### Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex logic
- [ ] Documentation updated
- [ ] No sensitive data in commit
```

## 💻 Development Setup

### Prerequisites
- Python 3.8+
- Google Chrome
- Git
- Groq API key (free tier works)

### Setup Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/Saurav-Gupta-9741/Job-Automation.git
   cd Job-Automation
   ```

2. **Run automated setup**
   ```bash
   setup.bat  # Windows
   # or
   ./setup.sh  # macOS/Linux (if available)
   ```

3. **Configure environment**
   ```bash
   # Edit .env
   GROQ_API_KEY=your_key_here
   ```

4. **Start development backend**
   ```bash
   start.bat
   ```

5. **Load extension in Chrome**
   - Go to `chrome://extensions`
   - Enable Developer mode
   - Load unpacked: `apps/extension/`

### Development Workflow

1. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```

2. **Make your changes**
   - Write code following style guidelines
   - Add tests for new features
   - Update documentation

3. **Test your changes**
   ```bash
   # Run automated tests
   cd services/ml-core
   pytest tests/test_robustness.py -v
   
   # Run system tests
   test.bat
   
   # Manual testing on LinkedIn
   # Follow LINKEDIN_TESTING_GUIDE.md
   ```

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add amazing feature"
   ```
   
   Use conventional commit messages:
   - `feat:` - New feature
   - `fix:` - Bug fix
   - `docs:` - Documentation changes
   - `test:` - Test additions/changes
   - `refactor:` - Code refactoring
   - `style:` - Code style changes (formatting)
   - `chore:` - Build process or auxiliary tool changes

5. **Push to your fork**
   ```bash
   git push origin feature/amazing-feature
   ```

6. **Create Pull Request**
   - Go to GitHub
   - Click "New Pull Request"
   - Fill in the template
   - Wait for review

## 📝 Coding Standards

### Python Style Guide

Follow PEP 8 with these specifics:

```python
# Use type hints
def process_element(element: Element, profile: Profile) -> Optional[Action]:
    """Process an element and return action.
    
    Args:
        element: The DOM element to process
        profile: User profile data
        
    Returns:
        Action to take, or None if no action needed
    """
    pass

# Use docstrings for all functions
# Use descriptive variable names
# Keep functions small and focused
# Handle errors explicitly

# Good
def calculate_confidence(score: float) -> ConfidenceTier:
    if score >= 0.85:
        return ConfidenceTier.HIGH
    elif score >= 0.60:
        return ConfidenceTier.MEDIUM
    elif score >= 0.40:
        return ConfidenceTier.LOW
    return ConfidenceTier.VERY_LOW

# Bad
def calc(s):
    if s >= 0.85: return "high"
    if s >= 0.60: return "med"
    return "low"
```

### JavaScript Style Guide

Follow modern ES6+ standards:

```javascript
// Use const/let, never var
const MAX_RETRIES = 3;
let retryCount = 0;

// Use arrow functions for callbacks
elements.forEach(el => processElement(el));

// Use async/await for promises
async function fetchData() {
  try {
    const response = await fetch(url);
    return await response.json();
  } catch (error) {
    console.error('Fetch failed:', error);
    return null;
  }
}

// Use descriptive names
// Add comments for complex logic
// Keep functions small and focused

// Good
async function detectRateLimit(elements) {
  const rateLimitPhrases = [
    'slow down',
    'too many applications',
    'wait a moment'
  ];
  
  const pageText = elements
    .map(el => el.text || '')
    .join(' ')
    .toLowerCase();
    
  return rateLimitPhrases.some(phrase => pageText.includes(phrase));
}

// Bad
function chk(els) {
  let t = '';
  for (let i = 0; i < els.length; i++) {
    t += els[i].text || '';
  }
  return t.indexOf('slow') > -1;
}
```

### Documentation Standards

- **Every function** should have a docstring (Python) or JSDoc comment (JavaScript)
- **Complex logic** should have inline comments explaining the "why"
- **API changes** must update relevant .md files
- **New features** need usage examples in documentation

### Testing Standards

```python
# Test naming: test_[what]_[condition]_[expected_result]
def test_retry_logic_on_transient_error_retries_with_backoff():
    """Test that transient errors trigger exponential backoff retry."""
    # Arrange
    error = TransientError("Rate limited")
    retry_count = 0
    
    # Act
    result = retry_with_backoff(error, retry_count)
    
    # Assert
    assert result.delay == 2 ** retry_count
    assert result.should_retry is True
```

## 🧪 Testing Guidelines

### Required Testing

Before submitting a PR, ensure:

1. **All existing tests pass**
   ```bash
   pytest tests/ -v
   ```

2. **New features have tests**
   - Unit tests for functions
   - Integration tests for features
   - Manual tests on LinkedIn

3. **Manual testing completed**
   - Test on at least 2 real LinkedIn jobs
   - Verify no errors in console
   - Check database records created

### Test Categories

1. **Unit Tests**: Test individual functions
2. **Integration Tests**: Test component interaction
3. **Manual Tests**: Test on real websites
4. **Regression Tests**: Ensure bugs don't return

## 📚 Documentation Guidelines

### When to Update Documentation

- **New features**: Add to relevant guides
- **Bug fixes**: Update troubleshooting guides
- **API changes**: Update CONFIGURATION_GUIDE.md
- **Breaking changes**: Update README.md with migration guide

### Documentation Structure

- **README.md**: Project overview, quick start
- **Technical guides**: How it works, architecture
- **User guides**: How to use features
- **Reference docs**: API, configuration options
- **Troubleshooting**: Common issues and solutions

## 🚦 Review Process

### What We Look For

1. **Code Quality**
   - Follows style guidelines
   - Well-tested
   - No code smells
   - Proper error handling

2. **Functionality**
   - Works as described
   - No breaking changes
   - Backward compatible (if possible)
   - Edge cases handled

3. **Documentation**
   - Updated for changes
   - Clear and comprehensive
   - Examples provided
   - No typos

4. **Security**
   - No sensitive data exposed
   - Proper input validation
   - No SQL injection risks
   - CSRF tokens handled

### Review Timeline

- Initial review: Within 3-5 days
- Follow-up responses: Within 2 days
- Final approval: After all feedback addressed

## 🎯 Priority Areas for Contribution

### High Priority
1. **Additional Platform Adapters**
   - Indeed.com
   - ZipRecruiter
   - Monster.com
   - AngelList

2. **Error Recovery Improvements**
   - Better CAPTCHA detection
   - Network retry strategies
   - Session recovery enhancements

3. **Testing**
   - More automated tests
   - Platform-specific test suites
   - Performance benchmarks

### Medium Priority
4. **UI Enhancements**
   - Better confidence indicators
   - Progress visualization
   - Settings panel

5. **Documentation**
   - Video tutorials
   - Platform-specific guides
   - Troubleshooting flowcharts

6. **Features**
   - Multi-language support
   - Custom field mapping UI
   - Analytics dashboard

### Nice to Have
7. **Developer Tools**
   - CI/CD pipeline
   - Automated releases
   - Code coverage reports

8. **Integrations**
   - Email notifications
   - Slack integration
   - Calendar integration

## 📞 Getting Help

### Where to Ask Questions

- **GitHub Discussions**: General questions, ideas
- **GitHub Issues**: Bug reports, feature requests
- **Documentation**: Check guides first

### Response Times

- Questions: 1-3 days
- Bug reports: 2-5 days
- Feature requests: 1-2 weeks
- Pull requests: 3-7 days

## 🏆 Recognition

Contributors will be:
- Listed in README.md
- Mentioned in release notes
- Credited in documentation (if significant contribution)

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to Career OS! Your efforts help job seekers save time and focus on what matters most. 🚀

**Questions?** Open a GitHub Discussion or contact the maintainers.
