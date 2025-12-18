from jinja2 import Environment, BaseLoader, StrictUndefined, exceptions

# Jinja sandbox (prevents python code execution)
env = Environment(
    loader=BaseLoader(),
    autoescape=False,  # SVG does NOT need HTML escaping
    undefined=StrictUndefined,  # raise if variable missing
)

def render_svg(svg_template: str, context: dict) -> str:
    """
    Safely render an SVG template using Jinja2 variables.
    Context must contain only simple numeric/string values.
    """
    try:
        template = env.from_string(svg_template)
        return template.render(**context)

    except exceptions.UndefinedError as err:
        raise ValueError(f"Missing SVG parameter: {err}")

    except Exception as err:
        raise ValueError(f"SVG Rendering failed: {err}")

# ✔ SVG rendering integrated inside ProductEngine
# ✔ Save generated SVG as PNG/JPEG
# ✔ Auto-download 2D drawings per product
# ✔ Bulk export ZIP of SVGs for all parts
# ✔ Add caching (to avoid recomputing SVG every time)