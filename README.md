# FitFindr

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first** — setup, every
> command, and what to do when something breaks.
>
> Once `python test.py` passes:
>
> ```bash
> python app.py listings --full -n 6      # read the data (Milestone 1)
> python app.py fields                    # what you can filter on
> python app.py ask 'vintage graphic tee under $30'
> ```
>
> All three tools are stubs, so that last command will do nothing useful yet.
> That's the starting position.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     HOW TO USE THIS FILE

     This is your submission. Fill each section in as you finish the milestone
     it belongs to — don't leave it all to the end.

     Unit 3 asks for the first five sections. Unit 4 adds the five below them.
     Leave the unit 4 sections alone until then; they're here so you know
     what's coming.

     Everything is pasted as TEXT. No screenshots, no images, no video links.
     A typed block of output gets full credit; a picture of the same output
     gets none.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 3 — THE BUILD ═══════════════════════ -->

## What This Does

FitFindr helps someone shop secondhand. They type what they want in plain
language ("vintage graphic tee under $30, size M"); the agent searches 40
thrift listings, picks the best match, suggests outfits built from clothes the
user already owns, and writes a short shareable caption (a "fit card") about
the find. If nothing matches, it stops and tells the user what to loosen
instead of making up an outfit for an item that doesn't exist.

---

## Tool Inventory

### `search_listings`

- **What it does:** Filters the 40 listings by price ceiling and size, scores the rest by keyword overlap with the description (title, description, tags, category, colors, brand), drops zero scores, and ranks best first. No model call.
- **Inputs:** `description` (str) keywords; `size` (str or None) — matches when every word of the requested size appears as a whole word in the listing's size, so `M` matches `M`, `S/M` and `M/L` but not `XL` or `US 9`; `max_price` (float or None) — inclusive ceiling.
- **Returns:** A list of up to `config.SEARCH_RESULT_LIMIT` (10) listing dicts (`id, title, description, category, style_tags, size, condition, price, colors, brand, platform`), highest keyword score first, ties broken by lower price.
- **When it has nothing:** Returns `[]` — an empty list, never `None`, never an exception. The loop branches on this.

### `suggest_outfit`

- **What it does:** Asks the model for one or two outfits that pair the thrifted item with pieces from the user's wardrobe, naming the owned pieces; with an empty wardrobe it asks for general styling advice instead.
- **Inputs:** `new_item` (dict) a listing; `wardrobe` (dict) with an `items` list of `{id, name, category, colors, style_tags, notes}`, possibly empty.
- **Returns:** A non-empty string of outfit suggestions.
- **When it has nothing:** Empty or missing wardrobe → general styling advice string (not `""`, no exception). If the model returns blank text, a short fallback string is returned.

### `create_fit_card`

- **What it does:** Asks the model to write a 2–4 sentence social-post caption about the find, mentioning the item, its price and its platform once each.
- **Inputs:** `outfit` (str) from `suggest_outfit`; `new_item` (dict) the listing.
- **Returns:** A caption string, 2–4 sentences.
- **When it has nothing:** If `outfit` is empty or whitespace, returns the message `"No fit card: there was no outfit suggestion to write about."` without calling the model.

---

## Planning Loop

**Branch rule:** If `search_listings` returns an empty list, put a message in `session["error"]` naming what to change (drop the size, raise the price ceiling, use broader keywords), return the session, and do not call `suggest_outfit` or `create_fit_card`. Otherwise take the first (best-scored) result as `selected_item`, call `suggest_outfit`, then `create_fit_card` with that same item.

**Where it lives:** `agent.py::run_agent`

**How the query is parsed:** Regex and string handling, no model call. `agent.py::parse_query` pulls a price ("under $30", "$30", "below 30") and a size ("size M", "size US 9", or a bare S/M/L/XL token), then strips those phrases and filler words; the remaining words are the description.

**What moves through the session:** `query` → `parsed` (description, size, max_price) → `search_results` → `selected_item` → `outfit_suggestion` → `fit_card`. Each tool reads its input back out of the session, and `error` is set only if the run stops early.

---

## Sample Run

**One full query**

```
$ python app.py ask 'vintage graphic tee under $30'

  Found:    Vintage Band Tee — Faded Grey — $19.0 on depop

  Outfit:   Outfit One: Pair the vintage band tee with the baggy straight-leg jeans, dark wash, and the brown leather belt. Layer the vintage black denim jacket on top and finish with the chunky white sneakers for a casual grunge street look. 

Outfit Two: Tuck the vintage band tee into the wide-leg khaki trousers, secured with the brown leather belt. Add the black combat boots and complete the outfit with the black crossbody bag for an effortless, vintage-inspired everyday vibe.

  Fit card: Finally letting go of this perfectly faded grey vintage band tee for $19 on depop, and honestly it has the ultimate grunge street vibe. Style it casually with baggy denim and chunky sneakers, or dress it up with khaki trousers and combat boots for an effortless everyday look 🎸🖤

0 model calls this session, 2 served from cache
```

