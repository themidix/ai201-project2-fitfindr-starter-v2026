# Acceptance criteria — FitFindr

Five criteria that say what "working" means for this agent, written in unit 3
**before** any results existed.

An acceptance criterion names a target: a number, a count, a rate, or something
a person could plainly observe. *"The agent handles errors"* is an opinion.
*"When search returns nothing, the agent stops before calling the second tool,
in 5 of 5 tries"* is a criterion.

Under each one, write a sentence or two on **why that target** and not a
stricter one. A reason that says something about your tools, your loop, or the
data earns credit; *"80% seemed reasonable"* does not.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

**Two are written for you. You write three.**

---

## 1. A matching query completes all three tools

Given a query that matches at least one listing, the agent completes all three
tool calls and returns a fit card — in at least 4 of 5 tries.

**Why this target:**
Search is a plain keyword match, and the query parser is regex, so an
unusual phrasing ("something cute for brunch") can score zero on every
listing. Two of the three tools also call a model that can time out or be
rate limited. 4 of 5 allows for one such miss; 5 of 5 would be a promise
about a model I don't control.

---

## 2. An impossible query stops before the second tool

Given a query that matches no listings, the agent stops before calling
`suggest_outfit` and returns a message naming what to change — 5 of 5 tries.

**Why this target:**
This path never touches the model. It depends only on `search_listings`
returning `[]` and one `if` in `run_agent`, both deterministic code, so
there is nothing that could vary between tries. Anything under 5 of 5 would
mean a bug, not bad luck.

---

## 3. Something about state

For a matching query, `session["selected_item"]["id"]` equals the `id` of
the item passed to `suggest_outfit` and to `create_fit_card`, and equals
`session["search_results"][0]["id"]`, in 5 of 5 tries. Checked by wrapping
both tools and comparing the ids they received.

**Why this target:**
The item is chosen once and then handed on by way of the session. A state
bug (a stale variable, a different result picked the second time) would look
like the outfit being about the wrong garment, which reads as a model
problem. The ids are exact and the comparison involves no model output, so
5 of 5 is the only fair target.


---

## 4. Something about the fit card

For a matching query, the fit card is 2 to 4 sentences, contains the
item's price (e.g. "$28") and its platform name, and does not open with the
same first sentence as the card for a different item, in at least 4 of 5
tries.

**Why this target:**
Those are the things I'd be unhappy to see in a post: a card that omits the
price, rambles past four sentences, or is a template that opens the same way
for every item. Each is a string check I can count. It's 4 of 5 rather than
5 of 5 because the model sometimes writes a fifth sentence or spells the
platform differently ("Thred Up"), and the prompt can only ask, not force.


---

## 5. Your choice

When a query includes a price ceiling (e.g. "under $30"), every listing in
`session["search_results"]` has `price` less than or equal to that ceiling,
in 5 of 5 tries across 5 different ceilings, and the filter treats the
ceiling as inclusive (a $30 item survives "under $30").

**Why this target:**
A price ceiling is the one constraint a shopper states as a hard number, and
returning a $45 jacket for "under $30" makes the whole agent look broken.
Filtering is plain code on a float field, so there is no reason to accept a
miss. The ceiling comes from my regex, so the real risk is parsing ("$30" vs
"30 dollars"), which is why the test uses several phrasings.


---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 4 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath it, like this:

         ## 4. Something about the fit card

         The fit card is different every time.

         **Why this target:** ...

         > **Revised in unit 4:** For 5 different items, the 5 fit cards share
         > no opening sentence.
         >
         > **Why revised:** "different" wasn't checkable — two cards that
         > differed by one word still counted. The new version is something I
         > can actually score.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "I said the empty search stops it 5 of 5 times, but I got 3 of 5,
            so 3 of 5 is more realistic."

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.
     ───────────────────────────────────────────────────────────────────────── -->
