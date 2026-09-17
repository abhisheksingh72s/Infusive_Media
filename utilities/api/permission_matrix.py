import csv
import logging
import os
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

EXCEL_COLUMNS = [
    "Page",
    "Page in Stage",
    "Page in Prod",
    "Feature",
    "Feature in Stage",
    "Feature in Prod",
    "Stage Permission",
    "Prod Permission",
    "Status",
    "Difference"
]


def build_permission_matrix(
    stage_json: Any,
    prod_json: Any,
    role: str = "Admin"
) -> List[Dict[str, Any]]:
    """
    Build structured Permission Matrix comparing Stage vs Prod permissions across Pages and Features.
    Performs full outer join (Stage + Prod) to capture all Pages & Features.

    Columns:
    - Page
    - Page in Stage ("Yes" / "No")
    - Page in Prod ("Yes" / "No")
    - Feature
    - Feature in Stage ("Yes" / "No" / "N/A")
    - Feature in Prod ("Yes" / "No" / "N/A")
    - Stage Permission ("TRUE" / "FALSE" / "N/A")
    - Prod Permission ("TRUE" / "FALSE" / "N/A")
    - Status ("PASS" / "FAIL")
    - Difference ("Page missing in Prod", "Feature missing in Prod", "Permission disabled in Prod", "Permission enabled in Prod", etc.)
    """
    stage_pages = stage_json if isinstance(stage_json, list) else (stage_json.get("permissions", []) if isinstance(stage_json, dict) else [])
    prod_pages = prod_json if isinstance(prod_json, list) else (prod_json.get("permissions", []) if isinstance(prod_json, dict) else [])

    stage_page_map = {}
    stage_feat_map = {}

    for p in stage_pages:
        if not isinstance(p, dict):
            continue
        p_id = p.get("id", "-")
        p_name = str(p.get("name") or p.get("label") or p.get("url") or f"Page_{p_id}").strip()
        p_key = (p_id, p_name.lower())
        p_perm = bool(p.get("permission", False))

        stage_page_map[p_key] = {"id": p_id, "name": p_name, "perm": p_perm}

        for f in (p.get("features") or []):
            if not isinstance(f, dict):
                continue
            f_id = f.get("id", "-")
            f_name = str(f.get("name") or f.get("label") or f.get("url") or f"Feature_{f_id}").strip()
            f_key = (p_key, f_id, f_name.lower())
            f_perm = bool(f.get("permission", False))

            stage_feat_map[f_key] = {"id": f_id, "name": f_name, "perm": f_perm, "page_id": p_id, "page_name": p_name}

    prod_page_map = {}
    prod_feat_map = {}

    for p in prod_pages:
        if not isinstance(p, dict):
            continue
        p_id = p.get("id", "-")
        p_name = str(p.get("name") or p.get("label") or p.get("url") or f"Page_{p_id}").strip()
        p_key = (p_id, p_name.lower())
        p_perm = bool(p.get("permission", False))

        prod_page_map[p_key] = {"id": p_id, "name": p_name, "perm": p_perm}

        for f in (p.get("features") or []):
            if not isinstance(f, dict):
                continue
            f_id = f.get("id", "-")
            f_name = str(f.get("name") or f.get("label") or f.get("url") or f"Feature_{f_id}").strip()
            f_key = (p_key, f_id, f_name.lower())
            f_perm = bool(f.get("permission", False))

            prod_feat_map[f_key] = {"id": f_id, "name": f_name, "perm": f_perm, "page_id": p_id, "page_name": p_name}

    def find_page_in_target(p_key, target_map):
        if p_key in target_map:
            return target_map[p_key]
        p_id, p_name_lower = p_key
        for k, v in target_map.items():
            if (p_id != "-" and k[0] == p_id) or (k[1] == p_name_lower):
                return v
        return None

    def find_feat_in_target(f_key, target_map):
        if f_key in target_map:
            return target_map[f_key]
        p_key, f_id, f_name_lower = f_key
        for k, v in target_map.items():
            if k[0][1] == p_key[1] or (p_key[0] != "-" and k[0][0] == p_key[0]):
                if (f_id != "-" and k[1] == f_id) or (k[2] == f_name_lower):
                    return v
        return None

    all_page_keys = list(stage_page_map.keys())
    for k in prod_page_map.keys():
        if not find_page_in_target(k, stage_page_map):
            all_page_keys.append(k)

    matrix_rows = []

    for p_key in all_page_keys:
        stg_page = stage_page_map.get(p_key) or find_page_in_target(p_key, stage_page_map)
        prod_page = prod_page_map.get(p_key) or find_page_in_target(p_key, prod_page_map)

        p_name = (stg_page or prod_page)["name"]

        page_in_stg = "Yes" if stg_page else "No"
        page_in_prod = "Yes" if prod_page else "No"

        feat_in_stg = "Yes" if stg_page else "No"
        feat_in_prod = "Yes" if prod_page else "No"

        if stg_page:
            stg_perm_str = "TRUE" if stg_page["perm"] else "FALSE"
        else:
            stg_perm_str = "N/A"

        if prod_page:
            prod_perm_str = "TRUE" if prod_page["perm"] else "FALSE"
        else:
            prod_perm_str = "N/A"

        # Difference & Status logic for Page row
        if stg_page and not prod_page:
            status = "FAIL"
            diff = "Page missing in Prod"
        elif not stg_page and prod_page:
            status = "FAIL"
            diff = "Page missing in Stage"
        else:
            stg_perm = stg_page["perm"]
            prod_perm = prod_page["perm"]
            if stg_perm == prod_perm:
                status = "PASS"
                diff = ""
            elif stg_perm and not prod_perm:
                status = "FAIL"
                diff = "Permission disabled in Prod"
            else:
                status = "FAIL"
                diff = "Permission enabled in Prod"

        matrix_rows.append({
            "Role": role,
            "Page": p_name,
            "Page in Stage": page_in_stg,
            "Page in Prod": page_in_prod,
            "Feature": p_name,
            "Feature in Stage": feat_in_stg,
            "Feature in Prod": feat_in_prod,
            "Stage Permission": stg_perm_str,
            "Prod Permission": prod_perm_str,
            "Status": status,
            "Difference": diff,
            "Type": "Page"
        })

        # Process features for this page
        all_feat_keys = []
        for k, v in stage_feat_map.items():
            if k[0] == p_key or k[0][1] == p_key[1]:
                all_feat_keys.append(k)
        for k, v in prod_feat_map.items():
            if k[0] == p_key or k[0][1] == p_key[1]:
                if not find_feat_in_target(k, stage_feat_map):
                    all_feat_keys.append(k)

        for f_key in all_feat_keys:
            stg_feat = stage_feat_map.get(f_key) or find_feat_in_target(f_key, stage_feat_map)
            prod_feat = prod_feat_map.get(f_key) or find_feat_in_target(f_key, prod_feat_map)

            f_name = (stg_feat or prod_feat)["name"]

            f_in_stg = "Yes" if stg_feat else "No"
            f_in_prod = "Yes" if prod_feat else "No"

            if stg_feat:
                f_stg_perm_str = "TRUE" if stg_feat["perm"] else "FALSE"
            else:
                f_stg_perm_str = "N/A"

            if prod_feat:
                f_prod_perm_str = "TRUE" if prod_feat["perm"] else "FALSE"
            else:
                f_prod_perm_str = "N/A"

            # Difference & Status logic for Feature row
            if stg_page and not prod_page:
                f_status = "FAIL"
                f_diff = "Page missing in Prod"
            elif not stg_page and prod_page:
                f_status = "FAIL"
                f_diff = "Page missing in Stage"
            elif stg_feat and not prod_feat:
                f_status = "FAIL"
                f_diff = "Feature missing in Prod"
            elif not stg_feat and prod_feat:
                f_status = "FAIL"
                f_diff = "Feature missing in Stage"
            else:
                f_stg_perm = stg_feat["perm"]
                f_prod_perm = prod_feat["perm"]
                if f_stg_perm == f_prod_perm:
                    f_status = "PASS"
                    f_diff = ""
                elif f_stg_perm and not f_prod_perm:
                    f_status = "FAIL"
                    f_diff = "Permission disabled in Prod"
                else:
                    f_status = "FAIL"
                    f_diff = "Permission enabled in Prod"

            matrix_rows.append({
                "Role": role,
                "Page": p_name,
                "Page in Stage": page_in_stg,
                "Page in Prod": page_in_prod,
                "Feature": f_name,
                "Feature in Stage": f_in_stg,
                "Feature in Prod": f_in_prod,
                "Stage Permission": f_stg_perm_str,
                "Prod Permission": f_prod_perm_str,
                "Status": f_status,
                "Difference": f_diff,
                "Type": "Feature"
            })

    return matrix_rows