**A query that matches nothing (the branch)**

```
$ python app.py ask 'designer ballgown size XXS under $5'

  No listings matched 'designer ballgown'. Try to drop or change the size (XXS), raise the price ceiling ($5), or try broader keywords like 'tee', 'jeans' or 'jacket'.

0 model calls this session
```

**The three tools, tested one at a time**

```
$ python -c "from tools import search_listings; print(search_listings('graphic tee', max_price=30))"
[{'id': 'lst_006', 'title': 'Graphic Tee — 2003 Tour Bootleg Style', 'description': 'Vintage-style bootleg tee with faded graphic. Slightly boxy fit. 100% cotton, soft and worn-in.', 'category': 'tops', 'style_tags': ['graphic tee', 'vintage', 'grunge', 'streetwear', 'band tee'], 'size': 'L', 'condition': 'good', 'price': 24.0, 'colors': ['black'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_002', 'title': 'Y2K Baby Tee — Butterfly Print', 'description': 'Super cute early 2000s baby tee with butterfly graphic. Fitted crop length. Tag says medium but fits like a small.', 'category': 'tops', 'style_tags': ['y2k', 'vintage', 'graphic tee', 'cottagecore'], 'size': 'S/M', 'condition': 'excellent', 'price': 18.0, 'colors': ['white', 'pink', 'purple'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_033', 'title': 'Vintage Band Tee — Faded Grey', 'description': 'Faded grey band-style tee with distressed graphic. Crew neck. Fits boxy. Well-loved but no holes or major damage.', 'category': 'tops', 'style_tags': ['vintage', 'grunge', 'band tee', 'graphic tee', 'streetwear'], 'size': 'L', 'condition': 'fair', 'price': 19.0, 'colors': ['grey', 'charcoal'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_017', 'title': 'Mesh Long-Sleeve Top — Black', 'description': 'Sheer black mesh long-sleeve. Great for layering under a graphic tee or over a bralette. Stretchy material, fits true to size.', 'category': 'tops', 'style_tags': ['y2k', 'grunge', 'goth', 'layering'], 'size': 'S/M', 'condition': 'excellent', 'price': 15.0, 'colors': ['black'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_015', 'title': 'Vintage Graphic Hoodie — Faded Black', 'description': 'Faded black pullover hoodie with barely-visible vintage graphic on the chest. Cozy interior. Some pilling but adds to the worn-in look.', 'category': 'tops', 'style_tags': ['vintage', 'grunge', 'graphic', 'streetwear'], 'size': 'L', 'condition': 'fair', 'price': 26.0, 'colors': ['black', 'charcoal'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_012', 'title': 'Oversized Crewneck Sweatshirt — Vintage Navy', 'description': 'Perfectly faded navy crewneck. Genuinely vintage — not manufactured distressed. Ribbed cuffs and hem. No graphics, clean.', 'category': 'tops', 'style_tags': ['vintage', 'basics', 'oversized', 'classic'], 'size': 'XL (fits oversized)', 'condition': 'good', 'price': 20.0, 'colors': ['navy'], 'brand': None, 'platform': 'thredUp'}, {'id': 'lst_011', 'title': 'Low-Rise Cargo Pants — Khaki', 'description': 'Y2K era low-rise cargo pants. Lots of pockets. Khaki color, slightly distressed at the hems. Great for layering with a long tee.', 'category': 'bottoms', 'style_tags': ['y2k', 'cargo', '2000s', 'streetwear'], 'size': 'W29', 'condition': 'fair', 'price': 27.0, 'colors': ['khaki', 'tan'], 'brand': None, 'platform': 'poshmark'}]
```

```
$ python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_example_wardrobe()))"
Outfit one: Pair the Vintage Levi's 501 Jeans with the white ribbed tank top, the oversized grey crewneck sweatshirt layered on top, and the chunky white sneakers. Add the black crossbody bag to complete this casual streetwear look. 

Outfit two: Style the Vintage Levi's 501 Jeans with the black cropped zip hoodie and the black combat boots. Cinch the waist with the brown leather belt and layer the vintage black denim jacket on top for a rugged, all-black-and-indigo ensemble.
```

```
$ python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('jeans and white sneakers', load_listings()[0]))"
Nothing beats finding a classic pair of vintage Levi's 501 jeans in the absolute best medium wash. Just styled them with crisp white sneakers for that effortless off-duty model vibe. Snagged these for $38 and they're currently live on my depop.
```

---

## How I Used AI

**Moment 1**

