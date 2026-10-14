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

**Moment 3 (unit 4)**

- *What I asked for:* Run the five criteria five times each, and tell me whether I passed.
- *What came back:* A 5/5 on everything, which didn't match what I could see in the output: the selected item for `black boots under $60` was a pair of shorts.
- *What I changed:* I didn't treat the table as the answer. I added a relevance diagnostic that doesn't depend on the search's own scoring, measured 3/5 on it, changed one thing in `search_listings`, and re-ran. It then exposed a parser leftover ("dollars"), which I reported rather than fixed.

<!-- ═══════════════════════ UNIT 4 — THE TEST ═══════════════════════

     Don't fill these in during unit 3.
     ═══════════════════════════════════════════════════════════════════ -->

---

## Run Log — Before

Produced by `score_runs.py` (which wraps `run_eval.py::run_once`, cache off,
temperature 0.9, five tries per criterion), against `agent.py::run_agent` after
`search_listings` moved onto MCP. Full output: `results/run_2026-10-14_1821_before.md`.
Each PASS/FAIL applies the sentence in `criteria.md` (`score_runs.py::passes`).
For criterion 5 the five tries use five different ceilings and phrasings
(`score_runs.py::CEILING_QUERIES`); for criterion 4 the "different item" card
is the card from criterion 3's try with the same number.

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. matching query completes | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. impossible query stops early | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. state: selected item reaches both tools | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. fit card: length, price, platform | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 5. price ceiling respected | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |

**Real output from one try, per criterion** (try 1, `results/run_2026-10-14_1821_before.md`):

*Criterion 1 — produced by `agent.py::run_agent`, query `vintage graphic tee under $30`*

```
selected_item: Vintage Band Tee — Faded Grey ($19.0, depop)
Fit card: Found this perfectly faded grey vintage band tee and I'm obsessed with how soft it is. Grab it on my depop for just $19 before I change my mind and keep it for myself. Style it grungy with combat boots and denim, or dress it down with wide-leg trousers for that effortless streetwear look 🎸🖤
```

*Criterion 2 — `agent.py::run_agent`, query `designer ballgown size XXS under $5`*

```
stopped early: yes — No listings matched 'designer ballgown'. Try to drop or change the size (XXS), raise the price ceiling ($5), or try broader keywords like 'tee', 'jeans' or 'jacket'.
selected_item: (none)    fit_card: None    suggest_outfit calls: 0
```

*Criterion 3 — `agent.py::run_agent`, query `black boots under $60`. Scorer saw the same `id` at `selected_item`, `search_results[0]`, the `suggest_outfit` argument and the `create_fit_card` argument.*

```
selected_item: Biker Shorts — Black, Shiny ($14.0, depop)
```

*Criterion 4 — `tools.py::create_fit_card`, query `vintage graphic tee under $30`*

```
obsessed with the perfectly worn-in fade on this vintage band tee, up on my depop for just $19. lean into total grunge with baggy denim and combat boots, or switch it up with wide-leg trousers and a black denim jacket for an easy streetwear moment. 🖤
```

*Criterion 5 — `tools.py::search_listings` via `mcp_server.py`, query `jeans under $30`*

```
selected_item: Straight Leg Black Jeans — Faded ($30.0, thredUp)   (every result <= $30)
```

---

## Verdicts and Diagnoses

| # | Criterion | Target | Verdict | How I decided |
|---|---|---|---|---|
| 1 | Matching query completes all three tools | 4 of 5 | MET (5/5) | 5 PASS cells; target was 4. |
| 2 | Impossible query stops before tool 2 | 5 of 5 | MET (5/5) | 5 of 5 stopped with an error naming what to change; the wrapped `suggest_outfit` was never called. |
| 3 | Selected item is the item passed on | 5 of 5 | MET (5/5) | The four ids matched in all 5 tries. |
| 4 | Fit card 2-4 sentences, price, platform, distinct opening | 4 of 5 | MET (5/5) | 5 PASS cells; counted by regex in `score_runs.py`. |
| 5 | No result over the price ceiling | 5 of 5 | MET (5/5) | 5 different ceilings, 0 results over the ceiling in all 5. |

**Diagnoses**

Nothing missed, so there is no failing stage to name. What I can say honestly
is that my targets were too easy, and I can point at the evidence.

