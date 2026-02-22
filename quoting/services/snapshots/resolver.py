from quoting.models import QuoteRevision
from quoting.serializers import QuoteLiveSerializer
from rest_framework.exceptions import NotFound

def resolve_quote_view(quote, revision_no=None):
    """
    Returns serialized quote data based on quote state.
    Ensures frontend (Alpine.js) receives a consistent schema.
    """
    # 1. Explicit Revision Requested
    if revision_no:
        rev = quote.revisions.filter(revision_no=revision_no).first()
        if not rev:
            raise NotFound(f"Revision {revision_no} not found.")
        return {
            "mode": "REVISION",
            "revision_no": rev.revision_no,
            "data": rev.snapshot  # Immutable JSON
        }

    # 2. Locked Quote: Force the latest Snapshot
    if quote.status == "locked":
        rev = quote.revisions.order_by("-revision_no").first()
        if rev:
            return {
                "mode": "LOCKED",
                "revision_no": rev.revision_no,
                "data": rev.snapshot
            }

    # 3. Live Mode (Draft/Edit): Dynamic Calculation
    return {
        "mode": "LIVE",
        "revision_no": None,
        "data": QuoteLiveSerializer(quote).data
    }