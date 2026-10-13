"""Check every recipe and section for formatting problems.

Usage:
    python scripts/check_recipes.py            check everything
    python scripts/check_recipes.py <file>     check one recipe file

Errors (✖) will stop the website from updating until fixed.
Warnings (⚠) are just friendly reminders.
"""
import difflib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RECIPES = ROOT / "_recipes"
SECTIONS = ROOT / "_sections"

RECIPE_KEYS = {"title", "description", "image", "servings", "prep_time",
               "cook_time", "cost", "tags", "coming_soon"}
SECTION_KEYS = {"title", "emoji", "order", "description"}
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
BIG_IMAGE_BYTES = 2 * 1024 * 1024
GOOD_NAME = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

try:
    import yaml  # optional: used for an extra-strict check when installed
except ImportError:
    yaml = None


class Report:
    def __init__(self):
        self.errors = 0
        self.warnings = 0
        self.soon = []

    def file(self, path, problems):
        rel = path.relative_to(ROOT).as_posix()
        if not problems:
            return
        print(f"\n{rel}")
        for level, msg in problems:
            if level == "error":
                self.errors += 1
                print(f"  ✖ {msg}")
            else:
                self.warnings += 1
                print(f"  ⚠ {msg}")


def parse_front_matter(text, problems):
    """Return (fields, body). Understands the simple `name: value` format we use."""
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        problems.append(("error", "The very first line must be ---  (the start of the recipe info block)."))
        return None, text
    try:
        end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration:
        problems.append(("error", "The recipe info block is never closed. Add a line with just --- after the info."))
        return None, text

    fields = {}
    for n, raw in enumerate(lines[1:end], start=2):
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if "\t" in raw:
            problems.append(("error", f"Line {n}: contains a TAB character. Use spaces instead."))
            continue
        if raw[0] == " ":
            problems.append(("error", f"Line {n}: starts with a space. Info lines must start at the very left edge."))
            continue
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*):(?:\s+(.*))?$", raw)
        if not m:
            problems.append(("error", f"Line {n}: \"{raw.strip()}\" should look like  name: value  (with a space after the colon)."))
            continue
        key, value = m.group(1), (m.group(2) or "").strip()
        if key in fields:
            problems.append(("error", f"Line {n}: '{key}' appears twice. Keep only one."))
        fields[key] = parse_value(value, n, problems)

    if yaml is not None and not any(level == "error" for level, _ in problems):
        try:
            yaml.safe_load("\n".join(lines[1:end]))
        except yaml.YAMLError as exc:
            problems.append(("error", f"The info block isn't valid: {exc}".replace("\n", " ")))

    return fields, "\n".join(lines[end + 1:])


def parse_value(value, n, problems):
    if value == "":
        return None
    if value[0] in "\"'":
        q = value[0]
        close = value.find(q, 1)
        if close == -1:
            problems.append(("error", f"Line {n}: opening quote {q} is never closed."))
            return value
        rest = value[close + 1:].strip()
        if rest and not rest.startswith("#"):
            problems.append(("error", f"Line {n}: extra text after the closing quote."))
        return value[1:close]
    value = re.split(r"\s#", value, maxsplit=1)[0].strip()  # strip trailing comment
    if value.startswith("["):
        if not value.endswith("]"):
            problems.append(("error", f"Line {n}: a list must end with ]  e.g. [quick, budget]"))
            return []
        return [v.strip().strip("\"'") for v in value[1:-1].split(",") if v.strip()]
    if value[0] in "{]}&*!|>%@`,":
        problems.append(("error", f"Line {n}: values can't start with '{value[0]}'. Wrap the value in \"double quotes\"."))
    if ": " in value:
        problems.append(("error", f"Line {n}: the value contains ': ' which confuses the website. Wrap the value in \"double quotes\"."))
    if value in ("true", "false"):
        return value == "true"
    return value


