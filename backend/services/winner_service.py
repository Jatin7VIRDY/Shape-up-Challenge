import os
import re
import openpyxl
from io import BytesIO

class ValidationError(Exception):
    def __init__(self, errors):
        super().__init__("; ".join(errors))
        self.errors = errors

class WinnerService:
    # Column mapping configurations (case-insensitive)
    HEADER_CANDIDATES = {
        "employee_id": [
            "employee id", "employee_id", "employeeid", "id", "emp id", "empid", 
            "emp_id", "emp code", "empcode", "employee code", "emp no", "empno", 
            "participant id", "user id", "sl. no.", "sl no", "sr no", "sr. no."
        ],
        "identifier_fallback": [
            "email-id", "email id", "email_id", "email", "phone no", "phone_no", 
            "phone", "mobile", "phone number", "mobile no", "mobile number"
        ],
        "name": [
            "name", "participant name", "employee name", "fullname", "full name", 
            "participant", "employee", "member name"
        ],
        "weight": [
            "weight", "weight (kg)", "weight(kg)", "weight (lbs)", "weight(lbs)", 
            "wt", "weight kg", "wt (kg)", "wt(kg)", "weight in kg", "initial weight", "final weight"
        ],
        "waist": [
            "waist", "waist (in)", "waist (cm)", "waist(in)", "waist(cm)", 
            "waist size", "waist (inches)", "waist(inches)", "waist in inches", "initial waist", "final waist", "waist circumference"
        ],
        "hip": [
            "hip", "hip (in)", "hip (cm)", "hip(in)", "hip(cm)", 
            "hip size", "hip (inches)", "hip(inches)", "hip in inches", "hips", "initial hip", "final hip", "hip circumference"
        ]
    }

    @staticmethod
    def clean_employee_id(val) -> str:
        if val is None:
            return ""
        val_str = str(val).strip()
        # Remove trailing .0 or .00 from floating numbers if read as such
        if re.match(r"^\d+\.0+$", val_str):
            val_str = val_str.split(".")[0]
        # Uppercase to ensure case-insensitive matching across files
        return val_str.upper()

    @staticmethod
    def clean_name(name_val) -> str:
        if name_val is None:
            return ""
        name = str(name_val).strip()
        # Clean trailing merged gender strings if present (e.g. "PavithraFemale" -> "Pavithra")
        if name.lower().endswith("female") and len(name) > 6 and name[-7] != " ":
            name = name[:-6].strip()
        elif name.lower().endswith("male") and len(name) > 4 and name[-5] != " ":
            name = name[:-4].strip()
        return name

    @classmethod
    def parse_and_validate_sheet(cls, file_data: bytes, sheet_label: str) -> tuple[dict, list[str]]:
        """
        Parses an Excel sheet from bytes.
        Validates only required calculation fields: Participant Identifier, Weight, Waist circumference, Hip circumference.
        Ignores completely blank rows and optional measurement fields (Email, BMI, BMR, Pressure, etc.).
        Returns:
            data: dict of {employee_id: {name, weight, waist, hip, whr}}
            errors: list of participant-specific validation error strings
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

        # Dynamically scan top rows (up to 15) to find the table header row
        header_row_idx = None
        header_indices = {}

        max_scan_row = min(15, ws.max_row)
        for r_idx in range(1, max_scan_row + 1):
            row_vals = [ws.cell(row=r_idx, column=c_idx).value for c_idx in range(1, ws.max_column + 1)]
            temp_indices = {}

            # 1. Resolve Name
            for c_idx, cell_val in enumerate(row_vals):
                if cell_val is not None and str(cell_val).strip().lower() in cls.HEADER_CANDIDATES["name"]:
                    temp_indices["name"] = c_idx
                    break

            # 2. Resolve Weight
            for c_idx, cell_val in enumerate(row_vals):
                if cell_val is not None and str(cell_val).strip().lower() in cls.HEADER_CANDIDATES["weight"]:
                    temp_indices["weight"] = c_idx
                    break

            # 3. Resolve Employee ID or Fallback Identifier (Email/Phone/Name)
            for c_idx, cell_val in enumerate(row_vals):
                if cell_val is not None and str(cell_val).strip().lower() in cls.HEADER_CANDIDATES["employee_id"]:
                    temp_indices["employee_id"] = c_idx
                    break
            if "employee_id" not in temp_indices:
                for c_idx, cell_val in enumerate(row_vals):
                    if cell_val is not None and str(cell_val).strip().lower() in cls.HEADER_CANDIDATES["identifier_fallback"]:
                        temp_indices["employee_id"] = c_idx
                        break
            if "employee_id" not in temp_indices and "name" in temp_indices:
                temp_indices["employee_id"] = temp_indices["name"]

            # 4. Resolve Waist & Hip (or Circumference fallback)
            for c_idx, cell_val in enumerate(row_vals):
                if cell_val is not None and str(cell_val).strip().lower() in cls.HEADER_CANDIDATES["waist"]:
                    temp_indices["waist"] = c_idx
                    break

            for c_idx, cell_val in enumerate(row_vals):
                if cell_val is not None and str(cell_val).strip().lower() in cls.HEADER_CANDIDATES["hip"]:
                    temp_indices["hip"] = c_idx
                    break

            # If Waist/Hip not found by name, check for columns containing "circumfer" or "circ"
            if "waist" not in temp_indices or "hip" not in temp_indices:
                circ_cols = []
                for c_idx, cell_val in enumerate(row_vals):
                    if cell_val is not None and ("circumfer" in str(cell_val).strip().lower() or "circ" in str(cell_val).strip().lower()):
                        circ_cols.append(c_idx)
                if len(circ_cols) >= 2:
                    if "waist" not in temp_indices:
                        temp_indices["waist"] = circ_cols[0]
                    if "hip" not in temp_indices:
                        temp_indices["hip"] = circ_cols[1]
                elif len(circ_cols) == 1 and "waist" not in temp_indices:
                    temp_indices["waist"] = circ_cols[0]

            # We MUST have at least 'name' and 'weight' and 'employee_id'
            if "name" in temp_indices and "weight" in temp_indices and "employee_id" in temp_indices:
                header_row_idx = r_idx
                header_indices = temp_indices
                break

        if not header_row_idx:
            errors.append(f"[{sheet_label}] Could not find required table columns ('Name' and 'Weight') in sheet headers.")
            return {}, errors

        processed_ids = set()

        # Parse data rows starting right after the detected header row
        for row_idx in range(header_row_idx + 1, ws.max_row + 1):
            row_cells = [ws.cell(row=row_idx, column=col_idx + 1).value for col_idx in range(ws.max_column)]
            
            # 1. Ignore completely blank rows (all cells empty or whitespace)
            if all(val is None or str(val).strip() == "" for val in row_cells):
                continue

            raw_id = row_cells[header_indices["employee_id"]] if header_indices["employee_id"] < len(row_cells) else None
            raw_name = row_cells[header_indices["name"]] if header_indices["name"] < len(row_cells) else None
            raw_weight = row_cells[header_indices["weight"]] if header_indices["weight"] < len(row_cells) else None

            emp_id = cls.clean_employee_id(raw_id)
            name = cls.clean_name(raw_name)
            display_label = f"Participant: {name}" if name else f"ID: {emp_id}" if emp_id else f"Row {row_idx}"

            row_has_error = False

            if not emp_id:
                errors.append(f"[{sheet_label}] Row {row_idx}: Participant identifier is missing")
                row_has_error = True
            elif emp_id in processed_ids:
                errors.append(f"[{sheet_label}] Row {row_idx} ({display_label}): Duplicate Participant Identifier '{emp_id}'")
                row_has_error = True
            else:
                processed_ids.add(emp_id)

            # Validate Weight (required)
            weight = None
            if raw_weight is not None and str(raw_weight).strip() != "":
                try:
                    f_val = float(str(raw_weight).strip())
                    if f_val > 0:
                        weight = f_val
                except ValueError:
                    pass

            if weight is None:
                errors.append(f"[{sheet_label}] Row {row_idx} ({display_label}): Weight is missing or invalid")
                row_has_error = True

            # Validate Waist Circumference (required if column exists in sheet)
            waist = None
            if "waist" in header_indices:
                raw_waist = row_cells[header_indices["waist"]] if header_indices["waist"] < len(row_cells) else None
                if raw_waist is not None and str(raw_waist).strip() != "":
                    try:
                        w_val = float(str(raw_waist).strip())
                        if w_val > 0:
                            waist = w_val
                    except ValueError:
                        pass
                if waist is None:
                    errors.append(f"[{sheet_label}] Row {row_idx} ({display_label}): Waist circumference is missing or invalid")
                    row_has_error = True

            # Validate Hip Circumference (required if column exists in sheet)
            hip = None
            if "hip" in header_indices:
                raw_hip = row_cells[header_indices["hip"]] if header_indices["hip"] < len(row_cells) else None
                if raw_hip is not None and str(raw_hip).strip() != "":
                    try:
                        h_val = float(str(raw_hip).strip())
                        if h_val > 0:
                            hip = h_val
                    except ValueError:
                        pass
                if hip is None:
                    errors.append(f"[{sheet_label}] Row {row_idx} ({display_label}): Hip circumference is missing or invalid")
                    row_has_error = True

            # If required fields have errors for this row, do not include row in results data
            if row_has_error:
                continue

            whr = (waist / hip) if (waist and hip) else None

            data[emp_id] = {
                "name": name or emp_id,
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
            warnings: list of warning messages
        """
        warnings = []
        
        # Determine common participants in day 0 and day 90
        day0_ids = set(day0_data.keys())
        day90_ids = set(day90_data.keys())
        day45_ids = set(day45_data.keys())

        # Exclude list warnings
        only_in_day0 = day0_ids - day90_ids
        for eid in sorted(only_in_day0):
            warnings.append(f"Participant '{day0_data[eid]['name']}' ({eid}) is in Day 0 but missing in Day 90. Excluded from rankings.")

        only_in_day90 = day90_ids - day0_ids
        for eid in sorted(only_in_day90):
            warnings.append(f"Participant '{day90_data[eid]['name']}' ({eid}) is in Day 90 but missing in Day 0. Excluded from rankings.")

        common_ids = day0_ids & day90_ids
        if not common_ids:
            raise ValueError("No common participants found between Day 0 and Day 90 Excel sheets.")

        raw_results = []
        max_weight_loss_pct = 0.0
        max_whr_imp_pct = 0.0
        has_whr_data = False

        for eid in common_ids:
            d0 = day0_data[eid]
            d90 = day90_data[eid]

            # Weight Loss %: ((Day0Weight - Day90Weight) / Day0Weight) * 100
            weight_loss_pct = ((d0["weight"] - d90["weight"]) / d0["weight"]) * 100.0

            # WHR Improvement %: ((Day0WHR - Day90WHR) / Day0WHR) * 100 (if WHR exists for both)
            whr_imp_pct = 0.0
            if d0["whr"] is not None and d90["whr"] is not None:
                whr_imp_pct = ((d0["whr"] - d90["whr"]) / d0["whr"]) * 100.0
                has_whr_data = True

            if weight_loss_pct > max_weight_loss_pct:
                max_weight_loss_pct = weight_loss_pct
            if whr_imp_pct > max_whr_imp_pct:
                max_whr_imp_pct = whr_imp_pct

            # Warn if missing in Day 45
            if eid not in day45_ids:
                warnings.append(f"Participant '{d0['name']}' ({eid}) is missing in Day 45 (included in rankings).")

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
            r["normalized_weight"] = max(0.0, (r["weight_loss_percent"] / norm_weight_denom) * 100.0) if max_weight_loss_pct > 0 else 0.0
            r["normalized_whr"] = max(0.0, (r["whr_improvement_percent"] / norm_whr_denom) * 100.0) if max_whr_imp_pct > 0 else 0.0
            
            # If WHR exists, 50% Weight Loss + 50% WHR. Otherwise 100% Weight Loss score.
            if has_whr_data:
                r["final_score"] = (r["normalized_weight"] * 0.5) + (r["normalized_whr"] * 0.5)
            else:
                r["final_score"] = r["normalized_weight"]

        # Sort descending by Final Score, using weight loss and WHR as secondary tie-breakers
        sorted_results = sorted(
            raw_results, 
            key=lambda x: (x["final_score"], x["weight_loss_percent"], x["whr_improvement_percent"]), 
            reverse=True
        )

        # Assign ranks
        for idx, r in enumerate(sorted_results, 1):
            r["rank"] = idx

        winner = sorted_results[0] if sorted_results else None

        summary = {
            "total_participants": len(sorted_results),
            "highest_weight_loss": round(max_weight_loss_pct, 2),
            "highest_whr_improvement": round(max_whr_imp_pct, 2) if has_whr_data else 0.0,
            "winner_name": winner["name"] if winner else "N/A",
            "winner_employee_id": winner["employee_id"] if winner else "N/A",
            "winner_final_score": round(winner["final_score"], 2) if winner else 0.0
        }

        # Format numeric floats for display
        for r in sorted_results:
            r["day0_weight"] = round(r["day0_weight"], 2)
            r["day90_weight"] = round(r["day90_weight"], 2)
            r["weight_loss_percent"] = round(r["weight_loss_percent"], 2)
            r["day0_whr"] = round(r["day0_whr"], 4) if r["day0_whr"] is not None else "-"
            r["day90_whr"] = round(r["day90_whr"], 4) if r["day90_whr"] is not None else "-"
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
            "Rank", "Identifier", "Name", 
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

            for col_idx in range(1, 11):
                ws.cell(row=row_idx, column=col_idx).border = thin_border

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
