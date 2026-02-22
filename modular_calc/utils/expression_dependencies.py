# utils/expression_dependencies.py
import ast

def extract_identifiers(expression: str) -> set[str]:
    """
    Extract variable names used in an expression.
    """
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError:
        return set()

    return {
        node.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Name)
    }

def extract_part_dependencies(
    identifiers: set[str],
    part_name_map: dict[str, int],
    part_id_map: dict[str, int],
) -> set[int]:
    """
    Resolve identifiers into part IDs they depend on.
    """
    dependencies = set()

    for name in identifiers:
        key = name.lower()

        if key in part_name_map:
            dependencies.add(part_name_map[key])

        elif key.startswith("part_") and key in part_id_map:
            dependencies.add(part_id_map[key])

    return dependencies

def build_dependency_graph(parts):
    """
    parts = iterable of Part objects
    """
    graph = {}

    # Pre-build lookup maps
    part_name_map = {
        part.normalized_name: part.id
        for part in parts
    }

    part_id_map = {
        f"part_{part.id}_length": part.id
        for part in parts
    }
    part_id_map |= {
        f"part_{part.id}_width": part.id
        for part in parts
    }
    part_id_map |= {
        f"part_{part.id}_thickness": part.id
        for part in parts
    }
    for part in parts:
        identifiers = set()

        for field in ("length_expr", "width_expr", "quantity_expr"):
            expr = getattr(part, field, None)
            if expr:
                identifiers |= extract_identifiers(expr)

        deps = extract_part_dependencies(
            identifiers,
            part_name_map,
            part_id_map,
        )

        # Remove self-dependency
        deps.discard(part.id)

        graph[part.id] = deps

    return graph
def has_circular_dependency(graph: dict[int, set[int]]) -> bool:
    visited = set()
    stack = set()

    def visit(node):
        if node in stack:
            return True
        if node in visited:
            return False

        visited.add(node)
        stack.add(node)

        for neighbor in graph.get(node, []):
            if visit(neighbor):
                return True

        stack.remove(node)
        return False

    return any(visit(node) for node in graph)