def exact_file_exists(folder, name):
    """Like Path.exists() but also checks upper/lower case, which matters on GitHub."""
    path = folder / name
    if not path.exists():
        return False, None
    actual = {p.name for p in path.parent.iterdir()}
    if path.name not in actual:
        match = next((a for a in actual if a.lower() == path.name.lower()), None)
        return False, match
    return True, None


def check_image(folder, ref, what, problems):
    if re.match(r"^(https?:)?//", ref):
        return
    if ref.startswith("/"):
        problems.append(("error", f"{what} '{ref}' starts with /. Save the photo in this recipe's folder and use just its file name."))
        return
    if " " in ref:
        problems.append(("error", f"{what} '{ref}' has spaces in its name. Rename the photo using dashes instead, e.g. my-photo.jpg"))
        return
    ok, case_match = exact_file_exists(folder, ref)
    if not ok:
        if case_match:
            problems.append(("error", f"{what} '{ref}' — the file is actually called '{case_match}'. Upper/lower case must match exactly."))
        else:
            problems.append(("error", f"{what} '{ref}' wasn't found. Put the photo in {folder.relative_to(ROOT).as_posix()}/"))
        return
    path = folder / ref
    if path.suffix.lower() not in IMAGE_EXTS:
        problems.append(("error", f"{what} '{ref}' isn't a web photo. Use .jpg, .png, .webp or .gif (iPhone .heic photos need converting)."))
    elif path.stat().st_size > BIG_IMAGE_BYTES:
        mb = path.stat().st_size / 1024 / 1024
        problems.append(("warning", f"{what} '{ref}' is {mb:.1f} MB, which loads slowly. Try shrinking it under 1 MB."))


def section_list_items(body, heading, numbered):
    """Return the list items under a '## heading' (including ### sub-groups)."""
    m = re.search(rf"^##\s+{heading}\s*$(.*?)(?=^##\s|\Z)", body, re.M | re.S | re.I)
    if not m:
        return None
    pattern = r"^\s*\d+[.)]\s+\S" if numbered else r"^\s*[-*+]\s+\S"
    return re.findall(pattern, m.group(1), re.M)


def check_recipe(path, report):
    problems = []
    folder = path.parent
    section = folder.name

    if folder.parent != RECIPES:
        problems.append(("error", "Recipes must sit directly inside a section folder, like _recipes/mains/my-recipe.md"))
    elif not (SECTIONS / f"{section}.md").exists():
        problems.append(("error", f"The folder '{section}' has no matching section file. Create _sections/{section}.md (see templates/section-template.md)."))
    if not GOOD_NAME.match(path.stem):
        problems.append(("error", f"File name '{path.name}' should be lowercase words joined by dashes, like chicken-adobo.md"))

    text = path.read_text(encoding="utf-8-sig").replace("\r\n", "\n")
    fields, body = parse_front_matter(text, problems)
    if fields is None:
        report.file(path, problems)
        return

    for key in fields:
        if key not in RECIPE_KEYS:
            close = difflib.get_close_matches(key.lower(), RECIPE_KEYS, n=1)
            hint = f" Did you mean '{close[0]}'?" if close else f" Known names: {', '.join(sorted(RECIPE_KEYS))}."
            problems.append(("warning", f"'{key}' isn't a recipe field the website uses.{hint}"))

    if not fields.get("title"):
        problems.append(("error", "Missing a title. Add a line like:  title: Chicken Adobo"))
    elif fields["title"] == "Recipe Name Here":
        problems.append(("error", "The title is still 'Recipe Name Here'."))

    if fields.get("tags") is not None and not isinstance(fields["tags"], list):
        problems.append(("error", "tags should be a list in square brackets, like  tags: [quick, budget]"))

    if fields.get("image"):
        check_image(folder, fields["image"], "Photo", problems)

    for ref in re.findall(r"!\[[^\]]*\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)", body):
        check_image(folder, ref, "Photo in the recipe", problems)
    for ref in re.findall(r"\{%\s*include\s+photo\.html\s+file=\"([^\"]+)\"", body):
        check_image(folder, ref, "Photo in the recipe", problems)

    if fields.get("coming_soon"):
        report.soon.append(path)
    else:
        ingredients = section_list_items(body, "Ingredients", numbered=False)
        steps = section_list_items(body, "Steps", numbered=True)
        if ingredients is None:
            problems.append(("error", "Missing a '## Ingredients' heading."))
        elif not ingredients:
            problems.append(("error", "'## Ingredients' has no list. Start each ingredient with '- '."))
        if steps is None:
            problems.append(("error", "Missing a '## Steps' heading."))
        elif not steps:
            problems.append(("error", "'## Steps' has no numbered list. Start each step with '1. ', '2. ', ..."))
        if not fields.get("description"):
            problems.append(("warning", "No description. A one-line description shows on the recipe card."))
        if (fields.get("description") or "").startswith("One short sentence about why"):
            problems.append(("warning", "The description is still the template's example sentence."))
        if "1 cup ingredient" in body or "First step." in body:
            problems.append(("warning", "Still has the template's example ingredients/steps in it."))
        if re.search(r"\bTODO\b", body):
            problems.append(("warning", "Contains TODO."))

    if re.search(r"^#\s", body, re.M):
        problems.append(("warning", "Use '## ' (two #) for headings. A single '# ' heading duplicates the page title."))

    report.file(path, problems)


