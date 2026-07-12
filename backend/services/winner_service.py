import os
import openpyxl
from io import BytesIO

class ValidationError(Exception):
    def __init__(self, errors):
        super().__init__("; ".join(errors))
        self.errors = errors

class WinnerService:
    # Column mapping configurations (case-insensitive)
    HEADER_CANDIDATES = {
        "employee_id": ["employee id", "employee_id", "employeeid", "id", "emp id", "empid"],
        "name": ["name", "participant name", "employee name", "fullname", "full name"],
        "weight": ["weight", "weight (kg)", "weight(kg)", "weight (lbs)", "weight(lbs)", "wt"],
        "waist": ["waist", "waist (in)", "waist (cm)", "waist(in)", "waist(cm)"],
        "hip": ["hip", "hip (in)", "hip (cm)", "hip(in)", "hip(cm)"]
    }

    @staticmethod
    def clean_employee_id(val) -> str:
        if val is None:
            return ""
        val_str = str(val).strip()
        # Remove trailing .0 from floating numbers if read as such
        if val_str.endswith(".0"):
            val_str = val_str[:-2]
        return val_str

    @classmethod
    def parse_and_validate_sheet(cls, file_data: bytes, sheet_label: str) -> tuple[dict, list[str]]:
        """
        Parses an Excel sheet from bytes.
        Returns:
            data: dict of {employee_id: {name, weight, waist, hip, whr}}
            errors: list of string validation errors/warnings
        """
        errors = []
        data = {}

        try:
            wb = openpyxl.load_workbook(BytesIO(file_data), data_only=True)
            ws = wb.active
        except Exception as e:
            return {}, [f"[{sheet_label}] Invalid Excel format or file could not be read: {str(e)}"]

        if not ws or ws.max_row == 0:
            return {}, [f"[{sheet_label}] Spreadsheet is empty"]

        # Read first row for headers
        header_row = [cell.value for cell in ws[1]]
        header_indices = {}

        # Resolve headers
        for col_name, candidates in cls.HEADER_CANDIDATES.items():
            found_idx = None
            for idx, cell_val in enumerate(header_row):
                if cell_val is not None:
                    normalized_cell = str(cell_val).strip().lower()
                    if normalized_cell in candidates:
                        found_idx = idx
                        break
            if found_idx is None:
                errors.append(f"[{sheet_label}] Missing required column for '{col_name.replace('_', ' ').title()}'")
            else:
                header_indices[col_name] = found_idx

        if errors:
            return {}, errors

        processed_ids = set()

        # Parse rows starting from row 2
        for row_idx in range(2, ws.max_row + 1):
            row_cells = [ws.cell(row=row_idx, column=col_idx).value for col_idx in range(1, ws.max_column + 1)]
            
            # Check if row is completely empty
            if all(val is None or str(val).strip() == "" for val in row_cells):
                continue

            # Read raw values
            raw_id = row_cells[header_indices["employee_id"]]
            raw_name = row_cells[header_indices["name"]]
            raw_weight = row_cells[header_indices["weight"]]
            raw_waist = row_cells[header_indices["waist"]]
            raw_hip = row_cells[header_indices["hip"]]

            emp_id = cls.clean_employee_id(raw_id)
            if not emp_id:
                errors.append(f"[{sheet_label}] Row {row_idx}: Employee ID is missing")
                continue

            if emp_id in processed_ids:
                errors.append(f"[{sheet_label}] Row {row_idx}: Duplicate Employee ID '{emp_id}'")
                continue
            processed_ids.add(emp_id)

            # Name validation
            name = str(raw_name).strip() if raw_name is not None else ""
            if not name:
                errors.append(f"[{sheet_label}] Row {row_idx} (Employee ID: {emp_id}): Name is missing")

            # Numeric fields validation
            numeric_vals = {}
            for field, val in [("weight", raw_weight), ("waist", raw_waist), ("hip", raw_hip)]:
                if val is None or str(val).strip() == "":
                    errors.append(f"[{sheet_label}] Row {row_idx} (Employee ID: {emp_id}): {field.title()} is missing")
                    numeric_vals[field] = None
                else:
                    try:
                        f_val = float(str(val).strip())
                        if f_val <= 0:
                            errors.append(f"[{sheet_label}] Row {row_idx} (Employee ID: {emp_id}): {field.title()} must be greater than zero")
                            numeric_vals[field] = None
                        else:
                            numeric_vals[field] = f_val
                    except ValueError:
                        errors.append(f"[{sheet_label}] Row {row_idx} (Employee ID: {emp_id}): {field.title()} has invalid non-numeric value '{val}'")
                        numeric_vals[field] = None

            # Skip row if any of the numeric fields are invalid/missing
            if any(v is None for v in numeric_vals.values()):
                continue

            weight = numeric_vals["weight"]
            waist = numeric_vals["waist"]
            hip = numeric_vals["hip"]
            
            whr = waist / hip

            data[emp_id] = {
                "name": name,
                "weight": weight,
                "waist": waist,
                "hip": hip,
                "whr": whr
            }

        return data, errors

    @classmethod
    def calculate_results(cls, day0_data: dict, day45_data: dict, day90_data: dict) -> tuple[dict, list[dict], list[str]]:
        """
        Merges datasets and calculates final rankings and metrics.
        Returns:
            summary: dict containing stats & winner info
            rankings: list of dict rankings
            warnings: list of warning messages (e.g. missing participants in sheet(s))
        """
        warnings = []
        
        # Determine common participants in day 0 and day 90
        day0_ids = set(day0_data.keys())
        day90_ids = set(day90_data.keys())
        day45_ids = set(day45_data.keys())

        # Exclude list warnings
        only_in_day0 = day0_ids - day90_ids
        for eid in only_in_day0:
            warnings.append(f"Participant '{day0_data[eid]['name']}' ({eid}) is in Day 0 but missing in Day 90. Excluded from rankings.")

        only_in_day90 = day90_ids - day0_ids
        for eid in only_in_day90:
            warnings.append(f"Participant '{day90_data[eid]['name']}' ({eid}) is in Day 90 but missing in Day 0. Excluded from rankings.")

        common_ids = day0_ids & day90_ids
        if not common_ids:
            raise ValueError("No common participants found between Day 0 and Day 90 Excel sheets.")

        raw_results = []
        max_weight_loss_pct = 0.0
        max_whr_imp_pct = 0.0

        for eid in common_ids:
            d0 = day0_data[eid]
            d90 = day90_data[eid]

            # Weight Loss %: ((Day0Weight - Day90Weight) / Day0Weight) * 100
            weight_loss_pct = ((d0["weight"] - d90["weight"]) / d0["weight"]) * 100.0

            # WHR Improvement %: ((Day0WHR - Day90WHR) / Day0WHR) * 100
            whr_imp_pct = ((d0["whr"] - d90["whr"]) / d0["whr"]) * 100.0

            # Track highest values for normalization (denominators must be positive)
            if weight_loss_pct > max_weight_loss_pct:
                max_weight_loss_pct = weight_loss_pct
            if whr_imp_pct > max_whr_imp_pct:
                max_whr_imp_pct = whr_imp_pct

            # Warn if missing in Day 45
            if eid not in day45_ids:
                warnings.append(f"Participant '{d0['name']}' ({eid}) is missing in Day 45 (included in rankings, but graphs may be incomplete).")

            raw_results.append({
                "employee_id": eid,
                "name": d0["name"],
                "day0_weight": d0["weight"],
                "day90_weight": d90["weight"],
                "weight_loss_percent": weight_loss_pct,
                "day0_whr": d0["whr"],
                "day90_whr": d90["whr"],
                "whr_improvement_percent": whr_imp_pct
            })

        # Step 5 & 6: Normalize and compute final score
        norm_weight_denom = max_weight_loss_pct if max_weight_loss_pct > 0 else 1.0
        norm_whr_denom = max_whr_imp_pct if max_whr_imp_pct > 0 else 1.0

        for r in raw_results:
            # Scale each between 0–100, clamping lower bound to 0 (in case of weight gain / WHR degradation)
            r["normalized_weight"] = max(0.0, (r["weight_loss_percent"] / norm_weight_denom) * 100.0) if max_weight_loss_pct > 0 else 0.0
            r["normalized_whr"] = max(0.0, (r["whr_improvement_percent"] / norm_whr_denom) * 100.0) if max_whr_imp_pct > 0 else 0.0
            
            # Final Score = (NormalizedWeight * 0.5) + (NormalizedWHR * 0.5)
            r["final_score"] = (r["normalized_weight"] * 0.5) + (r["normalized_whr"] * 0.5)

        # Sort descending by Final Score
        sorted_results = sorted(raw_results, key=lambda x: x["final_score"], reverse=True)

        # Assign ranks
        for idx, r in enumerate(sorted_results, 1):
            r["rank"] = idx

        # Winner Details
        winner = sorted_results[0] if sorted_results else None

        summary = {
            "total_participants": len(sorted_results),
            "highest_weight_loss": round(max_weight_loss_pct, 2),
            "highest_whr_improvement": round(max_whr_imp_pct, 2),
            "winner_name": winner["name"] if winner else "N/A",
            "winner_employee_id": winner["employee_id"] if winner else "N/A",
            "winner_final_score": round(winner["final_score"], 2) if winner else 0.0
        }

        # Format numeric floats for display
        for r in sorted_results:
            r["day0_weight"] = round(r["day0_weight"], 2)
            r["day90_weight"] = round(r["day90_weight"], 2)
            r["weight_loss_percent"] = round(r["weight_loss_percent"], 2)
            r["day0_whr"] = round(r["day0_whr"], 4)
            r["day90_whr"] = round(r["day90_whr"], 4)
            r["whr_improvement_percent"] = round(r["whr_improvement_percent"], 2)
            r["normalized_weight"] = round(r["normalized_weight"], 2)
            r["normalized_whr"] = round(r["normalized_whr"], 2)
            r["final_score"] = round(r["final_score"], 2)

        return summary, sorted_results, warnings

    @classmethod
    def generate_excel_bytes(cls, rankings: list[dict], title: str) -> bytes:
        """Generates a styled Excel sheet using openpyxl and returns bytes."""
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = title[:31]

        header_fill = PatternFill("solid", fgColor="4F46E5")
        header_font = Font(bold=True, color="FFFFFF")
        center_align = Alignment(horizontal="center", vertical="center")
        left_align = Alignment(horizontal="left", vertical="center")
        right_align = Alignment(horizontal="right", vertical="center")
        
        thin_border = Border(
            left=Side(style='thin', color='DDDDDD'),
            right=Side(style='thin', color='DDDDDD'),
            top=Side(style='thin', color='DDDDDD'),
            bottom=Side(style='thin', color='DDDDDD')
        )

        headers = [
            "Rank", "Employee ID", "Name", 
            "Day 0 Weight", "Day 90 Weight", "Weight Loss %", 
            "Day 0 WHR", "Day 90 WHR", "WHR Improvement %", 
            "Final Score"
        ]

        for col_idx, h in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_idx, value=h)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = center_align
            cell.border = thin_border

        for row_idx, r in enumerate(rankings, 2):
            ws.cell(row=row_idx, column=1, value=r["rank"]).alignment = center_align
            ws.cell(row=row_idx, column=2, value=r["employee_id"]).alignment = center_align
            ws.cell(row=row_idx, column=3, value=r["name"]).alignment = left_align
            ws.cell(row=row_idx, column=4, value=r["day0_weight"]).alignment = right_align
            ws.cell(row=row_idx, column=5, value=r["day90_weight"]).alignment = right_align
            ws.cell(row=row_idx, column=6, value=r["weight_loss_percent"]).alignment = right_align
            ws.cell(row=row_idx, column=7, value=r["day0_whr"]).alignment = right_align
            ws.cell(row=row_idx, column=8, value=r["day90_whr"]).alignment = right_align
            ws.cell(row=row_idx, column=9, value=r["whr_improvement_percent"]).alignment = right_align
            ws.cell(row=row_idx, column=10, value=r["final_score"]).alignment = right_align

            # Add thin border to all cells in the row
            for col_idx in range(1, 11):
                ws.cell(row=row_idx, column=col_idx).border = thin_border

        # Set heights and auto widths
        ws.row_dimensions[1].height = 25
        for row in range(2, len(rankings) + 2):
            ws.row_dimensions[row].height = 20

        for col in ws.columns:
            max_len = max(len(str(cell.value or "")) for cell in col)
            ws.column_dimensions[col[0].column_letter].width = max(14, max_len + 3)

        buf = BytesIO()
        wb.save(buf)
        buf.seek(0)
        return buf.getvalue()
