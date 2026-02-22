from ..models import QuoteRequest, QuoteSolution, QuoteProduct, QuotePart, QuotePartHardware

def create_quote_revision(old_quote_id):
    """
    Main entry point to create a R+1 revision of a quote.
    """
    old_quote = QuoteRequest.objects.get(id=old_quote_id)
    
    # 1. Duplicate the QuoteRequest
    new_quote = old_quote
    new_quote.pk = None  # Reset primary key to create new record
    new_quote.revision_number += 1
    new_quote.is_locked = False
    new_quote.save()

    # 2. Duplicate Solutions
    for sol in old_quote.solutions.all():
        clone_solution(sol, new_quote)

    return new_quote

def clone_solution(old_sol, new_quote):
    """
    Clones Solution and triggers Product cloning.
    """
    new_sol = old_sol
    new_sol.pk = None
    new_sol.quote = new_quote
    new_sol.save()

    for prod in old_sol.products.all():
        clone_product(prod, new_sol)

def clone_product(old_prod, new_sol):
    """
    Clones Product and triggers Part cloning.
    """
    new_prod = old_prod
    new_prod.pk = None
    new_prod.solution = new_sol
    new_prod.save()

    for part in old_prod.parts.all():
        clone_part(part, new_prod)

def clone_part(old_part, new_prod):
    """
    Clones Part and triggers Hardware cloning.
    """
    new_part = old_part
    new_part.pk = None
    new_part.quote_product = new_prod
    new_part.save()

    for hw in old_part.hardware.all():
        hw.pk = None
        hw.quote_part = new_part
        hw.save()