import os
from pathlib import Path

# Search for hardcoded 0.5 or 0.50
print("Looking for hardcoded 0.5 or 0.50 values...")
found = []
for py_file in Path('backend').rglob('*.py'):
    try:
        content = py_file.read_text(encoding='utf-8', errors='ignore')
        if '0.50' in content or '0.5' in content:
            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                if ('0.50' in line or '0.5' in line) and not line.strip().startswith('#'):
                    rel_path = str(py_file.relative_to("."))
                    found.append(f'{rel_path}: line {i}: {line.strip()[:100]}')
    except Exception as e:
        pass

if found:
    for item in found:
        print(item)
else:
    print("No hardcoded 0.5 or 0.50 values found")