- **Criterion 3 passes while the agent is wrong.** For `black boots under $60`,
  the criterion-3 scenario passed 5 of 5, and in all five tries the "selected
  item" was **Biker Shorts — Black, Shiny**. State was perfect; the item was not
  what was asked for. Stage: the tool (`tools.py::search_listings`). Mechanism:
  every query word counts the same, so the colour "black" in a title scores
  2 and the noun "boots" in the title of "Suede Chelsea Boots — Tan" also scores
  2. They tie, and the tie is broken by lower price, so the $14 shorts beat the
  $44 boots. Criterion 1 (target 4 of 5) can't see this either: it only asks
  that three tools ran.
- **Tighter target I would set:** "For 5 queries naming a garment, the top
  result's title contains that garment (or the list is empty because nothing
  with it fits the size and price) — 5 of 5." Criterion 1 as written is a
  statement about the loop, not about whether the answer is any good. The
  diagnostic below measures that sentence:

```
Before the change
| Diagnostic | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Result |
|---|---|---|---|---|---|---|---|
| top result is the thing asked for | 5 of 5 | FAIL | FAIL | PASS | PASS | PASS | 3/5 |
  FAIL  'black boots under $60'                  -> Biker Shorts — Black, Shiny
  FAIL  'cropped black hoodie size M'            -> Mesh Long-Sleeve Top — Black
  PASS  'denim jacket under $50'                 -> Denim Jacket — Light Wash, Cropped
  PASS  'white sneakers'                         -> Low-Top Canvas Sneakers — Off-White
  PASS  'vintage graphic tee under $30'          -> Vintage Band Tee — Faded Grey
```

- **Criterion 4 was also loose.** All five cards open differently, but they
  share phrases ("obsessed with", "grab it before I change my mind and keep it"),
  which my "different opening sentence" check passes. Tighter target: no more
  than 2 of 5 cards for the same item contain the same 4-word phrase.

I did not revise any criterion in `criteria.md`: none of them was unmeasurable,
they were measurable and easy.

---

## Loop Trace

**Happy path** (`python app.py ask 'denim jacket under $50' --trace`; `agent.py::run_agent`)

```
[1] parse_query
      in:  denim jacket under $50
      out: dict with keys: description, size, max_price
[2] search_listings (via MCP)
      in:  dict with keys: description, size, max_price
      out: 2 items: Denim Jacket — Light Wash, Cropped, 90s Track Jacket — Navy/White Stripe
[3] select
      out: Denim Jacket — Light Wash, Cropped ($42.0, poshmark)
      →    took the first (best-scored) result
[4] suggest_outfit
      in:  Denim Jacket — Light Wash, Cropped + 10 wardrobe items
      out: Outfit 1: Pair the Wrangler denim jacket with the white ribbed tank top, baggy straight-leg jeans, and chunky …
[5] create_fit_card
      in:  Denim Jacket — Light Wash, Cropped
      out: Obsessed with the 90s streetwear vibe of this cropped Wrangler light wash denim jacket, especially since it wa…
```

**Empty search** (`python app.py ask 'designer ballgown size XXS under $5' --trace`) — three steps, then it stops:

```
[1] parse_query
      in:  designer ballgown size XXS under $5
      out: dict with keys: description, size, max_price
[2] search_listings (via MCP)
      in:  dict with keys: description, size, max_price
      out: [] (empty)
[3] branch
      →    search returned [] — stopping before suggest_outfit
```

**The three failure modes, triggered on purpose**

| Failure | How I triggered it | What the agent said |
|---|---|---|
| Empty search | `designer ballgown size XXS under $5` | `No listings matched 'designer ballgown'. Try to drop or change the size (XXS), raise the price ceiling ($5), or try broader keywords like 'tee', 'jeans' or 'jacket'.` |
| Empty wardrobe | `python app.py ask 'oversized denim jacket under $60' --empty-wardrobe` | Not a crash and not an empty string: `suggest_outfit` returned general styling advice ("Pair the cropped Wrangler jacket with a fitted white ribbed tank top and high-waisted black straight-leg jeans…") and the card was written from it. |
| Model unavailable | `GEMINI_API_KEY=AQ.badkeyXXXX AI201_CACHE=0 python app.py ask 'striped knit sweater'` (set in the shell only; `.env` untouched) | `The model couldn't be reached while running 'outfit'. The model rejected your API key. Check GEMINI_API_KEY in your .env file, or create a fresh key at aistudio.google.com. Nothing was lost: fix the problem above and ask again.` The search step had already run. This was a crash-free handler I added: `agent.py::run_agent` catches `ModelUnavailable` (and `MCPError` for the search server). |

