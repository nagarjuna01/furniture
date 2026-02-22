import ast

ALLOWED_OPS = {
    "Gt", "GtE", "Lt", "LtE", "Eq"
}

def parse_constraints(expr: str) -> list[dict]:
    """
    Convert boolean expression into structured constraints.
    Supports:
      - AND / OR
      - chained comparisons
    """

    tree = ast.parse(expr, mode="eval")
    constraints = []

    def walk(node, logical_op="AND"):
        # -----------------------------
        # Boolean blocks (AND / OR)
        # -----------------------------
        if isinstance(node, ast.BoolOp):
            op_type = "AND" if isinstance(node.op, ast.And) else "OR"
            for value in node.values:
                walk(value, op_type)

        # -----------------------------
        # Comparisons
        # -----------------------------
        elif isinstance(node, ast.Compare):
            left = node.left
            ops = node.ops
            comparators = node.comparators

            # Handle chained comparisons
            for i, op in enumerate(ops):
                lhs = ast.unparse(left)
                rhs = ast.unparse(comparators[i])
                op_name = op.__class__.__name__

                if op_name not in ALLOWED_OPS:
                    raise ValueError(f"Unsupported operator: {op_name}")

                constraints.append({
                    "lhs": lhs,
                    "op": op_name,
                    "rhs": rhs,
                    "logical": logical_op
                })

                left = comparators[i]

    walk(tree.body)
    return constraints
