# Infusive Media Automation Framework

This is a Playwright + Python + Pytest automation framework using the Page Object Model (POM).

## Setup

1. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Or venv\Scripts\activate on Windows
   pip install -r requirements.txt
   playwright install chromium
   ```

2. Environment Variables:
   Copy `.env.example` to `.env` and fill in the required credentials.

## Running Tests

Run all tests:
```bash
pytest
```

Run UI tests only:
```bash
pytest tests/UI
```

Run API tests only:
```bash
pytest tests/api
```

## Reports
HTML reports will be generated in the `reports/` directory. Screenshots for failed tests will be saved in the `screenshots/` directory.