**On the MCP move:** `search_listings` is registered in `mcp_server.py` with its
description and typed inputs, and `run_agent` calls it with
`mcp_client.call_tool("search_listings", {...})`. The other two tools are
called directly. Nothing behaved differently: for three queries the MCP result
was `==` to the direct call (7, 2 and 0 results). The costs are speed (each call
starts a Python process) and that the trace says `(via MCP)`.

---

## The Improvement

**What I changed:** In `tools.py::search_listings`, the last keyword of the
description is treated as the kind of thing being asked for. A listing whose
title, category, tags or colours don't contain it is dropped instead of ranked.
That is one change in one function; the MCP server wraps it unchanged.

**Which failure it was meant to fix:** The diagnosis above: `black boots under
$60` returned Biker Shorts because a matching colour tied with the matching
noun and price broke the tie. Under the new rule the shorts are dropped
because they are not "boots".

### Run Log — After

`results/run_2026-10-14_1825_after.md`, same scorer, same format.

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. matching query completes | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. impossible query stops early | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. state: selected item reaches both tools | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. fit card: length, price, platform | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 5. price ceiling respected | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |

Relevance diagnostic (the sentence I should have written as a criterion), before and after, same five queries:

```
Before
| Diagnostic | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Result |
|---|---|---|---|---|---|---|---|
| top result is the thing asked for | 5 of 5 | FAIL | FAIL | PASS | PASS | PASS | 3/5 |
  FAIL  'black boots under $60'                  -> Biker Shorts — Black, Shiny
  FAIL  'cropped black hoodie size M'            -> Mesh Long-Sleeve Top — Black
  PASS  'denim jacket under $50'                 -> Denim Jacket — Light Wash, Cropped
  PASS  'white sneakers'                         -> Low-Top Canvas Sneakers — Off-White
  PASS  'vintage graphic tee under $30'          -> Vintage Band Tee — Faded Grey

After
| Diagnostic | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Result |
|---|---|---|---|---|---|---|---|
| top result is the thing asked for | 5 of 5 | PASS | PASS | PASS | PASS | PASS | 5/5 |
  PASS  'black boots under $60'                  -> Suede Chelsea Boots — Tan
  PASS  'cropped black hoodie size M'            -> []
  PASS  'denim jacket under $50'                 -> Denim Jacket — Light Wash, Cropped
  PASS  'white sneakers'                         -> Low-Top Canvas Sneakers — Off-White
  PASS  'vintage graphic tee under $30'          -> Vintage Band Tee — Faded Grey
```

**Did it help, and how do I know:** The relevance diagnostic went from 3/5 to
5/5: `black boots` now returns the Chelsea boots and `cropped black hoodie size M`
returns an empty list, correctly, since the only hoodie is size L, so the
agent stops and tells the user to change the size. The five criteria were 5/5
before and after, so they could not show the difference; they were never going
to. It also **cost something**: in the after run, try 5 of criterion 5 used
`boots under 60 dollars`, and it returned *no results*. The parser removes
"under 60" and leaves "dollars", which is now the last word and so the "kind of
thing"; nothing is called "dollars". That try is a PASS only because an empty
list is never over the ceiling. The "after" 5/5 for criterion 5 is therefore
weaker than it looks, and I'm not counting it as a clean pass.

---

## What's Still Broken

- **The `dollars` leftover (regression I caused).** `agent.py::parse_query`
  strips "under 60" but not the word "dollars", and my new rule turns the last
  leftover word into a hard requirement. Fix: strip a trailing currency word in
  the parser. I did not make it because this unit allows one improvement, and
  I wanted the measured change to be the change I reported.
- **"Top" matches inside "Low-Top".** `tops $20` returns "Low-Top Canvas
  Sneakers" as the second result because the stem `top` is in its title.
  A category-aware match (use `category == "tops"`) would fix it.
- **The head noun is just the last word.** `tee in black` makes "black" the
  head, which matches the colour field, so the noun isn't enforced.
- **Criterion 4 is satisfiable by a template.** See the diagnosis; I'd tighten
  it to a repeated-phrase count. I stopped because it needs a prompt change,
  which would be a second improvement.
- **The search only matches words.** "something cute for brunch" still returns
  nothing. I'd need embeddings or the model to rewrite the query, and that is
  a different project.

---

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
