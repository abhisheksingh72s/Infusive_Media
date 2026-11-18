# QA Tracker: Defects & Product Suggestions

This repository tracks confirmed software defects (bugs) and proposed product/architectural suggestions for Infusive Media.

---

## 1. Summary Ledger

| ID | Type | Severity / Priority | Module | Summary Description | Status |
| :---: | :---: | :---: | :--- | :--- | :---: |
| **`DEF-001`** | **DEFECT** | Medium | Invoices (`/invoice-list-page`) | `Overpay` tab badge displays `0` despite 3 overpaid invoices in table | **AUDITED (0 in DB)** |
| **`DEF-002`** | **DEFECT** | Critical | Invoices PDF Engine | USD Invoice PDF hardcodes `Currency: INR`, `Rupees` in words, and `CGST/SGST ($)` | **VERIFIED FIXED** |
| **`DEF-003`** | **DEFECT** | Major | Projects (`/project-details`) | `Project Start Date` & `Billing Start Date` accept past dates without validation | **VERIFIED FIXED** |
| **`DEF-004`** | **DEFECT** | Major | Projects (`/project-details`) | Project Status: `Inactive` KPI badge renders with Green styling instead of Red | **VERIFIED FIXED** |
| **`DEF-005`** | **DEFECT** | Major | Service Budget (`Tab 2`) | Estimated Amount calculation erroneously treats 10 Days as 10 Months | **VERIFIED FIXED (SUG-004)** |
| **`DEF-006`** | **DEFECT** | Major | Projects (`Tab 1 & 2`) | Configured services can be removed from Project Details despite existing budget | **VERIFIED FIXED** |
| **`DEF-007`** | **DEFECT** | Major | Projects Listing (`/projects`) | Project Amount column displayed as INR (₹) for foreign USD projects | **VERIFIED FIXED** |
| **`DEF-008`** | **DEFECT** | Major | Customer (`/customers/{id}`) | Invoice amounts now render native currency ($/€), but KPI summary cards default to INR (₹) for US clients | **PARTIALLY RESOLVED** |
| **`DEF-009`** | **DEFECT** | Medium | Customer (`/customers/{id}` Client Profile -> Tax) | GSTIN label hardcoded; fails to dynamically switch to EIN (US) or VAT (UK) | **PARTIALLY FIXED** |
| **`DEF-010`** | **DEFECT** | Medium / High | Billing Plans (`/allBillingPlans` Edit Modal) | Inactive plan Next Invoice Date update to today is discarded by backend recalculation engine; date remains unchanged | **CONFIRMED (BUG OPEN)** |
| **`SUG-001`** | **SUGGESTION** | High (Policy) | Projects (`Tabs 2, 3, 4, 5`) | Inactive Project Lockout: Freeze Budget, Resources, Tasks, and Billing mutations | **VERIFIED IMPLEMENTED** |
| **`SUG-002`** | **SUGGESTION** | High (Architecture) | Billing (`check-duplicate`) | Check Overlapping Recurring Date Ranges (`start <= EndDate`) instead of exact start date only | **SUBMITTED TO DEV** |
| **`SUG-003`** | **SUGGESTION** | Medium (UX) | Project Status Lifecycle | Deactivation/Reactivation Modals (`[ Stop Billing ]` vs `[ Continue Billing ]`) | **VERIFIED IMPLEMENTED** |
| **`SUG-004`** | **SUGGESTION** | Low (UI Cleanliness) | Service Budget (`Tab 2`) | Remove "Days" from Duration Unit dropdown; retain only "Months" and "Years" | **AGREED (PRODUCT DECISION)** |
| **`SUG-005`** | **SUGGESTION** | High (Architecture & UX) | Billing Plans & Invoices | Multi-Plan Traceability Gap: Missing Plan ID, Plan Name, Service Badges & Invoice Drilldown | **SPECIFIED & PROPOSED** |

---

## 2. Confirmed Defect Reports (Bugs)

### Defect 1: `DEF-001` — Dynamic Badge Count Mismatch on "Overpay" Tab
- **Type:** **DEFECT**
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
- **Type:** **DEFECT**
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

