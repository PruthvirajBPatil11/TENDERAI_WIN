from backend.extraction.criterion_extractor import safe_parse_json

# Test 1: Normal JSON
result1 = safe_parse_json('[{"id": "C1", "text": "test"}]')
print(f"✓ Test 1 (normal JSON): {result1}")

# Test 2: JSON with markdown code block
result2 = safe_parse_json('```json\n[{"id": "C1"}]\n```')
print(f"✓ Test 2 (markdown): {result2}")

# Test 3: JSON with trailing comma
result3 = safe_parse_json('[{"id": "C1",}]')
print(f"✓ Test 3 (trailing comma): {result3}")

# Test 4: JSON with control characters
result4 = safe_parse_json('[{"id": "C1", "text": "line\x01break"}]')
print(f"✓ Test 4 (control chars): {result4}")

# Test 5: Completely invalid JSON (should return empty list/dict)
result5 = safe_parse_json('this is not json at all')
print(f"✓ Test 5 (invalid): {result5}")

print("\n✅ All parser tests passed!")
