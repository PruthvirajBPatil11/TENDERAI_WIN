#!/usr/bin/env python3
import re

text = "ISO 9001:2015, valid till 15/06/2027"
text_upper = text.upper()

print(f"Original: {text}")
print(f"Upper:    {text_upper}")
print(f"Search 'ISO\\s*9001': {re.search(r'ISO\s*9001', text_upper, re.IGNORECASE)}")
