#!/usr/bin/env python3
"""Parse openapi-spec.json into a structured endpoint-inventory.json.

Groups endpoints by category (tag), identifies singular/plural pairs,
classifies CRUD types, and extracts schema references.
"""

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SPEC_PATH = REPO_ROOT / "openapi-spec.json"
OUTPUT_PATH = REPO_ROOT / "endpoint-inventory.json"

# Map HTTP methods to CRUD operation types
METHOD_TO_CRUD = {
    "get": "read",
    "post": "create",
    "patch": "update",
    "put": "replace",
    "delete": "delete",
}


def extract_schema_ref(content: dict) -> str | None:
    """Extract the schema $ref from a request/response content block."""
    if not content:
        return None
    for media_type in ("application/json", "*/*"):
        if media_type in content:
            schema = content[media_type].get("schema", {})
            if "$ref" in schema:
                return schema["$ref"].split("/")[-1]
            # Check for allOf/oneOf/anyOf
            for combiner in ("allOf", "oneOf", "anyOf"):
                if combiner in schema:
                    for item in schema[combiner]:
                        if "$ref" in item:
                            return item["$ref"].split("/")[-1]
    return None


def classify_endpoint(path: str, method: str, operation: dict) -> dict:
    """Classify a single endpoint."""
    operation_id = operation.get("operationId", "")
    tags = operation.get("tags", [])
    summary = operation.get("summary", "")
    description = operation.get("description", "")

    # Extract path segments after /api/v2/
    path_suffix = re.sub(r"^/api/v2/", "", path)
    segments = path_suffix.split("/")

    # Determine category from tag or first path segment
    category = tags[0].lower() if tags else segments[0]

    # Determine resource name (last meaningful segment)
    resource = segments[-1] if segments else "unknown"

    # Detect special endpoint types
    is_apply = resource == "apply"
    is_settings = "settings" in resource or "settings" in path
    is_plural = resource.endswith("s") and not is_settings and not is_apply
    is_singular = not is_plural and not is_apply and not is_settings

    # Detect if this is a bulk operation (plural DELETE/PUT)
    crud_type = METHOD_TO_CRUD.get(method, "unknown")
    is_bulk = is_plural and method in ("delete", "put")

    # Extract schemas
    request_schema = None
    response_schema = None

    if "requestBody" in operation:
        request_schema = extract_schema_ref(
            operation["requestBody"].get("content", {})
        )

    # Check 200 response for schema
    responses = operation.get("responses", {})
    for code in ("200", "201"):
        if code in responses:
            response_schema = extract_schema_ref(
                responses[code].get("content", {})
            )
            if response_schema:
                break

    # Extract query/path parameters
    params = []
    for param in operation.get("parameters", []):
        params.append({
            "name": param.get("name"),
            "in": param.get("in"),
            "required": param.get("required", False),
            "type": param.get("schema", {}).get("type", "string"),
        })

    return {
        "path": path,
        "method": method.upper(),
        "operationId": operation_id,
        "summary": summary,
        "description": description[:200] if description else "",
        "category": category,
        "resource": resource,
        "crud_type": crud_type,
        "is_apply": is_apply,
        "is_settings": is_settings,
        "is_plural": is_plural,
        "is_singular": is_singular,
        "is_bulk": is_bulk,
        "request_schema": request_schema,
        "response_schema": response_schema,
        "parameters": params,
        "tags": tags,
    }


def find_pairs(endpoints: list[dict]) -> list[dict]:
    """Identify singular/plural endpoint pairs within a category."""
    pairs = []
    # Group by path prefix (everything before last segment)
    by_prefix = defaultdict(list)
    for ep in endpoints:
        segments = ep["path"].rsplit("/", 1)
        prefix = segments[0] if len(segments) > 1 else ""
        by_prefix[prefix].append(ep)

    # Check for singular/plural pairs at same prefix
    seen_paths = set()
    for prefix, eps in by_prefix.items():
        resources = {ep["resource"]: ep for ep in eps}
        for resource, ep in resources.items():
            # Look for plural form
            plural = resource + "s"
            if plural in resources and resource not in seen_paths:
                pairs.append({
                    "singular": resource,
                    "plural": plural,
                    "singular_path": ep["path"],
                    "plural_path": resources[plural]["path"],
                })
                seen_paths.add(resource)
    return pairs


def main():
    if not SPEC_PATH.exists():
        print(f"Error: {SPEC_PATH} not found. Run the fetch script first.", file=sys.stderr)
        sys.exit(1)

    with open(SPEC_PATH) as f:
        spec = json.load(f)

    paths = spec.get("paths", {})
    schemas = spec.get("components", {}).get("schemas", {})

    # Process all endpoints
    all_endpoints = []
    for path, methods in sorted(paths.items()):
        for method, operation in methods.items():
            if method not in ("get", "post", "put", "patch", "delete"):
                continue
            endpoint = classify_endpoint(path, method, operation)
            all_endpoints.append(endpoint)

    # Group by category
    by_category = defaultdict(list)
    for ep in all_endpoints:
        by_category[ep["category"]].append(ep)

    # Build category summaries
    categories = {}
    for cat, eps in sorted(by_category.items()):
        pairs = find_pairs(eps)
        categories[cat] = {
            "endpoint_count": len(eps),
            "methods": sorted(set(ep["method"] for ep in eps)),
            "resources": sorted(set(ep["resource"] for ep in eps)),
            "pairs": pairs,
            "has_apply": any(ep["is_apply"] for ep in eps),
            "has_settings": any(ep["is_settings"] for ep in eps),
            "endpoints": eps,
        }

    # Build inventory
    inventory = {
        "openapi_version": spec.get("openapi"),
        "api_version": spec.get("info", {}).get("version"),
        "total_paths": len(paths),
        "total_operations": len(all_endpoints),
        "total_schemas": len(schemas),
        "categories": categories,
        "schema_names": sorted(schemas.keys()),
    }

    with open(OUTPUT_PATH, "w") as f:
        json.dump(inventory, f, indent=2)

    # Print summary
    print(f"Inventory written to {OUTPUT_PATH}")
    print(f"  OpenAPI: {inventory['openapi_version']}")
    print(f"  API version: {inventory['api_version']}")
    print(f"  Paths: {inventory['total_paths']}")
    print(f"  Operations: {inventory['total_operations']}")
    print(f"  Schemas: {inventory['total_schemas']}")
    print(f"  Categories: {', '.join(sorted(categories.keys()))}")
    for cat, info in sorted(categories.items()):
        print(f"    {cat}: {info['endpoint_count']} endpoints, {len(info['pairs'])} pairs, apply={info['has_apply']}")


if __name__ == "__main__":
    main()