def format_matrix_table(matrix_rows: List[Dict[str, Any]]) -> str:
    """Format Permission Matrix rows into clean ASCII / Markdown table for terminal log."""
    if not matrix_rows:
        return "No Permission Matrix data available."

    headers = EXCEL_COLUMNS

    widths = {h: len(h) for h in headers}
    for row in matrix_rows:
        for h in headers:
            val_str = str(row.get(h, ""))
            widths[h] = max(widths[h], len(val_str))

    header_line = "| " + " | ".join(f"{h:<{widths[h]}}" for h in headers) + " |"
    sep_line = "|-" + "-|-".join("-" * widths[h] for h in headers) + "-|"

    body_lines = []
    for row in matrix_rows:
        line = "| " + " | ".join(f"{str(row.get(h, '')):<{widths[h]}}" for h in headers) + " |"
        body_lines.append(line)

    lines = [
        "",
        "                                  PERMISSION COMPARISON MATRIX",
        "=" * len(header_line),
        header_line,
        sep_line,
        "\n".join(body_lines),
        "=" * len(header_line)
    ]
    return "\n".join(lines)


def release_excel_lock(filepath: Path):
    """Option 2: Force release Excel lock if Excel process currently holds write lock on report file."""
    try:
        if not filepath.exists():
            return
        try:
            with open(filepath, "r+"):
                pass
        except PermissionError:
            logger.info("File '%s' is open in Excel. Force-releasing lock by closing Excel process...", filepath.name)
            subprocess.run("taskkill /F /IM excel.exe", shell=True, capture_output=True)
            time.sleep(0.5)
    except Exception as err:
        logger.debug("Lock release exception: %s", err)