def check_section(path, report):
    problems = []
    if not GOOD_NAME.match(path.stem):
        problems.append(("error", f"File name '{path.name}' should be lowercase words joined by dashes, like baked-goods.md"))
    text = path.read_text(encoding="utf-8-sig").replace("\r\n", "\n")
    fields, _ = parse_front_matter(text, problems)
    if fields is not None:
        for key in fields:
            if key not in SECTION_KEYS:
                problems.append(("warning", f"'{key}' isn't a section field. Known names: {', '.join(sorted(SECTION_KEYS))}."))
        if not fields.get("title"):
            problems.append(("error", "Missing a title."))
        if fields.get("order") is not None and not str(fields["order"]).isdigit():
            problems.append(("error", "order must be a whole number, like  order: 3"))
        if fields.get("order") is None:
            problems.append(("warning", "No order number, so this section may show up in a random spot."))
    if not (RECIPES / path.stem).is_dir():
        problems.append(("warning", f"No recipe folder yet. Create _recipes/{path.stem}/ and put recipes in it."))
    report.file(path, problems)


def check_stray_files(report):
    for path in sorted(RECIPES.rglob("*")):
        if path.is_dir() or path.suffix.lower() == ".md" or path.suffix.lower() in IMAGE_EXTS:
            continue
        if path.suffix.lower() in (".heic", ".heif"):
            msg = "iPhone .heic photos don't show in web browsers. Export it as .jpg instead."
        else:
            msg = "This file isn't a recipe (.md) or a photo, and will be published as-is."
        report.file(path, [("warning", msg)])


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    report = Report()

    if len(sys.argv) > 1:
        targets = [Path(a).resolve() for a in sys.argv[1:]]
        for t in targets:
            if not t.exists():
                print(f"Can't find {t}")
                sys.exit(1)
            (check_section if t.parent == SECTIONS else check_recipe)(t, report)
        checked = len(targets)
    else:
        sections = sorted(SECTIONS.glob("*.md"))
        recipes = sorted(RECIPES.rglob("*.md"))
        for s in sections:
            check_section(s, report)
        for r in recipes:
            check_recipe(r, report)
        check_stray_files(report)
        checked = len(recipes)
        print(f"\nChecked {len(sections)} sections and {len(recipes)} recipes.")

    if report.soon:
        print(f"{len(report.soon)} recipe(s) still marked coming_soon (that's fine, they show as 'Coming soon').")
    if report.errors:
        print(f"✖ {report.errors} error(s) to fix, {report.warnings} warning(s).")
        sys.exit(1)
    print(f"✔ No errors{f' ({report.warnings} warning(s))' if report.warnings else ''}. "
          f"{'Looks good!' if checked else ''}")


if __name__ == "__main__":
    main()
