"""Column contract for the FTIR ``records`` table."""

from __future__ import annotations

# Uploadable source columns, in schema order. Computed fields are derived on insert.
SOURCE_COLUMNS: list[str] = [
    "sbpr_no",
    "ftir_no",
    "ftir_report_date",
    "reply_date",
    "status",
    "fc_ok",
    "product_model_code",
    "sales_model_code",
    "segmentation",
    "vin",
    "engine_no",
    "transmission_no",
    "date_registered",
    "date_of_incident",
    "using_time_km",
    "reported_company",
    "issued_company",
    "outbreak_country",
    "manufacturer_factory",
    "subject",
    "c_measure",
    "customer_complaint",
    "trouble_code_complaint",
    "trouble_code_defect",
    "checked_contents",
    "checked_results",
    "repair_status",
    "repair_contents",
    "problem_solved",
    "action_judgement",
    "causal_parts_no",
    "causal_parts_name",
    "supplier_of_causal_parts",
    "production_base",
    "parts_availability",
    "file_name",
    "quality",
    "rank",
    "reported_country",
    "days_used",
    "fpcr_no",
    "sales_dealer",
    "service_dealer",
    "spec_on_destination",
    "collection_request_date",
    "parts_retrieved_date",
    "person_of_action_judgement",
    "dept_of_action_judgement",
    "judgement_date",
    "reason_not_sbpr",
    "approval_judgement_date",
]

# Present in the table, but filled by the loader (accepted if a file already has them).
DERIVED_COLUMNS: list[str] = [
    "using_km_int",
    "report_year",
    "report_month",
    "is_resolved",
    "has_sbpr",
    "summary",
    "root_cause",
]

# Metadata the loader owns. If a file includes them, they are dropped quietly.
DROPPED_COLUMNS = {"id", "created_at", "row_hash"}

REQUIRED_COLUMNS: list[str] = [
    "ftir_no",
    "ftir_report_date",
    "status",
    "product_model_code",
    "outbreak_country",
    "customer_complaint",
]

DATE_COLUMNS = {
    "ftir_report_date",
    "reply_date",
    "date_registered",
    "date_of_incident",
    "collection_request_date",
    "parts_retrieved_date",
    "judgement_date",
    "approval_judgement_date",
}

CATEGORY_COLUMNS: list[str] = [
    "status",
    "fc_ok",
    "product_model_code",
    "sales_model_code",
    "segmentation",
    "reported_company",
    "issued_company",
    "outbreak_country",
    "manufacturer_factory",
    "trouble_code_complaint",
    "trouble_code_defect",
    "repair_status",
    "problem_solved",
    "action_judgement",
    "causal_parts_name",
    "supplier_of_causal_parts",
    "production_base",
    "parts_availability",
    "quality",
    "rank",
    "reported_country",
    "sales_dealer",
    "service_dealer",
    "spec_on_destination",
    "dept_of_action_judgement",
]

NUMERIC_COLUMNS: list[str] = [
    "days_used",
    "using_km_int",
    "report_year",
    "report_month",
    "is_resolved",
    "has_sbpr",
]

INSERT_COLUMNS: list[str] = SOURCE_COLUMNS + [
    "row_hash",
    "using_km_int",
    "report_year",
    "report_month",
    "is_resolved",
    "has_sbpr",
    "summary",
    "root_cause",
]

HASH_FIELDS: list[str] = [c for c in SOURCE_COLUMNS if c != "file_name"]

ALIASES = {
    "ftir_number": "ftir_no",
    "ftirno": "ftir_no",
    "ftir": "ftir_no",
    "report_date": "ftir_report_date",
    "ftir_date": "ftir_report_date",
    "model_code": "product_model_code",
    "product_model": "product_model_code",
    "country": "outbreak_country",
    "complaint": "customer_complaint",
    "km": "using_time_km",
    "mileage": "using_time_km",
    "using_km": "using_time_km",
    "odometer": "using_time_km",
}

LABELS = {
    "sbpr_no": "SBPR number",
    "ftir_no": "FTIR number",
    "ftir_report_date": "FTIR report date",
    "reply_date": "Reply date",
    "status": "Status",
    "fc_ok": "FC OK",
    "product_model_code": "Product model",
    "sales_model_code": "Sales model",
    "segmentation": "Segmentation",
    "vin": "VIN",
    "engine_no": "Engine number",
    "transmission_no": "Transmission number",
    "date_registered": "Date registered",
    "date_of_incident": "Date of incident",
    "using_time_km": "Usage (km, text)",
    "reported_company": "Reported company",
    "issued_company": "Issued company",
    "outbreak_country": "Outbreak country",
    "manufacturer_factory": "Factory",
    "subject": "Subject",
    "c_measure": "Countermeasure",
    "customer_complaint": "Customer complaint",
    "trouble_code_complaint": "Trouble code (complaint)",
    "trouble_code_defect": "Trouble code (defect)",
    "checked_contents": "Checked contents",
    "checked_results": "Checked results",
    "repair_status": "Repair status",
    "repair_contents": "Repair contents",
    "problem_solved": "Problem solved",
    "action_judgement": "Action judgement",
    "causal_parts_no": "Causal part number",
    "causal_parts_name": "Causal part",
    "supplier_of_causal_parts": "Causal part supplier",
    "production_base": "Production base",
    "parts_availability": "Parts availability",
    "file_name": "File name",
    "quality": "Quality",
    "rank": "Severity rank",
    "reported_country": "Reported country",
    "days_used": "Days used",
    "fpcr_no": "FPCR number",
    "sales_dealer": "Sales dealer",
    "service_dealer": "Service dealer",
    "spec_on_destination": "Destination spec",
    "collection_request_date": "Collection request date",
    "parts_retrieved_date": "Parts retrieved date",
    "person_of_action_judgement": "Person of action judgement",
    "dept_of_action_judgement": "Department of action judgement",
    "judgement_date": "Judgement date",
    "reason_not_sbpr": "Reason not SBPR",
    "approval_judgement_date": "Approval date",
    "using_km_int": "Usage (km)",
    "report_year": "Report year",
    "report_month": "Report month",
    "is_resolved": "Resolved flag",
    "has_sbpr": "Has SBPR",
    "summary": "Summary",
    "root_cause": "Root cause",
}

ALLOWED_CHART_COLUMNS = set(CATEGORY_COLUMNS) | set(NUMERIC_COLUMNS) | DATE_COLUMNS

SOURCE_SET = set(SOURCE_COLUMNS)
DERIVED_SET = set(DERIVED_COLUMNS)
KNOWN_UPLOAD_COLUMNS = SOURCE_SET | DERIVED_SET | DROPPED_COLUMNS


def label_for(name: str) -> str:
    return LABELS.get(name, name.replace("_", " ").title())


def column_meta(names: list[str]) -> list[dict[str, str]]:
    return [{"name": name, "label": label_for(name)} for name in names]
