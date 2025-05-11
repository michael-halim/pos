import re

def remove_non_digit(number: str) -> str:
    """Remove all non-digit characters from number"""
    return re.sub(r'\D', '', str(number))

def format_number(number: str) -> str:
    """Convert number to string with thousand separator"""
    try:
        num = remove_non_digit(number)
        
        # Add thousand separator (equivalent to replace(/(\d)(?=(\d{3})+$)/g, '$1.'))
        num = re.sub(r'(\d)(?=(\d{3})+(?!\d))', r'\1.', num)
        
        return num if num else "0"
        
    except (ValueError, TypeError):
        return "0"

def add_prefix(number: str, prefix: str = 'Rp. ') -> str:
    """Add prefix to number"""
    return f'{prefix}{number}'
