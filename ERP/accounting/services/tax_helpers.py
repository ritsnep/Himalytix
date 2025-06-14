"""
Tax calculation helper functions.
"""
def calculate_tax(amount, tax_code):
    """
    Calculate tax for a given amount and tax code.
    """
    rate = getattr(tax_code, 'rate', 0)
    return amount * rate / 100
