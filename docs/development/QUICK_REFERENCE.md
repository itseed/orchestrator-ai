# 🚀 Quick Reference
## Orchestrator AI - Quick Access Guide

---

## ⚡ Most Used Files

### 🎯 Start Here
- **[README_DEVELOPMENT.md](README_DEVELOPMENT.md)** - Quick development start
- **[SUMMARY.md](SUMMARY.md)** - Project overview

### 📚 Documentation
- **[docs/README.md](docs/README.md)** - All documentation
- **[docs/CODE_REVIEW.md](docs/CODE_REVIEW.md)** - Code review
- **[docs/testing/](docs/testing/)** - Test results
- **[docs/development/](docs/development/)** - Development guides

### 🛠️ Scripts
- `scripts/dev_start.sh` - Start development
- `scripts/quick_test.py` - Test API

---

## 📁 File Locations

| What You Need | Where to Find |
|--------------|---------------|
| Quick Start | `README_DEVELOPMENT.md` |
| Test Results | `docs/testing/` |
| Development Guide | `docs/development/` |
| Code Review | `docs/CODE_REVIEW.md` |
| Architecture | `docs/ARCHITECTURE.md` |
| All Docs | `docs/README.md` |

---

## 🎯 Common Tasks

### Start Development
```bash
# See: README_DEVELOPMENT.md
docker-compose -f docker-compose.dev.yml up -d redis postgres
source venv/bin/activate
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

### Run Tests
```bash
pytest tests/ -v
```

### View Test Results
- Unit: `docs/testing/TEST_RESULTS.md`
- Integration: `docs/testing/INTEGRATION_TEST_RESULTS.md`

---

**Everything is organized and easy to find! 📁**
