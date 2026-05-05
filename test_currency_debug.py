from backend.extraction.value_normaliser import normalise_currency
import re

# Test step by step
text = "8.2 crore"
print(f"Input: '{text}'")

# Step 1: Remove symbols
text_clean = re.sub(r'Rs\.?\s*', '', text, flags=re.IGNORECASE)
print(f"After Rs removal: '{text_clean}'")
text_clean = re.sub(r'INR\s*', '', text_clean, flags=re.IGNORECASE)
print(f"After INR removal: '{text_clean}'")
text_clean = text_clean.replace('₹', '')
print(f"After ₹ removal: '{text_clean}'")
text_clean = text_clean.strip()
print(f"After strip: '{text_clean}'")

# Step 2: Regex match
pattern = r'([\d,]+(?:\.\d+)?)\s*(?:(crore|cr|Cr\.|Cr|CRORE|Crs|lakh|lac|L|Lakh|LAKH))?'
print(f"\nUsing pattern: {pattern}")
match = re.search(pattern, text_clean, re.IGNORECASE)
if match:
    print(f"Match found!")
    print(f"Match group 1: '{match.group(1)}'")
    print(f"Match group 2: '{match.group(2)}'")
    number_str = match.group(1).replace(',', '')
    print(f"After comma removal: '{number_str}'")
    number = float(number_str)
    print(f"Parsed as float: {number}")
    
    unit = (match.group(2) or "").lower()
    print(f"Unit: '{unit}'")
    
    if unit and any(u in unit for u in ['crore', 'cr', 'crs']):
        number = number * 10_000_000
        print(f"After crore multiplication: {number}")
else:
    print("No match found!")

# Now test the actual function
print(f"\nActual function result: {normalise_currency('8.2 crore')}")
print("\n=== Full test suite ===")
tests = [
    ('Rs. 8,20,00,000', 82000000.0),
    ('8.2 crore', 82000000.0),
    ('820 lakh', 82000000.0),
    ('2.1 crore', 21000000.0),
    ('5 Crore', 50000000.0),
]
for inp, expected in tests:
    result = normalise_currency(inp)
    status = "✓" if result == expected else "✗"
    print(f"{status} {inp} -> {result} (expected {expected})")
