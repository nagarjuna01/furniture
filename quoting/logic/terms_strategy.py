# quoting/logic/terms_strategy.py

def get_terms_for_lead(lead_source):
    """
    Returns a dictionary of terms based on the business strategy.
    """
    STRATEGIES = {
        'direct': {
            'payment': "50% Advance, 50% Before Dispatch",
            'warranty': "1 Year Standard Warranty",
            'validity': "7 Days"
        },
        'referral': {
            'payment': "40% Advance, 60% Before Dispatch",
            'warranty': "2 Year Extended Warranty",
            'validity': "15 Days"
        },
        'website': {
            'payment': "100% Advance (Online Booking)",
            'warranty': "1 Year Standard Warranty",
            'validity': "3 Days"
        }
    }
    return STRATEGIES.get(lead_source, STRATEGIES['direct'])
