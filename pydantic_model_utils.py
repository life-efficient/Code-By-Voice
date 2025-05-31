from pydantic import create_model, BaseModel
from typing import Any, Dict, List, Type, Optional

def pydantic_type_from_schema(prop: dict) -> Any:
    """
    Recursively determine the Python type for a property from its JSON schema.
    """
    typ = prop.get("type")
    if typ == "string":
        return str
    elif typ == "integer":
        return int
    elif typ == "number":
        return float
    elif typ == "boolean":
        return bool
    elif typ == "array":
        items_type = pydantic_type_from_schema(prop["items"])
        return List[items_type]
    elif typ == "object":
        # Recursively create a nested model
        return make_pydantic_model_from_schema(prop)
    else:
        return Any

def make_pydantic_model_from_schema(schema: dict, name: str = "ToolModel") -> Type[BaseModel]:
    """
    Recursively create a Pydantic model from a JSON schema dict.
    """
    properties = schema.get("properties", {})
    required = set(schema.get("required", []))
    fields = {}
    for pname, pinfo in properties.items():
        typ = pydantic_type_from_schema(pinfo)
        default = ... if pname in required else None
        fields[pname] = (typ, default)
    return create_model(name, **fields) 