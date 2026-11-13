# Living Defect Repository: Active QA Bugs & Statutory Issues

## 1. Defect Summary Ledger

| Defect ID | Severity | Module | Description | Status |
| :---: | :---: | :--- | :--- | :---: |
| **`DEF-001`** | **Medium** | Invoices (`/invoice-list-page`) | `Overpay` tab badge displays `0` despite 3 overpaid invoices in table | **CONFIRMED** |
| **`DEF-002`** | **Critical** | Invoices PDF Engine | USD Invoice PDF hardcodes `Currency: INR`, `Rupees` in words, and `CGST/SGST ($)` | **CONFIRMED** |
| **`DEF-003`** | **Major** | Projects (`/project-details`) | `Project Start Date` & `Billing Start Date` accept past dates without validation (Violates PM Ritesh Singh rule) | **REPORTED TO DEV (FIX PENDING)** |
| **`DEF-004`** | **Major** | Projects (`/project-details`) | Project Status: `Inactive` KPI badge renders with Green styling instead of Red/Danger styling | **CONFIRMED** |
| **`DEF-005`** | **Major** | Service Budget (`/project-details` Tab 2) | Estimated Amount calculation does not consider selected duration unit (Remove "Days", keep "Months" and "Years") | **CONFIRMED (RESOLUTION DEFINED)** |

---

## 2. Detailed Defect Reports

### Defect 1: `DEF-001` — Dynamic Badge Count Mismatch on "Overpay" Tab
- **Severity:** Medium (UI/Data Synchronization)
- **Module:** Invoices Ledger (`https://infusive-front.jobvritta.com/invoice-list-page`)
- **Observed Behavior:**
  - In the top status tab bar, the tab label reads: `Overpay: 0`.
  - When the user clicks the `Overpay` tab, the dynamic table successfully renders **3 active invoices**:
    1. `INV-2026-0013` (ConvCo Alpha, Overpay: $50.00)
    2. `INV-2026-0005` (Beta Media, Overpay: ₹12,000.00)
    3. `INV-2026-0016` (Testing Company, Overpay: $20.00)
  - The pagination text explicitly states: `Showing 1–3 of 3 records`.
- **Expected Behavior:**
  - The tab badge must reflect the exact record count of the filtered query: `Overpay: 3`.
- **Root Cause Hypothesis:**
  - The tab count aggregate API query (`GET /api/invoices/count?status=overpay`) uses a stale cache or applies an incorrect SQL filter, while the table query (`GET /api/invoices?status=overpay`) retrieves all matching rows.
- **Automated Verification:**
  - Test: `tests/UI/test_invoices_module.py::test_dynamic_tab_count_parity`

---

### Defect 2: `DEF-002` — USD Invoice PDF Hardcodes INR Currency, Rupee Words & Domestic CGST/SGST
- **Severity:** Critical (Statutory & Financial Compliance Violation)
- **Module:** PDF Generation Service (`/api/invoices/{id}/download-pdf`)
- **Reference Evidence:** User Screenshot `INV-2026-0041` (Bill To: `test10thj`)
- **Observed Behavior:**
  When a project billing plan is created in **USD** with a unit price of `$100.00`:
  1. **Header Metadata:** Displays `Currency: INR` directly under `Due Date` and `Payment Terms: 30 Days`.
  2. **Tax Breakdown:** Applies `CGST (9%): $9.00` and `SGST (9%): $9.00`, erroneously attaching dollar signs (`$`) to Indian domestic state taxes.
  3. **Amount in Words:** Displays `"Rupees One Hundred Eighteen Only"` for a `$118.00` foreign transaction.
- **Expected Statutory Behavior:**
  - **Header Currency:** Must dynamically inherit the billing plan currency: `Currency: USD`.
  - **Amount in Words:** Must resolve currency units dynamically: `"US Dollars One Hundred Eighteen Only"`.
  - **Statutory Taxation Compliance:**
    - Under **Section 16 of the Integrated Goods and Services Tax (IGST) Act, 2017**, cross-border supply of services is classified as **Zero-Rated Export of Services** under Letter of Undertaking (LUT).
    - If exported under LUT, tax rate is **0%** (`Tax: $0.00`).
    - If subject to tax, it must be **IGST**, never domestic Intra-State `CGST + SGST`.
    - Combining domestic `CGST` + `SGST` with foreign currency symbols (`$9.00`) violates GST statutory filing standards.
- **Automated Verification:**
  - Test: `tests/UI/test_invoice_phase5_pdf_and_cancellation.py::test_usd_billing_plan_generates_usd_invoice_and_pdf`
  - Automated `pypdf` text audit assertions flag these discrepancies.

---

### Defect 3: `DEF-003` — Missing Past-Date Validation on Project Start Date & Billing Schedules
- **Severity:** Major (Business Logic & Scheduling Anomaly)
- **Module:** Project Details (`/project-details` -> Project Details Tab & Billing & Invoices Tab)
- **Stakeholder Confirmation:**
  - **Project Manager:** Ritesh Singh (RS)
  - **Query:** *"Project Start Date\* -> sir ye past me to nhi hoga na ?"*
  - **PM Response:** *"nahi"* (Confirmed: Backdating is **strictly prohibited**).
