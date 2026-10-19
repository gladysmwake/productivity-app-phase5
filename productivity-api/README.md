# Productivity API (Flask Backend)

This directory contains the secure Flask REST API for the Productivity application.

For the comprehensive project documentation—including system architecture, full API endpoint tables, database models, environment configuration, testing, and client integration—please refer to the primary repository documentation:

👉 **[Main Project Documentation (README.md)](../README.md)**

---

### Backend Quick Reference

```bash
# 1. Install pinned dependencies
pipenv install

# 2. Enter virtual environment
pipenv shell

# 3. Apply database migrations
flask db upgrade

# 4. Seed database with starter data
python seed.py

# 5. Launch the API server (Port 5555)
python app.py
```

### Running Test Suite

```bash
pytest -v
```
