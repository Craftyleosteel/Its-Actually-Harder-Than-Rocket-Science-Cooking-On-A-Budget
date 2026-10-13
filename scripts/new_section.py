"""Create a new section of the cookbook (a new tab on the website).

Usage:
    python scripts/new_section.py "Section Name" [emoji]

Example:
    python scripts/new_section.py "Drinks" 🍹
    -> creates _sections/drinks.md and the folder _recipes/drinks/
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from new_recipe import slugify, yaml_value  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def main():
    if len(sys.argv) not in (2, 3):
        print(__doc__)
        sys.exit(1)
    title = sys.argv[1].strip()
    emoji = sys.argv[2].strip() if len(sys.argv) == 3 else "🍽️"
    slug = slugify(title)

    target = ROOT / "_sections" / f"{slug}.md"
    if target.exists():
        print(f"That section already exists: {target.relative_to(ROOT).as_posix()}")
        sys.exit(1)

    orders = []
    for p in (ROOT / "_sections").glob("*.md"):
        m = re.search(r"^order:\s*(\d+)", p.read_text(encoding="utf-8"), re.M)
        if m:
            orders.append(int(m.group(1)))
    order = max(orders, default=0) + 1

    target.write_text(
        "---\n"
        f"title: {yaml_value(title)}\n"
        f"emoji: {emoji}\n"
        f"order: {order}\n"
        "description: A short line about what's in this section.\n"
        "---\n",
        encoding="utf-8",
        newline="\n",
    )
    folder = ROOT / "_recipes" / slug
    folder.mkdir(parents=True, exist_ok=True)

    # Add the new section to the VS Code "New recipe" picker.
    tasks = ROOT / ".vscode" / "tasks.json"
    if tasks.exists():
        text = tasks.read_text(encoding="utf-8")
        text = re.sub(r'("options": \[[^\]]*?)\]', rf'\1, "{slug}"]', text, count=1)
        tasks.write_text(text, encoding="utf-8", newline="\n")

    print(f"Created {target.relative_to(ROOT).as_posix()} and the folder _recipes/{slug}/")
    print(f"Add recipes with: python scripts/new_recipe.py {slug} \"Recipe Title\"")


if __name__ == "__main__":
    main()