---

### Defect 3: `DEF-003` — Missing Past-Date Validation on Project Start Date & Billing Schedules
- **Type:** **DEFECT**
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
  - Upon saving, the project immediately recalculates **Estimated End Date** into the past, and the billing plan enters a premature `Due for invoice` / `Overdue` state before delivery starts.
- **Expected Behavior:**
  - Form validation and date pickers must strictly enforce:
    $$\text{Project Start Date} \ge \text{Today's Date}$$
    $$\text{Billing Start Date} \ge \text{Project Start Date} \ge \text{Today's Date}$$
    $$\text{Next Invoice Date} \ge \text{Billing Start Date}$$
  - The date input must include `min="YYYY-MM-DD"` (Today's date).
  - Submitting a past date must be blocked by the frontend (`"Project Start Date cannot be in the past"`) and rejected by the backend with HTTP `400 Bad Request`.
- **Automated Verification:**
  - Test: `tests/UI/test_project_tab1_details.py::test_tab1_start_date_backdating_rejection_audit`
  - Test: `tests/UI/test_project_billing_services.py::test_billing_schedule_date_constraints`

---

### Defect 4: `DEF-004` — Project Status: "Inactive" KPI Badge Rendered in Green Instead of Red
- **Type:** **DEFECT**
- **Severity:** Major (UI/UX Status Inversion & Visual Ambiguity)
- **Module:** Project Details (`https://infusive-front.jobvritta.com/project-details` -> Tab 1: Project Details KPI Deck)
- **Observed Behavior:**
  - When the project status is updated to `Inactive` and saved, the 7th KPI summary card (`Project Status`) displays:
    - Text: `Inactive`
    - Computed CSS `color`: `rgb(21, 128, 61)` (emerald green `#15803d`)
    - Computed CSS `backgroundColor`: `rgb(220, 252, 231)` (pale green `#dcfce7`)
- **Expected Behavior:**
  - An `Inactive` status must clearly convey disabled/deactivated state using **RED / Danger styling**:
    - Recommended text color: `rgb(185, 28, 28)` or `#dc2626`
    - Recommended background: `rgb(254, 226, 226)` or `#fee2e2`
  - Only `Active` status should use Green styling (`#15803d` / `#dcfce7`).
- **Automated Verification:**
  - Test: `tests/UI/test_project_tab1_details.py::test_tab1_project_details_comprehensive_validation`

---

### Defect 5: `DEF-005` — Estimated Amount Calculation Does Not Consider Selected Duration Unit
- **Type:** **DEFECT**
- **Severity:** Major (Calculation / Financial Integrity Defect)
- **Module:** Project Management → Service Budget (`/project-details` Tab 2)
- **Observed Behavior:**
  - In `#budget-edit-form`, when selecting **Monthly Budget = 100**, **Estimated Duration = 10**, and **Unit = Days**:
  - The system multiplies Monthly Budget directly by the duration value, calculating **$1,000** (as if 10 days were 10 months).
- **Expected Behavior:**
  - Calculation must scale properly based on the duration unit, or follow the agreed product decision in `SUG-004`.
- **Status:** **VERIFIED FIXED (Resolved via SUG-004)**
- **Resolution:** Developer removed `"Days"` option from the duration unit dropdown. Only `"Months"` and `"Years"` are selectable, ensuring clean monthly retainer calculations (`Estimated Amount = Monthly Budget * Duration (Months)`).
- **Verification Evidence:** Confirmed via manual execution & screenshot evidence (`Apex Global Solutions LLC - Project`, `PPC` budget 25 * 3 Months = $75).

---

### Defect 6: `DEF-006` — Configured Services Can Be Removed from Project Details Tab
- **Type:** **DEFECT**
- **Severity:** Major (Data Integrity & Referential Integrity Violation)
- **Reported By:** Abhishek Singh
- **Module:** Project Management → Project Details (`/project-details`) → Tab 1 (Details) & Tab 2 (Budget)
- **Observed Behavior:**
  - Once a service's budget has been configured under Tab 2 (Budget), navigating back to Tab 1 allows that service to be unchecked and removed from `Service Interested In`.
  - Saving creates an orphaned record: the Budget tab continues to retain financial allocations for a service that no longer exists in Project Details.
- **Expected Behavior:**
  - Configured services must be locked and disabled from removal in the `Service Interested In` multi-select menu.
- **Automated Verification:**
  - Test: `tests/UI/test_project_tab1_details.py::test_tab1_configured_service_removal_protection_audit`

---

### Defect 7: `DEF-007` — Project Amount on Show All Projects (/projects) Displayed as INR (₹) for Foreign Projects
- **Type:** **DEFECT**
- **Severity:** Major (Currency Inversion & Listing Parity)
- **Module:** Projects Listing (`https://infusive-front.jobvritta.com/projects`)
- **Observed Behavior:**
  - On `/projects`, the `Project Amount` column previously hardcoded the Indian Rupee symbol (`₹`) for foreign projects configured in USD (`$`).
- **Expected Behavior:**
  - The `Project Amount` column must format amounts dynamically using the project's native currency symbol (`$`).
- **Status:** **VERIFIED FIXED**
- **Verification Evidence:** Confirmed on staging via user screenshot `media_1794910936274_b542d33c.jpg` and `media_1794910977425_2b4d0db6.png`:
  - `Apex Global Solutions LLC - Project` (`AGS_POC_USD`) has Monthly Budget `$25.00` in USD.
  - The master `Show All Projects` table now displays **`$25.00`** in the `PROJECT AMOUNT` column with the **`$`** symbol correctly rendered.

---

### Defect 8: `DEF-008` — Customer Profile Currency Parity & Default Toggle
- **Type:** **DEFECT / LOCALIZATION INCONSISTENCY**
- **Severity:** Medium / Major
- **Module:** Customer Details (`/customers/{id}`) → Overview & Invoices Tabs
- **Current Live Status (Audited 17-Nov-2026):**
  1. **Line-Item Invoices Fixed:** In `/customers/{id}` → Invoices tab, the table rows **now correctly display their native currency**:
     - USD invoices display with **`$`** (e.g., `INV-2026-0008` &rarr; `$10.00`, `INV-2026-0004` &rarr; `$25.00`).
     - EUR invoices display with **`€`** (e.g., `INV-2026-0009` &rarr; `€11.94`, `INV-2026-0007` &rarr; `€11.31`).
     - The previous bug where individual foreign invoices rendered with `₹` is **FIXED** in the table ledger.
  2. **Remaining Defect (KPI Cards Default to INR):**
     - For international customers (e.g., `Apex Global Solutions LLC` in the United States), both the **Overview** and **Invoices** tabs hardcode the default currency toggle to **`₹ INR`**.
     - As a result, the summary KPI cards initially render in Indian Rupees:
       - `TOTAL OUTSTANDING`: `₹15,144.45`
       - `DUE IN NEXT 7 DAYS`: `₹1,243.64`
     - Only when an administrator manually clicks the `[$ USD]` toggle does it recalculate to `$160.70`.
  3. **Associated Defect (Project Eye Icon HTTP 500):**
     - On `/customers/{id}` → Projects tab, clicking the Eye icon (`👁️`) makes an API call:
       `GET /api/ProjectResourceAllocation/ProjectResourceCost/{projectId}` which fails with **HTTP 500 Internal Server Error**, displaying a red error toast:
       *"An error occurred while calculating project resource cost."*
- **Expected Behavior:**
  1. If the customer's billing country is `United States` (or currency is `USD`), the currency toggle must **default to `[$ USD]`**, not `[₹ INR]`.
  2. Fix the backend 500 exception on `ProjectResourceCost` calculation.
- **Automated Verification:**
  - Test Suite: `tests/UI/test_audit_customer_def008_all_tabs.py` (Headed execution verified).

---

### Defect 9: `DEF-009` — GSTIN Label Should Be Country-Specific for Global Customers
- **Type:** **DEFECT**
- **Severity:** Medium (Localization & Internationalization Discrepancy)
- **Priority:** Medium
- **Module:** Customer Management → Customer Details (`/customers/{id}`) → Tab 4 (Client Profile) → Sub-Tab 3 (Tax Details)
- **Title:** GSTIN Label Hardcoded for Global Customers (Fails to Dynamically Adapt to EIN for US or VAT for UK)
- **Steps to Reproduce:**
  1. Navigate to Customers (`/customers`).
  2. Open any customer profile (`/customers/{id}`).
  3. Go to `Client Profile` (Tab 4) → `Tax Details` (Sub-Tab 3).
  4. Change the billing / tax country to **United States** (or United Kingdom).
  5. Observe the tax ID field label and input placeholder.
- **Observed Behavior:**
  - The tax identification field remains labeled as **`GSTIN`** (Goods and Services Tax Identification Number), which is strictly an Indian domestic tax terminology.
  - Indian tax terminology is presented to international clients in the US, UK, and Europe.
- **Expected Behavior:**
  - The tax field label, placeholder, and format validation should dynamically adapt based on the selected country:
    - **India:** `GSTIN` (15-character alphanumeric format: `29ABCDE1234F1Z5`)
    - **United States:** `EIN` (Employer Identification Number / `Tax ID`, format: `XX-XXXXXXX`)
    - **United Kingdom / European Union:** `VAT Number` (e.g., `GB999 9999 73`)
    - **Other / Global:** `Tax Identification Number (TIN)`
- **Automated Verification:**
  - Test: `tests/UI/test_bug_customer_tax_gst_terminology.py::test_dynamic_country_tax_label_localization`

---

### Defect 10: `DEF-010` — Inactive Billing Plan: User-Edited Next Invoice Date Is Silently Overridden by Backend Engine
- **Type:** **DEFECT & DATA INTEGRITY DISCREPANCY**
- **Severity:** Medium / High
- **Priority:** High
- **Module:** Billing Plans (`/allBillingPlans` → `Update Billing Plan` Modal & Backend Controller `PUT /api/projects/{projectId}/billing/{planId}`)
- **Title:** Setting Next Invoice Date on Inactive Plan Is Silently Discarded by Backend Recalculation Engine, Leaving Dates Unchanged
- **Steps to Reproduce:**
  1. Navigate to Billing Plans (`/allBillingPlans`).
  2. Locate a recurring plan (e.g. `Apex Global Solutions LLC - Project`, Row 1) and ensure its status is `Inactive` (Stopped).
  3. Notice the table shows `NEXT INVOICE`: `30-11-2026`.
  4. Click the Edit action (pencil icon) to open the `Update Billing Plan` modal.
  5. In the modal, change `Next Invoice Date *` to today's date (e.g., `17/11/2026` / `2026-11-17`).
  6. Scroll down to the modal footer and click `Update Plan`.
  7. On the duplicate alert dialog, click `Create anyway`.
  8. Observe the network payload, backend response, and table row.
- **Observed Behavior:**
  1. The frontend correctly submits the user's date in the payload:
     `PUT /api/projects/1/billing/5` with `{"nextInvoiceDate": "2026-11-17"}`.
  2. However, the backend responds with `200 OK` returning:
     `{"id": 5, "nextInvoiceDate": "2026-12-01T00:00:00"}`.
     The backend recalculation engine completely discards/overwrites the user-entered date, recalculating automatically based on the recurring interval (Semi-Monthly: ~15 days from start date).
  3. The table `/allBillingPlans` refreshes and displays `NEXT INVOICE`: `30-11-2026` ("still remain same as it is").
  4. The user receives a successful toast (`"Billing plan updated"`), falsely implying that their date modification succeeded.
  5. In addition, the duplicate dialog confusingly asks *"Do you still want to create this plan? Cancel / Create anyway"*, when updating an existing plan.
- **Expected Behavior & Recommended Resolution:**
  - **Option A (Architectural Lockout - Recommended per `SUG-001`):**
    When a billing plan is in `Inactive` (Stopped) state, `Next Invoice Date` should be **disabled / read-only**. Since invoicing is stopped, scheduling next dates is meaningless and confusing.
  - **Option B (Honor Explicit User Overrides):**
    If manual date overrides are permitted, the backend `PUT /api/projects/{id}/billing/{id}` endpoint must persist the user's submitted `nextInvoiceDate` rather than silently recalculating and replacing it.
  - **Dialog Copy Fix:** On edit/update, the duplicate prompt should state *"Update anyway"* instead of *"Create anyway"*.
- **Automated Verification:**
  - Automated network trace captured live: `PUT /api/projects/1/billing/5` -> sent `2026-11-17`, returned `2026-12-01T00:00:00`.

---

## 3. Product Suggestions & Architectural Enhancements

### Suggestion 1: `SUG-001` — Inactive Project Read-Only Lockout Policy Across Sub-Modules
- **Type:** **SUGGESTION (Architectural Policy)**
- **Priority:** High
- **Module:** Project Management (`/project-details`) → Tabs 2, 3, 4, 5
- **Proposed Enhancement:**
  When a project status is `Inactive`, enforce a strict **Read-Only / Frozen State**:
  1. **Tab 2 (Budget):** Disable "Configure Budget" & "Add Service" buttons; make budget rows non-editable.
  2. **Tab 3 (Resources):** Disable "Assign Resource" / "Add Member" button; prevent modifying member hours.
  3. **Tab 4 (Tasks):** Disable "Create Task" button; block timesheet/hour logging against inactive projects.
  4. **Tab 5 (Billing):** Disable "Create Plan" button; past invoices remain accessible (read-only).
  5. **UI Banner:** Display top banner: *"🔒 Project Inactive — Editing budget, resources, tasks, and billing is locked. Reactivate project to make changes."*
  6. **Backend Enforcement:** Controllers return `400 Bad Request` if mutation is attempted on an Inactive project.
- **Automated Verification:**
  - Test Suite: `tests/UI/test_project_inactive_lockout.py`

---

### Suggestion 2: `SUG-002` — Duplicate Billing Plan Overlapping Date Range Protection
- **Type:** **SUGGESTION (Backend Logic Enhancement)**
- **Priority:** High
- **Module:** Billing API (`[HttpPost("check-duplicate")]`)
- **Proposed Enhancement:**
  - Current backend query only checks exact start date equality: `c.StartDate == start`.
  - If a 3-month recurring plan exists from Nov 14 to Feb 14, creating a plan on Nov 15 bypasses the duplicate modal and double-bills the client every month.
  - **Proposed Fix in LINQ Query:**
    ```csharp
    (c.StartDate == start || (c.BillingType == BillingType.Recurring && start >= c.StartDate && (c.EndDate == null || start <= c.EndDate)))
    ```
- **Automated Verification:**
  - Test: `tests/UI/test_project_billing_services.py::test_recurring_billing_plan_overlapping_date_range_validation`

---

### Suggestion 3: `SUG-003` — Deactivation & Reactivation Confirmation Modal Lifecycle
- **Type:** **SUGGESTION (UX & Billing Governance)**
- **Priority:** Medium
- **Module:** Project Details (Tab 1 Status Toggle)
- **Proposed Enhancement:**
  1. **When marking Project `Inactive` (with active recurring plan):**
     Display modal:
     > *"Active Recurring Billing Plan Detected: A recurring billing plan exists for this project from [Start Date] to [End Date]. Since you are marking this project as Inactive, how would you like to handle future recurring invoices?"*
     > **Buttons:** `[ Stop Billing ]` (Recommended) | `[ Continue Billing ]` | `[✕]` (Cancel/Abort)
  2. **When reactivating Project `Active` (with remaining plan dates):**
     Display modal:
     > *"Paused Billing Plan Detected: Project has a paused recurring plan with remaining billing cycles through [End Date]. Would you like to resume automatic invoice generation for remaining dates?"*
     > **Buttons:** `[ Resume Billing ]` | `[ Keep Billing Stopped ]` | `[✕]` (Cancel/Abort)
  3. **Invoice Immutability:** Generated invoices remain 100% untouched when deactivating.

---

### Suggestion 4: `SUG-004` — Remove "Days" Unit from Service Budget Duration Dropdown
- **Type:** **SUGGESTION (UI Simplification)**
- **Priority:** Low
- **Module:** Service Budget (`/project-details` Tab 2)
- **Proposed Enhancement:**
  - Remove `Days` (`value="1"`) from the duration unit dropdown.
  - Retain only `Months` (`value="2"`) and `Years` (`value="3"`).
  - Eliminates fractional day-to-month calculation anomalies and aligns with monthly agency retainer contracts.

---

### Suggestion 5: `SUG-005` — Multi-Plan Traceability & Distinction Architecture Gap
- **Type:** **SUGGESTION (Architecture & UX Governance)**
- **Priority:** High
- **Module:** Billing Plans (`/allBillingPlans`) & Invoices Ledger (`/invoice-list-page`)
- **Problem Statement (The Gap):**
  When a single customer or project has $N$ billing plans (e.g. `Apex Global Solutions LLC` has 5 recurring plans), all rows display identical `CUSTOMER`, identical `PROJECT`, identical `START`, identical `FREQUENCY`, and identical `AMOUNTS`:
  1. **No Plan Identifier:** The table uses row serial numbers (`1, 2, 3...`) rather than a persistent unique Business Plan ID (e.g., `PLAN-001`, `BP-005`).
  2. **No Plan Name / Nickname:** When setting up a billing plan, there is no label (e.g. *"PPC Monthly Retainer"*, *"SEO Optimization"*, *"Web Development Milestone 1"*).
  3. **No Services Column:** The table hides which service(s) are bundled inside each plan. An administrator must open the edit modal for every row to see what service is being billed.
  4. **Dead "Invoices" Number (No Drilldown):** The `INVOICES` column shows `1` or `2` as plain unclickable text. There is no link, modal, or filter to see *which* invoice numbers belong to *which* plan.
  5. **Invoices Ledger Has Zero Plan Lineage:** In `/invoice-list-page`, invoices display the Project Name, but have no `Billing Plan ID` or plan reference. An accountant cannot trace an invoice back to its originating billing plan.
  6. **High Operational Risk:** An operator wishing to stop or modify a specific service (e.g. PPC) could accidentally stop another identical-looking plan (e.g. SEO).
- **Proposed Engineering Solution:**
  1. **Auto-Generated Plan Name Algorithm:** Format: `{Initials}-{DDMonYY}-{HHmm}` (e.g. `AGS-17Nov26-1015`, `AGS-17Nov26-1430`). Displayed prominently with a `Recurring` pill, exactly mimicking the `INV-2026-0007` format from the Invoices ledger.
  2. **Add Customer Column:** Display `CUSTOMER` (`Apex Global Solutions LLC`) as a dedicated column; remove redundant `PROJECT` column in `/project-details` (Tab 5).
  3. **Minimalist Services Display:** Add a `SERVICES` column showing plain-text tags (e.g. `PPC`, `SEO`) with zero emojis or heavy SVGs.
  4. **Clickable `+N more` Services Drilldown Modal:** For multi-service bundles, render top 2 tags followed by a clickable `+3 more` badge. Clicking `+3 more` triggers the itemized **Services in Billing Plan Modal** showing:
     - Header: Plan Name, Customer, Services Count badge.
     - Table: `#`, `SERVICE NAME` (clean text, no emojis), `DESCRIPTION`, `QTY`, `UNIT PRICE`, `TAX`, `TOTAL`.
     - Footer: Frequency, Subtotal, GST, Total.
  5. **5th Metric KPI Card:** Add `INACTIVE` metric card (e.g., `1 stopped plan`) on top alongside `Total Plans`, `Active`, `Due`, and `Recurring`.
  6. **Clickable Invoices Link:** Make the `INVOICES` count a clickable hyperlink that filters `/invoice-list-page?planId=X` or opens a quick drawer showing linked invoice numbers (`INV-2026-0002`).
  7. **Cross-Module Invoices Ledger Column:** Add a `Billing Plan` column in `/invoice-list-page` and print the `Plan ID` on the invoice PDF.
