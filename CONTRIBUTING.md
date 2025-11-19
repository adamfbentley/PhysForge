# Contributing to PhysForge

Thank you for your interest in contributing to PhysForge! This document provides guidelines for contributing to the project.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR-USERNAME/PhysForge_-_Meta-Simulation.git
   cd PhysForge_-_Meta-Simulation
   ```
3. **Create a branch** for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Setup

### Backend Services

Each backend service has its own dependencies:

```bash
cd backend/auth_service
pip install -r requirements.txt
pytest tests/  # Run tests
```

### Frontend

```bash
cd frontend
npm install
npm run dev     # Start development server
npm run build   # Build for production
```

### Docker Compose (Full Stack)

```bash
docker-compose up --build
```

## Code Style

### Python
- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Write docstrings for all public functions/classes
- Run `flake8` and `black` before committing:
  ```bash
  flake8 backend/
  black backend/
  ```

### TypeScript/React
- Use TypeScript strict mode
- Follow React hooks best practices
- Use Prettier for formatting:
  ```bash
  cd frontend
  npm run format
  ```

## Testing

- **Backend:** Write pytest tests for new features
- **Frontend:** Add unit tests for new components
- All tests must pass before merging:
  ```bash
  # Backend
  cd backend/SERVICE_NAME
  pytest tests/ -v
  
  # Frontend
  cd frontend
  npm test
  ```

## Pull Request Process

1. **Update documentation** if you change functionality
2. **Add tests** for new features
3. **Ensure all tests pass** locally
4. **Update CHANGELOG.md** with your changes
5. **Submit PR** with clear description of changes
6. **Link related issues** in PR description

### PR Title Format

Use conventional commits format:
- `feat: Add symbolic regression caching`
- `fix: Resolve PINN training convergence issue`
- `docs: Update architecture documentation`
- `refactor: Simplify job orchestration logic`
- `test: Add unit tests for derivative service`

## Reporting Issues

When reporting bugs, please include:
- **Description** of the issue
- **Steps to reproduce**
- **Expected vs actual behavior**
- **Environment** (OS, Python version, etc.)
- **Logs/error messages** if applicable

## Feature Requests

For new features:
- **Describe the use case** clearly
- **Explain the benefit** to users/researchers
- **Consider implementation complexity**
- **Discuss in an issue** before implementing

## Code Review

All contributions require code review:
- Be respectful and constructive
- Address review feedback promptly
- Maintainers may request changes before merging

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Questions?

- Open an issue for questions
- Tag maintainers for urgent matters
- Join discussions in issue threads

---

**Thank you for contributing to scientific discovery! 🔬🚀**
