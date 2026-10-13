"""Create a new recipe file from the template.

Usage:
    python scripts/new_recipe.py <section-folder> "Recipe Title"

Example:
    python scripts/new_recipe.py breakfast "Breakfast Burritos"
    -> creates _recipes/breakfast/breakfast-burritos.md
"""
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "templates" / "recipe-template.md"


def slugify(text):
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text


def yaml_value(text):
    """Quote a value if YAML would otherwise trip over it."""
    if re.search(r":\s|\s#", text) or text[:1] in "[]{}&*!|>'\"%@`#,?:-":
        return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return text


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    section, title = sys.argv[1].strip().lower(), sys.argv[2].strip()

    if not (ROOT / "_sections" / f"{section}.md").exists():
        known = sorted(p.stem for p in (ROOT / "_sections").glob("*.md"))
        print(f"There is no section called '{section}'.")
        print("Pick one of: " + ", ".join(known))
        print("(or make a new one: python scripts/new_section.py \"Section Name\")")
        sys.exit(1)

    target = ROOT / "_recipes" / section / f"{slugify(title)}.md"
    if target.exists():
        print(f"That recipe already exists: {target.relative_to(ROOT).as_posix()}")
        sys.exit(1)

    text = TEMPLATE.read_text(encoding="utf-8")
    text = text.replace("title: Recipe Name Here", f"title: {yaml_value(title)}", 1)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8", newline="\n")
    print(f"Created {target.relative_to(ROOT).as_posix()}")
    print("Open it, fill it in, then delete the 'coming_soon: true' line.")


if __name__ == "__main__":
    main()
