from django.db import transaction
from quoting.permissions import QuoteProductService


@transaction.atomic
def bulk_expand_products(products):
    expanded = []

    for qp in products.select_related("solution", "solution__quote"):
        if qp.status == qp.STATUS_FROZEN:
            continue

        expanded_qp = QuoteProductService.expand_to_parts(qp)
        expanded.append(expanded_qp)

    return expanded