- *What I asked for:* An implementation of `search_listings` from my Tool Inventory spec, including the size rule I had written: a size matches only when every word of the request is a whole word of the listing's size.
- *What came back:* A tokenizing `_size_matches` (not a substring test), plus scoring that weights title hits double and breaks ties by lower price.
- *What I changed:* I checked it against the real sizes in the data rather than trusting it: `M` returned only `S/M` items, and `L` returned only `L` and `M/L`, never `XL` or shoes. Searching "graphic tee" ranks "Vintage Band Tee" above "Graphic Tee" for "vintage graphic tee" because of the tie-break, which I left alone.

**Moment 2**

- *What I asked for:* The planning loop in `agent.py::run_agent` following my branch rule, with query parsing done by regex.
- *What came back:* `parse_query` plus a step-based loop that stops after `search_listings` returns `[]`, with an error naming what to change.
- *What I changed:* I ran the parser on five phrasings ("under $30", "max 60", "$40", "size US 9", a bare "L") and wrapped both model tools to confirm the same `id` reached each one as `selected_item` (criterion 3). I ran both example paths in `python agent.py` to confirm the ballgown query returns `fit_card = None`.

<!-- ═══════════════════════ UNIT 4 — THE TEST ═══════════════════════

     Don't fill these in during unit 3.
     ═══════════════════════════════════════════════════════════════════ -->

---

## Run Log — Before

<!-- Five criteria, five tries each, in this exact format.

     Five, because your criteria are written out of five. Mark each try PASS
     or FAIL, count the passes, and read that count against your target — a
     row targeting 4 of 5 with three PASS cells is MISSED (3/5).

     `python run_eval.py --label before` runs everything and writes the table
     into results/. Paste it here and fill in the verdicts. -->

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Real output from one try**, pasted as text, naming the file and function
that produced it:

```

```

---

## Verdicts and Diagnoses

<!-- MET or MISSED per criterion against LAST UNIT's target, plus a sentence on
     how you decided.

     Then, for every miss: which of the four places it happened — a tool, the
     loop's branch, the session, or the model's output — AND the mechanism.

     Not a diagnosis:  "The fit card was bad."
     A diagnosis:      "The fit card criterion missed on 2 of 5 items. Both had
                        an empty brand field. My prompt puts the brand in the
                        first sentence, so the card opened with a blank and read
                        like a fragment. The tool worked; the prompt assumed a
                        field that isn't always there."

     Look for a pattern. Three misses on the same tool is one problem, not
     three. -->

| # | Criterion | Target | Verdict | How I decided |
|---|---|---|---|---|
| 1 |  |  |  |  |
| 2 |  |  |  |  |
| 3 |  |  |  |  |
| 4 |  |  |  |  |
| 5 |  |  |  |  |

**Diagnoses**



---

## Loop Trace

<!-- One full run, printed step by step, with the MCP call visible in it.

     `python app.py ask '...' --trace` once you've added the trace.step()
     calls in Milestone 2.

     Worth pasting BOTH the happy path and the empty-search path. The empty
     one should be visibly shorter, because it stops. If your two traces are
     the same length, your branch isn't working — and this is the fastest way
     anyone will ever find that out. -->

**Happy path**

```

```

**Empty search**

```

```

**On the MCP move:** <!-- what changed in your code, and whether anything
behaved differently afterwards. If the rewire didn't work, say exactly where it
broke — the error text and the last thing that worked. That earns the point in
full. -->



---

## The Improvement

<!-- What you changed, why your diagnosis pointed at it, and the after-run in
     the same table format. One change, measured properly.

     `python run_eval.py --label after` -->

**What I changed:**

**Which failure it was meant to fix:**

### Run Log — After

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Did it help, and how do I know:**

<!-- If it made things worse, say that. Honestly reported, that earns full
     credit and is more interesting than one that worked. -->



---

## What's Still Broken

<!-- For each criterion still missed: what you'd do, and why you stopped where
     you did. "I ran out of time" is fine if it's true. Pretending nothing is
     left is not. -->



<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 3

       [ ] criteria.md has five numbered criteria, each with a target
       [ ] Each criterion has a reason underneath it
       [ ] All five unit 3 sections above have real content
       [ ] Tool Inventory: all three tools, inputs WITH TYPES, a specific
           return value, and the empty case
       [ ] Planning Loop names the branch rule and agent.py::run_agent
       [ ] Sample Run: one full query plus the three per-tool tests, as text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN, you submit the same one
           next unit

     SUBMISSION CHECKLIST — unit 4

       [ ] mcp_server.py exists with one tool registered
           (or a written record of exactly where the rewire broke)
       [ ] Run Log — Before, five criteria, five tries each
       [ ] Real output pasted underneath, naming file and function
       [ ] A verdict on every criterion
       [ ] A diagnosis for every miss, naming a place AND a mechanism
       [ ] Loop Trace, with the MCP call visible in it
       [ ] All three failure modes triggered and handled
       [ ] One improvement, with Run Log — After in the same format
       [ ] What's Still Broken
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository. Your commit history is what
     shows your criteria existed before your results did.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
