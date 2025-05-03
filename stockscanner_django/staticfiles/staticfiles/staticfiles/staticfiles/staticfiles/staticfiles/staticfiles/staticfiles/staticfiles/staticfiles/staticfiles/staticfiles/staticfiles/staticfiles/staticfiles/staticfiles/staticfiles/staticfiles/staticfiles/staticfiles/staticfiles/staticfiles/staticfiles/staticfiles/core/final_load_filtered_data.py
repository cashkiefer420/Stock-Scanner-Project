def coerce_float(val):
    try:
        return float(val)
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

        print(f"🔍 Filtering field: {normalized_field} with condition: {condition_type} {value}")

        if value is None or condition_type is None:
            continue

        if condition_type in ["greater_than", "less_than"]:
            value = coerce_float(value)
            for row in filtered_data:
                row_val = coerce_float(row.get(normalized_field))
                row[normalized_field] = row_val

            if condition_type == "greater_than":
                filtered_data = [r for r in filtered_data if r[normalized_field] is not None and r[normalized_field] > value]
            elif condition_type == "less_than":
                filtered_data = [r for r in filtered_data if r[normalized_field] is not None and r[normalized_field] < value]

        elif condition_type == "equal_to":
            value = coerce_float(value)
            for row in filtered_data:
                row_val = coerce_float(row.get(normalized_field))
                row[normalized_field] = row_val
            filtered_data = [r for r in filtered_data if r[normalized_field] == value]

        elif condition_type == "contains":
            filtered_data = [r for r in filtered_data if value.lower() in str(r.get(normalized_field, "")).lower()]

    print(f"✅ Matched {len(filtered_data)} results after filtering.")
    return filtered_data