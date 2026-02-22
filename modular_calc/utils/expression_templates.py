# utils/expression_templates.py

EXPRESSION_TEMPLATES = {
    "between": {
        "label": "Between",
        "description": "Ensure a value lies between two limits",
        "template": "{var} >= {min} and {var} <= {max}",
        "fields": ["var", "min", "max"],
    },
    "clearance": {
        "label": "Clearance",
        "description": "Ensure outer >= inner + clearance",
        "template": "{outer} >= {inner} + {gap}",
        "fields": ["outer", "inner", "gap"],
    },
    "max": {
        "label": "Maximum",
        "description": "Ensure value does not exceed a limit",
        "template": "{var} <= {max}",
        "fields": ["var", "max"],
    },
    "min": {
        "label": "Minimum",
        "description": "Ensure value meets a minimum",
        "template": "{var} >= {min}",
        "fields": ["var", "min"],
    },
}
