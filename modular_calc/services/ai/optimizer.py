import ast
import re

COMPARISON_FLIP = {
    ast.Lt: ast.Gt,
    ast.Gt: ast.Lt,
    ast.LtE: ast.GtE,
    ast.GtE: ast.LtE,
}


def optimize_candidates(candidates: list[dict], context: dict) -> list[dict]:
    optimized_list = []

    for c in candidates:
        original = c["expression"].strip()
        expr = re.sub(r"\s+", " ", original)

        optimized = False

        try:
            tree = ast.parse(expr, mode="eval")

            # Only handle simple comparisons: <number> <op> <variable>
            if (
                isinstance(tree.body, ast.Compare)
                and len(tree.body.ops) == 1
                and len(tree.body.comparators) == 1
            ):
                left = tree.body.left
                right = tree.body.comparators[0]
                op = tree.body.ops[0]

                if (
                    isinstance(left, ast.Constant)
                    and isinstance(right, ast.Name)
                    and type(op) in COMPARISON_FLIP
                ):
                    flipped_op = COMPARISON_FLIP[type(op)]()
                    expr = f"{right.id} {ast.dump(flipped_op).replace('()', '')} {left.value}"
                    optimized = True

        except Exception:
            # Never crash optimizer
            pass

        optimized_list.append({
            **c,
            "expression": expr,
            "optimized": optimized
        })

    return optimized_list
