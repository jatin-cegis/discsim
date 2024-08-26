def get_relevant_functionality(warning):
    match warning.lower():
        case s if "duplicate" in s:
            return "Drop/Export Duplicate Rows"
        case s if "missing" in s:
            return "Missing Entries Analysis"
        case s if "zero" in s:
            return "Zero Entries Analysis"
        case _:
            return "Unique ID Verifier"