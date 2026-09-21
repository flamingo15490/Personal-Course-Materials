import pathlib

p = pathlib.Path(r"D:\虚拟C盘\study\人工智能与计算思维大作业\scripts\f8_influence_index.py")
text = p.read_text(encoding="utf-8")

# Fix 1: {D:.0%} -> {W_D:.0%}
text = text.replace('{D:.0%} | \u8eab\u4efd\u6807\u7b7e\u79cd\u7c7b\u6570 |',
                    '{W_D:.0%} | \u8eab\u4efd\u6807\u7b7e\u79cd\u7c7b\u6570 |')

# Fix 2: {E:.0%} -> {W_E:.0%}  
text = text.replace('{E:.0%} | \u793e\u4f1a\u5173\u7cfb + \u4eb2\u5c5e\u5173\u7cfb',
                    '{W_E:.0%} | \u793e\u4f1a\u5173\u7cfb + \u4eb2\u5c5e\u5173\u7cfb')

# Fix 3: Remove the .replace() chain
# Find the line and replace it
lines = text.split('\n')
new_lines = []
skip = False
for i, line in enumerate(lines):
    stripped = line.strip()
    if stripped.startswith('""").replace(') and 'W_A:.0%' in stripped:
        # This is the chain we want to replace
        # Find previous line that ends the dedent string
        # Replace previous line's ending
        if new_lines and new_lines[-1].strip() == '| `README.md` | 本说明文档 |':
            pass
        # Just change this line to close the triple-quote
        indent = len(line) - len(line.lstrip())
        new_lines.append(' ' * indent + '"""')
        skip = True
        continue
    if skip and ('.replace(' in stripped or "f'" in stripped):
        continue
    if skip and stripped == ')':
        skip = False
        continue
    new_lines.append(line)

text = '\n'.join(new_lines)
p.write_text(text, encoding="utf-8")
print("Fixed successfully")