- **Observed Behavior:**
  - On **Tab 1: Project Details**, the `Project Start Date` input (`input[type='date']`) has no HTML5 `min` attribute constraint.
  - On **Tab 5: Billing & Invoices**, both `Billing Start Date` and `Next Invoice Date` allow arbitrary past dates (e.g. `2026-01-01`).
  - The form saves successfully without any warning or validation constraint.
  - Upon saving, the project immediately recalculates **Estimated End Date** into the past, and the billing plan immediately enters a premature `Due for invoice` / `Overdue` state before commercial delivery begins.
- **Expected Behavior (Confirmed by PM Ritesh Singh):**
  - Form validation and date pickers must strictly enforce:
    $$\text{Project Start Date} \ge \text{Today's Date}$$
    $$\text{Billing Start Date} \ge \text{Project Start Date} \ge \text{Today's Date}$$
    $$\text{Next Invoice Date} \ge \text{Billing Start Date}$$
  - The date input must include `min="YYYY-MM-DD"` (Today's date).
  - Submitting an arbitrary past date must be blocked by the frontend with helper text or error toast: `"Project Start Date cannot be in the past"`, and rejected by the backend with HTTP `400 Bad Request`.
- **Automated Verification:**
  - Test: `tests/UI/test_project_tab1_details.py::test_tab1_start_date_backdating_rejection_audit`
  - Test: `tests/UI/test_project_billing_services.py::test_billing_schedule_date_constraints`
  - Test: `tests/UI/test_phase4_project_setup.py::test_project_start_date_past_date_rejection`

---

### Defect 4: `DEF-004` — Project Status: "Inactive" KPI Badge Rendered in Green Instead of Red
- **Severity:** Major (UI/UX Status Inversion & Visual Ambiguity)
- **Module:** Project Details (`https://infusive-front.jobvritta.com/project-details` -> Tab 1: Project Details KPI Deck)
- **Reference Evidence:**
  - User Screenshot: `media_1794395697234_1e120e1a.png` (explicitly showing `Project Status: Inactive` badge in light green background with green text).
- **Observed Behavior:**
  - When the project status is updated to `Inactive` and saved, the 7th KPI summary card (`Project Status`) displays:
    - Text: `Inactive`
    - Computed CSS `color`: `rgb(21, 128, 61)` (emerald green `#15803d`)
    - Computed CSS `backgroundColor`: `rgb(220, 252, 231)` (pale green `#dcfce7`)
    - Class: `chakra-text project-summary-status css-0`
  - The styling is 100% identical to `Active` status.
- **Expected Behavior:**
  - An `Inactive` status must clearly convey disabled/deactivated state using **RED / Danger styling**:
    - Recommended text color: `rgb(185, 28, 28)` or `#dc2626` / `#b91c1c`
    - Recommended background: `rgb(254, 226, 226)` or `#fee2e2`
  - Only `Active` status should use Green styling (`#15803d` / `#dcfce7`).
- **Automated Verification:**
  - Test: `tests/UI/test_project_tab1_details.py::test_tab1_project_details_comprehensive_validation`
  - Evidence: `badge_style = {'text': 'Inactive', 'color': 'rgb(21, 128, 61)', 'backgroundColor': 'rgb(220, 252, 231)'}`

---

### Defect 5: `DEF-005` — Estimated Amount Calculation Does Not Consider Selected Duration Unit
- **Severity:** Major (Calculation / Financial Integrity Defect)
- **Priority:** High
- **Module:** Project Management → Service Budget (`/project-details` Tab 2)
- **Title:** Estimated Amount Calculation Does Not Consider Selected Duration Unit
- **Steps to Reproduce:**
  1. Navigate to Project Details → Budget Tab (`/project-details`).
  2. Click `Configure` / `Edit` on a service row to open `#budget-edit-form`.
  3. Select **Service Type** as `Recurring`.
  4. Enter **Monthly Budget** as `100`.
  5. Set **Estimated Duration** to `10`.
  6. Select unit dropdown as **Days** (`value="1"`).
  7. Observe the calculated **Estimated Amount**.
  8. Switch unit to **Months** (`value="2"`) and **Years** (`value="3"`), and compare.
- **Expected Result:**
  - The client-side formula and backend calculation should scale according to the selected duration unit:
    - **Days:** $\text{Monthly Budget} \div 30 \times \text{Duration}$ (or calendar pro-rata: $100 \div 30 \times 10 = \$33.33$)
    - **Months:** $\text{Monthly Budget} \times \text{Duration}$ ($100 \times 10 = \$1,000$)
    - **Years:** $\text{Monthly Budget} \times 12 \times \text{Duration}$ ($100 \times 12 \times 10 = \$12,000$)
- **Actual Result:**
  - The system multiplies Monthly Budget directly by the duration value, irrespective of the selected unit. For example, $100 \times 10\text{ Days}$ erroneously displays **$1,000** (as if 10 days were 10 months).
- **Comments / QA Observation & Product Decision:**
  - **Confirmed Resolution (Product Decision):** **Remove `Days` entirely from the dropdown!** Retain only **`Months`** and **`Years`** in the dropdown.
  - **Updated Expected Formula:**
    - **Months (`val="2"`):** $\text{Estimated Amount} = \text{Monthly Budget} \times \text{Duration}$
    - **Years (`val="3"`):** $\text{Estimated Amount} = \text{Monthly Budget} \times 12 \times \text{Duration}$
  - Eliminating `Days` prevents fractional month/calendar conversion discrepancies and enforces clean monthly/annual recurring budgeting.
- **Automated Verification:**
  - Test: `tests/UI/test_project_tab2_budget.py::test_tab2_budget_duration_unit_calculation_audit`