def auto_open_excel(filepath: Path):
    """Option 3: Automatically open the freshly updated Excel report in Microsoft Excel."""
    try:
        out_str = str(filepath.resolve())
        logger.info("Auto-opening updated Excel report in Microsoft Excel: %s", out_str)
        if os.name == "nt":
            os.startfile(out_str)
        else:
            subprocess.Popen(["open", out_str])
    except Exception as err:
        logger.warning("Could not auto-open Excel file: %s", err)


def export_multi_role_matrix_to_excel(
    role_matrices: Dict[str, List[Dict[str, Any]]],
    filepath: str = "reports/Permission_Comparison_Matrix.xlsx",
    auto_open: bool = True
) -> Path:
    """
    Export Permission Matrix rows into a multi-sheet Microsoft Excel (.xlsx) workbook.

    Worksheets created:
    - Summary (High level metrics, pass/fail totals, compliance %)
    - Admin
    - BDM
    - Pre Sales
    - Team Lead
    - Manager
    """
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter

    out_path = Path(filepath).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Option 2: Force release Excel lock before saving
    release_excel_lock(out_path)

    wb = openpyxl.Workbook()
    wb.remove(wb.active)

    # Styling definitions
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="1F497D", end_color="1F497D", fill_type="solid")
    summary_header_fill = PatternFill(start_color="002060", end_color="002060", fill_type="solid")

    center_align = Alignment(horizontal="center", vertical="center")
    left_align = Alignment(horizontal="left", vertical="center")

    thin_border = Border(
        left=Side(style="thin", color="D9D9D9"),
        right=Side(style="thin", color="D9D9D9"),
        top=Side(style="thin", color="D9D9D9"),
        bottom=Side(style="thin", color="D9D9D9")
    )

    double_bottom_border = Border(
        left=Side(style="thin", color="D9D9D9"),
        right=Side(style="thin", color="D9D9D9"),
        top=Side(style="thin", color="000000"),
        bottom=Side(style="double", color="000000")
    )

    pass_fill = PatternFill(start_color="D9EAD3", end_color="D9EAD3", fill_type="solid")
    pass_font = Font(name="Calibri", size=11, bold=True, color="274E13")

    fail_fill = PatternFill(start_color="F4CCCC", end_color="F4CCCC", fill_type="solid")
    fail_font = Font(name="Calibri", size=11, bold=True, color="990000")

    diff_fill = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")

    # 1. Create SUMMARY Sheet
    ws_summary = wb.create_sheet(title="Summary")
    ws_summary.freeze_panes = "A2"
    summary_headers = ["Role", "Total Pages", "Total Features", "Total Pass", "Total Fail", "Differences Found", "Compliance %"]

    ws_summary.append(summary_headers)
    for col_num in range(1, len(summary_headers) + 1):
        cell = ws_summary.cell(row=1, column=col_num)
        cell.font = header_font
        cell.fill = summary_header_fill
        cell.alignment = center_align

    roles_order = ["Admin", "BDM", "Pre Sales", "Team Lead", "Manager"]

    grand_total_pages = 0
    grand_total_features = 0
    grand_total_pass = 0
    grand_total_fail = 0
    grand_total_diff = 0

    for row_idx, role_name in enumerate(roles_order, start=2):
        rows = role_matrices.get(role_name, [])

        tot_pages = sum(1 for r in rows if r.get("Type") == "Page")
        tot_feats = sum(1 for r in rows if r.get("Type") == "Feature")
        tot_pass = sum(1 for r in rows if r.get("Status") == "PASS")
        tot_fail = sum(1 for r in rows if r.get("Status") == "FAIL")
        tot_diff = sum(1 for r in rows if r.get("Difference"))
        tot_items = len(rows)

        compliance_pct = (tot_pass / tot_items * 100.0) if tot_items > 0 else 100.0

        grand_total_pages += tot_pages
        grand_total_features += tot_feats
        grand_total_pass += tot_pass
        grand_total_fail += tot_fail
        grand_total_diff += tot_diff

        row_vals = [role_name, tot_pages, tot_feats, tot_pass, tot_fail, tot_diff, f"{compliance_pct:.1f}%"]
        ws_summary.append(row_vals)

        for col_num in range(1, len(summary_headers) + 1):
            cell = ws_summary.cell(row=row_idx, column=col_num)
            cell.border = thin_border
            cell.alignment = center_align if col_num > 1 else left_align

            if col_num == 7: # Compliance %
                if compliance_pct == 100.0:
                    cell.fill = pass_fill
                    cell.font = pass_font
                else:
                    cell.fill = fail_fill
                    cell.font = fail_font

    # Grand Total Row
    tot_items_all = grand_total_pass + grand_total_fail
    grand_compliance = (grand_total_pass / tot_items_all * 100.0) if tot_items_all > 0 else 100.0
    gt_row = ["GRAND TOTAL", grand_total_pages, grand_total_features, grand_total_pass, grand_total_fail, grand_total_diff, f"{grand_compliance:.1f}%"]
    ws_summary.append(gt_row)

    gt_row_idx = len(roles_order) + 2
    for col_num in range(1, len(summary_headers) + 1):
        cell = ws_summary.cell(row=gt_row_idx, column=col_num)
        cell.font = Font(name="Calibri", size=11, bold=True)
        cell.border = double_bottom_border
        cell.alignment = center_align if col_num > 1 else left_align

    # Auto Column Widths for Summary Sheet
    for col in ws_summary.columns:
        max_len = max(len(str(cell.value or "")) for cell in col)
        col_letter = get_column_letter(col[0].column)
        ws_summary.column_dimensions[col_letter].width = max(max_len + 4, 15)

    # 2. Create ROLE Sheets (Admin, BDM, Pre Sales, Team Lead, Manager)
    headers = EXCEL_COLUMNS

    for role_name in roles_order:
        ws = wb.create_sheet(title=role_name)
        ws.freeze_panes = "A2"

        ws.append(headers)
        for col_num in range(1, len(headers) + 1):
            cell = ws.cell(row=1, column=col_num)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = center_align

        rows = role_matrices.get(role_name, [])

        for row_idx, r_data in enumerate(rows, start=2):
            r_vals = [r_data.get(h, "") for h in headers]
            ws.append(r_vals)

            status_val = str(r_data.get("Status", "")).upper()
            diff_val = str(r_data.get("Difference", ""))
            is_fail = (status_val == "FAIL")

            for col_num, h in enumerate(headers, start=1):
                cell = ws.cell(row=row_idx, column=col_num)
                cell.border = thin_border

                if h in ["Page in Stage", "Page in Prod", "Feature in Stage", "Feature in Prod", "Stage Permission", "Prod Permission", "Status"]:
                    cell.alignment = center_align
                else:
                    cell.alignment = left_align

                if is_fail:
                    # Highlight the ENTIRE row with soft red/pink fill for FAIL
                    cell.fill = fail_fill
                    if h == "Status":
                        cell.font = fail_font
                    elif h == "Difference" and diff_val:
                        cell.font = Font(name="Calibri", size=11, bold=True, color="990000")
                else:
                    if h == "Status":
                        cell.fill = pass_fill
                        cell.font = pass_font


        # Auto-adjust column widths
        for col in ws.columns:
            max_len = max(len(str(cell.value or "")) for cell in col)
            col_letter = get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = max(max_len + 4, 12)

    try:
        wb.save(str(out_path))
        logger.info("Updated Excel (.xlsx) Permission Matrix report at: %s", out_path)
    except PermissionError:
        release_excel_lock(out_path)
        wb.save(str(out_path))
        logger.info("Force-updated Excel (.xlsx) Permission Matrix report at: %s", out_path)

    # Option 3: Auto-open updated Excel report in Microsoft Excel
    if auto_open:
        auto_open_excel(out_path)

    return out_path


export_matrix_to_excel = export_multi_role_matrix_to_excel
export_matrix_to_csv = export_multi_role_matrix_to_excel
