from jinja2 import Template

def render_svg(svg_template: str, context: dict) -> str:
    """
    Fill an SVG template (string) using Jinja2 {{placeholders}} from context.
    """
    return Template(svg_template).render(**context)
