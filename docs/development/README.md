# Development Documentation
## Orchestrator AI - Development Guides

---

## 📚 Development Guides

### 🚀 Quick Start
- **[README_DEVELOPMENT.md](./README_DEVELOPMENT.md)** - Quick development start guide (start here!)
- **[START_DEVELOPMENT.md](./START_DEVELOPMENT.md)** - Quick start guide
- **[DEVELOPMENT_READY.md](./DEVELOPMENT_READY.md)** - Setup completion status
- **[SUMMARY.md](./SUMMARY.md)** - Project summary and overview

### 📖 Detailed Guides
- **[DEVELOPMENT_GUIDE.md](./DEVELOPMENT_GUIDE.md)** - Comprehensive development guide
- **[DEVELOPMENT_STATUS.md](./DEVELOPMENT_STATUS.md)** - Current development status

### 📋 Reference & Organization
- **[QUICK_REFERENCE.md](./QUICK_REFERENCE.md)** - Quick reference guide
- **[FILE_ORGANIZATION.md](./FILE_ORGANIZATION.md)** - File organization guide
- **[FILE_ORGANIZATION_SUMMARY.md](./FILE_ORGANIZATION_SUMMARY.md)** - Organization summary
- **[ORGANIZATION_COMPLETE.md](./ORGANIZATION_COMPLETE.md)** - Organization completion status

---

## 🚀 Quick Start

### 1. Start Services
```bash
docker-compose -f docker-compose.dev.yml up -d redis postgres
```

### 2. Start API Server
```bash
source venv/bin/activate
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Test API
```bash
curl http://localhost:8000/health
python scripts/quick_test.py
```

---

## 🔗 Important URLs

- **API:** http://localhost:8000
- **Docs:** http://localhost:8000/docs
- **Health:** http://localhost:8000/health

---

## 📝 Development Workflow

1. Create feature branch
2. Make changes
3. Run tests: `pytest tests/ -v`
4. Check code quality: `black . --check`
5. Commit changes

---

## 🛠️ Available Scripts

- `scripts/dev_start.sh` - Start all services
- `scripts/test_api.sh` - Test API endpoints
- `scripts/quick_test.py` - Python API test script

---

## 📖 Additional Resources

- **Code Review:** [../CODE_REVIEW.md](../CODE_REVIEW.md)
- **Test Results:** [../testing/](../testing/)
- **Architecture:** [../ARCHITECTURE.md](../ARCHITECTURE.md)
- **All Documentation:** [../README.md](../README.md)

---

For detailed information, see individual guide files.
