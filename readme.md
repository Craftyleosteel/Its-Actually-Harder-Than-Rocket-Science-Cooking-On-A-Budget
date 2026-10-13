# It's Actually Harder Than Rocket Science: Cooking on a Budget

A home cookbook website, built automatically by GitHub Pages.

**Live site:** https://craftyleosteel.github.io/Its-Actually-Harder-Than-Rocket-Science-Cooking-On-A-Budget/

---

## How it's organized

```
_sections/              one file per section (the tabs on the website)
  breakfast.md
  mains.md
  ...
_recipes/               one folder per section, one file per recipe
  breakfast/
    breakfast-burritos.md
    breakfast-burritos.jpg      <- photos go right next to the recipe
  mains/
    chicken-adobo.md
templates/              copy these when adding something new
  recipe-template.md      blank recipe
  recipe-example.md       a filled-in example to compare against
  section-template.md     blank section
scripts/                helper tools (see below)
```

The folder name inside `_recipes/` must match a file name in `_sections/`.
For example, `_recipes/mains/` goes with `_sections/mains.md`.

---

## Add a recipe

**Option A: in VS Code (easiest)**
`Terminal → Run Task… → Cookbook: New recipe`, pick the section, type the title. It creates the file for you.

**Option B: from a terminal**
```
python scripts/new_recipe.py mains "Chicken Adobo"
```

**Option C: by hand (works on github.com too)**
Copy `templates/recipe-template.md` into the right folder in `_recipes/` and rename it.
Use lowercase words joined by dashes: `chicken-adobo.md`.

### The recipe format

```markdown
---
title: Chicken Adobo
description: Salty, tangy, garlicky, and costs almost nothing.
image: chicken-adobo.jpg
servings: 4
prep_time: 10 min
cook_time: 45 min
cost: about $2 per serving
tags: [one-pot, filipino, freezer-friendly]
---

## Ingredients

- 2 lb chicken thighs
- 1/2 cup soy sauce

## Steps

1. Do this.
2. Then this.

## Notes

- Tips, swaps, leftovers.
```

Rules of thumb:
- The part between the `---` lines is the recipe info. Each line is `name: value` with a space after the colon.
- If a value has a colon in it, wrap it in quotes: `title: "Horchata: The Cheap Way"`.
- Only `title` is required. Delete any info lines you don't need.
- Ingredients start with `- `. Steps start with `1. `, `2. `, …
- Use `### For the sauce` under Ingredients to split ingredients into groups.
- `**bold**` for emphasis, and a line starting with `> ` becomes a highlighted tip box.
- **Coming soon:** while `coming_soon: true` is in the info, the website shows only the title and a "Coming soon" banner. Delete that line when the recipe is ready.

See `templates/recipe-example.md` for a complete example.

---

## Add photos

1. Save the photo **in the same folder as the recipe**, e.g. `_recipes/mains/chicken-adobo.jpg`.
   - Name it with lowercase letters and dashes, no spaces.
   - Use `.jpg` or `.png`. iPhone `.heic` photos need to be exported as JPG first.
   - Keep it under about 1 MB. Phone photos are big, so shrink them first (on Windows: open in Photos → `…` → Resize image).
2. **Main photo** (shown at the top and on the recipe card): add `image: chicken-adobo.jpg` to the info.
3. **Photos inside the recipe**, e.g. for a step:
   ```markdown
   ![The sauce should look like this](chicken-adobo-sauce.jpg)
   ```
   Or with a caption underneath:
   ```
   {% include photo.html file="chicken-adobo-sauce.jpg" caption="Reduce until syrupy" %}
   ```

On github.com you can drag photos straight into a folder with **Add file → Upload files**.

---

## Add a section

**VS Code:** `Terminal → Run Task… → Cookbook: New section`
**Terminal:** `python scripts/new_section.py "Drinks" 🍹`

This creates `_sections/drinks.md` and the folder `_recipes/drinks/`. Open the section file to change its
emoji, description, or `order` (its position in the menu: 1 comes first).

---

## Check your formatting

**VS Code:** `Terminal → Run Task… → Cookbook: Check the recipe I have open` (or *Check all recipes*)
**Terminal:** `python scripts/check_recipes.py`

It tells you exactly what's wrong and how to fix it, for example:

```
_recipes/mains/chicken-adobo.md
  ✖ Line 3: the value contains ': ' which confuses the website. Wrap the value in "double quotes".
  ✖ Photo 'Chicken-Adobo.JPG' wasn't found. Put the photo in _recipes/mains/
  ⚠ 'servngs' isn't a recipe field the website uses. Did you mean 'servings'?
```

- **✖ errors** stop the website from updating, so a broken recipe never goes live.
- **⚠ warnings** are reminders. The site still updates.

**See what it looks like:** open a recipe in VS Code and press `Ctrl+Shift+V` for a preview (photos included).

The same check runs on GitHub every time you push. Look at the **Actions** tab: a green check means the
site updated, and a red X means click in to see what to fix.

---

## Publish / update the site

Any change pushed to the `main` branch rebuilds the site automatically within a minute or two.

**One-time setup** (already done if the live link above works):
GitHub repo → **Settings → Pages → Build and deployment → Source: GitHub Actions**.
