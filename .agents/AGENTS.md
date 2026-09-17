# Workspace Agent Rules

## API Testing Environment Rule
- **Default Environment**: By default, all API tests MUST target the **STAGE** environment (`BASE_API_URL_STG = https://infusive-back.jobvritta.com/api/`).
- **Production Environment Switching**: Tests should only execute against **PROD** (`BASE_API_URL_PROD = https://crmapi.infusivemedia.com/api/`) when the user explicitly passes `--env=prod` / `--env=PRODUCTION` or explicitly requests Production execution.
