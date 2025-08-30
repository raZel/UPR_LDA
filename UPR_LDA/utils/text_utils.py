import re
from unidecode import unidecode

_PROBLEMATIC_CHARACTERS_PATTERN = r'[\[\]{}()"\'\\/?,.]'

def clean_country_name(text: str) -> str:
    """
    Cleans a string by:
    1. Transliterating it to ASCII using unidecode.
    2. Removing a set of problematic characters.
    """
    # First, transliterate to the closest ASCII representation
    cleaned_text = unidecode(text)
    # Then, remove any remaining problematic characters
    return re.sub(_PROBLEMATIC_CHARACTERS_PATTERN, '', cleaned_text)