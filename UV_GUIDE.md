# 📦 UV Package Manager Guide

This project uses `uv` for fast, modern Python dependency management.

## 🏗️ Project Structure

```
cybersecurity-news-feed/
├── pyproject.toml          # Root project (legacy monolithic app)
├── backend/
│   ├── pyproject.toml      # Backend dependencies
│   └── requirements.txt    # (Can be removed)
└── frontend/
    ├── pyproject.toml      # Frontend dependencies
    └── requirements.txt    # (Can be removed)
```

## 🚀 Setup with UV

### Backend Setup

```bash
cd backend

# Create virtual environment and install dependencies
uv sync

# Or if you want to add a new dependency
uv add <package-name>

# Run the backend
uv run python mcp_server.py
```

### Frontend Setup

```bash
cd frontend

# Create virtual environment and install dependencies
uv sync

# Or if you want to add a new dependency
uv add streamlit

# Run the frontend
uv run streamlit run app.py
```

## 📝 Common Commands

### Installing Dependencies

```bash
# Backend
cd backend && uv sync

# Frontend
cd frontend && uv sync
```

### Adding New Dependencies

```bash
# Backend - add production dependency
cd backend
uv add aiohttp

# Backend - add dev dependency
uv add --dev pytest

# Frontend - add production dependency
cd frontend
uv add pandas
```

### Removing Dependencies

```bash
cd backend
uv remove <package-name>
```

### Running Scripts

```bash
# Backend
cd backend
uv run python mcp_server.py
uv run python test_backend.py

# Frontend
cd frontend
uv run streamlit run app.py
```

### Updating Dependencies

```bash
cd backend
uv sync --upgrade
```

## 🔄 Migration from requirements.txt

You can now safely remove the `requirements.txt` files:

```bash
# After verifying pyproject.toml works
rm backend/requirements.txt
rm frontend/requirements.txt
```

## 📊 Root pyproject.toml

The root `pyproject.toml` contains the original monolithic app dependencies. You have two options:

### Option 1: Keep Root for Reference (Recommended)
Keep the root `pyproject.toml` as-is for the original `app.py` and `mcp_server.py` (now in root, not backend).

### Option 2: Convert to Workspace
Update root to use UV workspaces:

```toml
[tool.uv.workspace]
members = ["backend", "frontend"]
```

## ⚡ Why UV?

- **Fast**: 10-100x faster than pip
- **Modern**: Uses pyproject.toml standard
- **Deterministic**: Lock files for reproducible builds
- **Simple**: One command to rule them all

## 🎯 Recommended Workflow

### Daily Development

```bash
# Terminal 1 - Backend
cd backend
uv sync
uv run python mcp_server.py

# Terminal 2 - Frontend
cd frontend
uv sync
uv run streamlit run app.py
```

### Adding Features

```bash
# Need a new backend dependency?
cd backend
uv add <package>
git add pyproject.toml uv.lock
git commit -m "feat: add <package> for <feature>"

# Need a new frontend dependency?
cd frontend
uv add <package>
git add pyproject.toml uv.lock
git commit -m "feat: add <package> for <feature>"
```

## 🐳 Docker Integration

When creating Dockerfiles, use uv:

```dockerfile
# Backend Dockerfile
FROM python:3.12-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock* ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy application
COPY . .

CMD ["uv", "run", "python", "mcp_server.py"]
```

## 📚 Resources

- [UV Documentation](https://docs.astral.sh/uv/)
- [pyproject.toml Specification](https://peps.python.org/pep-0621/)

---

**TL;DR:**
- Use `uv sync` instead of `pip install -r requirements.txt`
- Use `uv add <package>` instead of manually editing files
- Use `uv run <command>` to run scripts in the virtual environment
- You can delete `requirements.txt` files after confirming everything works

