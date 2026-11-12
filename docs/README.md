# Infusive Media — System QA Specifications & Master Architecture

## 1. System Overview
**Infusive Media** is an enterprise agency management and revenue realization platform spanning the entire client lifecycle: from initial presales lead prospecting, BDM opportunity qualification and conversion, to project delivery setup, customer financial ledgering, billing plan governance, and statutory GST-compliant invoicing.

This documentation suite serves as the **Living QA Specification** and single source of truth for test design, business validation rules, statutory compliance checks, and automated Playwright test suites.

---

## 2. Platform Navigation & Module URLs

| Module # | Module Name | Target URL | Primary Roles | Key Responsibilities |
| :---: | :--- | :--- | :--- | :--- |
| **01** | **Presales / Company** | `/company`, `/lead-pool` | Pre-Sales, Admin | Quick lead generation, Company & POC onboarding, Lead assignment |
| **02** | **BDM Leads** | `/created-lead`, `/my-leads` | BDM, Sales Lead | Lead acceptance, sales qualification, stage transitions to "Won" |
| **03** | **Projects** | `/projects`, `/project-details` | Project Manager, Admin | Project setup, Service Budgeting, Resource Allocation, Tasks, Billing Plan |
| **04** | **Customers** | `/customers`, `/customers/{id}` | Finance, Admin | Master client directory, Active state validation, Outstanding receivables |
| **05** | **Billing Plans** | `/allBillingPlans` | Finance, Operations | Centralized recurring & milestone billing plans, dynamic metrics cards |
| **06** | **Invoices & Tax** | `/invoice-list-page` | Finance, Auditor | Statutory GST invoices, dynamic status tabs, PDF audit, payment settlement |

---

## 3. User Personas & Test Credentials
Configured in `.env` and mapped dynamically via `pages/login_page.py` & credential resolution utilities:

```
┌─────────────────┬───────────────────────────────┬────────────────────────────┐
│ Persona         │ Default Email                 │ Primary Authorization Scope│
├─────────────────┼───────────────────────────────┼────────────────────────────┤
│ Admin           │ Admin@infusive.com            │ Full System Master Access  │
│ Pre-Sales       │ PreSales2@mailinator.com      │ Leads, Companies, Contacts │
│ BDM (Sales)     │ Uday@mailinator.com           │ My Leads, Won Conversion   │
│ Project Manager │ pm@infusivemedia.com          │ Projects, Tasks, Budgets   │
│ Finance / Accts │ accounts@infusivemedia.com    │ Billing Plans, Invoices    │
└─────────────────┴───────────────────────────────┴────────────────────────────┘
```

---

## 4. Documentation Structure

```text
docs/
├── README.md                               <-- System overview, user roles, environment directory (This file)
│
├── integration/                            <-- CROSS-MODULE END-TO-END SPECIFICATIONS
│   └── e2e_presales_to_invoice_flow.md     <-- Master 6-Phase revenue journey (Pre-sales -> BDM -> PM -> Invoices)
│
├── modules/                                <-- DEDICATED MODULE-WISE SPECIFICATIONS
│   ├── 01_presales_flow_validation.md      <-- Lead creation, Company & POC forms, constraints, BDM allocation
│   ├── 02_bdm_leads_flow_validation.md     <-- Lead acceptance, BDM status transitions, Won conversion trigger
│   ├── 03_projects_flow_validation.md      <-- Project details, Service Budgeting, Resource Allocation & Tasks
│   ├── 04_customers_flow_validation.md     <-- Active customer profile, POC sync, outstanding ledger balance
│   ├── 05_billing_plans_flow_validation.md <-- Central plans ledger, cycle governance, currency parity, metric cards
│   └── 06_invoices_flow_validation.md      <-- Invoice ledger, dynamic tabs, statutory tax rules, PDF inspection
│
└── bug_tracker/                            <-- LIVING QA DEFECT REPOSITORY
    └── active_defects.md                   <-- Confirmed bugs: Overpay badge mismatch, PDF USD/Tax hardcoding, Past dates
```

---

## 5. Playwright Automation Architecture Mapping

```
                                      TEST SUITES
                            tests/UI/test_*.py
                                    │
                                    ▼
                                WORKFLOWS
                   workflows/billing_invoice_workflow.py
                   workflows/e2e_company_to_invoice_workflow.py
                                    │
                                    ▼
                               PAGE OBJECTS
                            pages/*_page.py
                                    │
                                    ▼
                               BASE ENGINE
                        Playwright Sync API & pytest
```

- **Page Objects (`pages/`)**: Encapsulate stable UI locators, interaction methods, actionability checks, and Chakra UI component handlers.
- **Workflows (`workflows/`)**: Orchestrate multi-step, cross-module business journeys (e.g., login handoff, data passing between Lead and Invoice).
- **Test Suites (`tests/UI/`)**: Contain declarative pytest test cases, parameterized data drivers, and strict hard assertions.
