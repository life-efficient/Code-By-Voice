def build_json_schema(properties, required=None, additional_properties=False):
    """
    Recursively build a JSON schema dict for OpenAI tool definitions.
    Supports nested objects, arrays, enums, and all OpenAI-compatible types.
    """
    schema = {
        "type": "object",
        "properties": {},
        "additionalProperties": additional_properties,
    }
    if required:
        schema["required"] = required

    for name, prop in properties.items():
        if name == "additionalProperties":
            continue
        prop_type = prop.get("type")
        if prop_type == "object":
            # Recursively build nested object
            nested_required = prop.get("required", [])
            nested_additional = prop.get("additionalProperties", False)
            schema["properties"][name] = build_json_schema(
                prop.get("properties", {}), nested_required, nested_additional
            )
        elif prop_type == "array":
            # Recursively build array items
            items_schema = build_json_schema(
                prop["items"].get("properties", {}),
                prop["items"].get("required", []),
                prop["items"].get("additionalProperties", False),
            ) if prop["items"].get("type") == "object" else prop["items"]
            schema["properties"][name] = {
                "type": "array",
                "items": items_schema,
            }
        else:
            # Copy all other keys (type, enum, description, etc.)
            schema["properties"][name] = {k: v for k, v in prop.items() if k != "properties"}
    return schema 