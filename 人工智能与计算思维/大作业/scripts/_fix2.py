import pathlib

p = pathlib.Path(r"D:\虚拟C盘\study\人工智能与计算思维大作业\scripts\f8_influence_index.py")
text = p.read_text(encoding="utf-8")

# The issue: textwrap.dedent(f"""\  needs closing """")
# Current: | `README.md` | 本说明文档 |\n    """
# Should be: | `README.md` | 本说明文档 |\n    """)

old = '    """\n\n    with open(OUT_DIR'
new = '    """)\n\n    with open(OUT_DIR'
text = text.replace(old, new)

p.write_text(text, encoding="utf-8")
print("Fixed!")
