import datetime

def coerce_float(val):
    try:
        return float(val)
    except (ValueError, TypeError):
        return None

def coerce_date(val):
    try:
        return datetime.datetime.fromisoformat(val)
    except (ValueError, TypeError):
        return None

def load_filtered_data(filters):
    data = load_json_data()
    if not filters:
        return data

    filtered_data = data.copy()
    for field, condition in filters.items():
        normalized_field = normalize_field_name(field)
        value = condition.get("value")
        condition_type = condition.get("type")
        value2 = condition.get("value2")  # for ranges

        print(f"🔍 Filtering field: {normalized_field} with condition: {condition_type} {value} {value2 or ''}")

        if value is None or condition_type is None:
            continue

        if condition_type in ["greater_than", "less_than", "equal_to", "not_equal", "range"]:
            value = coerce_float(value)
            if value2:
                value2 = coerce_float(value2)
            for row in filtered_data:
                row_val = coerce_float(row.get(normalized_field))
                row[normalized_field] = row_val

            if condition_type == "greater_than":
                filtered_data = [r for r in filtered_data if r[normalized_field] is not None and r[normalized_field] > value]
            elif condition_type == "less_than":
                filtered_data = [r for r in filtered_data if r[normalized_field] is not None and r[normalized_field] < value]
            elif condition_type == "equal_to":
                filtered_data = [r for r in filtered_data if r[normalized_field] == value]
            elif condition_type == "not_equal":
                filtered_data = [r for r in filtered_data if r[normalized_field] != value]
            elif condition_type == "range" and value is not None and value2 is not None:
                filtered_data = [r for r in filtered_data if r[normalized_field] is not None and value <= r[normalized_field] <= value2]

        elif condition_type == "contains":
            filtered_data = [r for r in filtered_data if value.lower() in str(r.get(normalized_field, "")).lower()]

        elif condition_type == "date_after":
            date_val = coerce_date(value)
            for row in filtered_data:
                row_date = coerce_date(row.get(normalized_field))
                row[normalized_field] = row_date
            filtered_data = [r for r in filtered_data if r[normalized_field] is not None and r[normalized_field] > date_val]

        elif condition_type == "date_before":
            date_val = coerce_date(value)
            for row in filtered_data:
                row_date = coerce_date(row.get(normalized_field))
                row[normalized_field] = row_date
            filtered_data = [r for r in filtered_data if r[normalized_field] is not None and r[normalized_field] < date_val]

    print(f"✅ Matched {len(filtered_data)} results after filtering.")
    return filtered_data