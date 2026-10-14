"""
The three FitFindr tools.

Each one is a standalone function you can call and test on its own, before any
of them are wired into the loop. Build and test them one at a time — three
untested tools joined by a loop is one problem that looks like six, because you
can't tell which layer is lying to you.

    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)             → str
    create_fit_card(outfit, new_item)              → str

All three are stubs right now. They run and they do nothing — that's the
starting position and it's deliberate.

⚠️ Before you write any of them, fill in the **Tool Inventory** section of your
README (Milestone 2). Four lines per tool: what it does, each input with its
type, exactly what it returns, and what it returns when it has nothing to give.
That last line is what your loop branches on. "Returns a list" earns nothing —
the description has to say what is *in* the list.
"""

import re

import config
from generate import generate
from utils.data_loader import load_listings


# ── helpers for search_listings ───────────────────────────────────────────────

_STOPWORDS = {
    "a", "an", "the", "and", "or", "for", "of", "in", "on", "with", "to", "i",
    "me", "my", "want", "need", "looking", "find", "show", "some", "something",
    "any", "that", "is", "are", "size", "under", "below", "than", "less",
    "max", "up", "around", "about", "please", "like",
}


def _words(text: str) -> list[str]:
    """Lowercase alphanumeric words, with a trailing plural 's' trimmed."""
    out = []
    for w in re.findall(r"[a-z0-9]+", text.lower()):
        if len(w) > 3 and w.endswith("s") and not w.endswith("ss"):
            w = w[:-1]
        out.append(w)
    return out


def _size_matches(wanted: str, listing_size: str) -> bool:
    """
    True when every word of the requested size is a whole word of the listing's
    size. "M" matches "M", "S/M", "M/L"; it does not match "XL" or "US 9".
    "L" does not match "XL". "US 9" matches only "US 9".
    """
    want = re.findall(r"[a-z0-9.]+", wanted.lower())
    have = set(re.findall(r"[a-z0-9.]+", listing_size.lower()))
    return bool(want) and all(w in have for w in want)


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the listings data for items matching a description, and optionally a
    size and a price ceiling.

    This is the tool that doesn't call the model, which makes it the easiest one
    to test and the one to move onto MCP in unit 4.

    Args:
        description: keywords describing what the user wants
                     (e.g. "vintage graphic tee").
        size:        a size string to filter by, or None to skip size filtering.
                     Match case-insensitively — "M" should match "S/M".

                     ⚠️ Read the sizes in the data before you reach for a plain
                     substring test. `"s" in "us 9"` is True, and so is
                     `"l" in "xl"`. A filter that returns shoes when someone
                     asked for a small top reads like a broken search, and it
                     will quietly cost you in unit 4 when you test criterion 1.
                     What counts as a size match is part of your spec — decide
                     it and write it into your Tool Inventory.
        max_price:   maximum price, inclusive, or None to skip price filtering.

    Returns:
        A list of matching listing dicts, best match first.
        **Returns an empty list when nothing matches — an empty list, not None,
        and not an exception.** Your loop branches on this.

    Each listing dict has these fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand (str or None), platform

    Note that `brand` is None for most listings. That is deliberate and
    realistic — thrift listings often have no brand. If something you write
    assumes a brand is always there, you will find out in unit 4.

    TODO:
        1. Load every listing with load_listings().
        2. Filter by max_price and by size, when each is provided.
        3. Score what's left by keyword overlap with `description`.
        4. Drop anything scoring zero.
        5. Sort by score, highest first, and return the listing dicts —
           at most config.SEARCH_RESULT_LIMIT of them.

    Test it from a terminal before you move on:
        python -c "from tools import search_listings; print(search_listings('graphic tee', max_price=30))"
    """
    query_words = {w for w in _words(description) if w not in _STOPWORDS}
    if not query_words:
        return []

    # The last keyword is the thing being asked for ("boots" in "black boots");
    # the words before it describe it. An item that doesn't have that word in
    # its title, category, tags or colours is a different kind of thing, so it
    # is dropped rather than ranked.
    head = [w for w in _words(description) if w not in _STOPWORDS][-1]

    scored = []
    for item in load_listings():
        if max_price is not None and item["price"] > max_price:
            continue
        if size and not _size_matches(size, item["size"]):
            continue
        kind_words = set(
            _words(
                " ".join([item["title"], item["category"],
                          " ".join(item["style_tags"]), " ".join(item["colors"])])
            )
        )
        if head not in kind_words:
            continue

        title_words = set(_words(item["title"]))
        other_words = set(
            _words(
                " ".join(
                    [
                        item["description"],
                        item["category"],
                        " ".join(item["style_tags"]),
                        " ".join(item["colors"]),
                        item["brand"] or "",
                    ]
                )
            )
        )
        # a title hit counts a little more than a hit anywhere else
        score = sum(2 if w in title_words else 1 for w in query_words if w in title_words or w in other_words)
        if score > 0:
            scored.append((score, item))

    scored.sort(key=lambda pair: (-pair[0], pair[1]["price"]))
    return [item for _, item in scored[: config.SEARCH_RESULT_LIMIT]]


def _describe_item(item: dict) -> str:
    brand = item.get("brand") or "no brand listed"
    return (
        f"{item['title']} — {item['category']}, size {item['size']}, "
        f"{item['condition']} condition, colors: {', '.join(item['colors'])}, "
        f"style: {', '.join(item['style_tags'])}, brand: {brand}, ${item['price']:.0f} on {item['platform']}"
    )


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest one or two outfits.

    This one calls the model, through `generate()`. You don't need to think
    about rate limits — the adapter handles pacing for you.

    Args:
        new_item: a listing dict — the item the user is considering.
        wardrobe: a wardrobe dict with an 'items' key holding a list of items.
                  **It may be empty.** Handle that.

    Returns:
        A non-empty string with outfit suggestions.
        With an empty wardrobe, return general styling advice rather than
        raising or returning "". Unit 4 has you trigger the empty wardrobe on
        purpose, so decide now what it should do.

    TODO:
        1. Check whether wardrobe['items'] is empty.
        2. If it is, ask the model for general styling ideas for this item.
        3. If it isn't, format the wardrobe items into the prompt and ask for
           specific combinations naming pieces the user already owns.
        4. Return the model's response.

    Test it from a terminal before you move on:
        python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_example_wardrobe()))"
    """
    item_line = _describe_item(new_item)
    items = (wardrobe or {}).get("items") or []

    if not items:
        prompt = (
            f"A shopper is thinking of buying this secondhand piece:\n{item_line}\n\n"
            "They have not told us what else they own. Suggest one or two outfits "
            "built around it, using common pieces most people have (say what kind "
            "of piece, e.g. 'straight-leg jeans'). Keep it under 120 words, "
            "plain text, no headings."
        )
    else:
        owned = "\n".join(
            f"- {w['name']} ({w['category']}; {', '.join(w.get('colors', []))}"
            + (f"; {w['notes']}" if w.get("notes") else "")
            + ")"
            for w in items
        )
        prompt = (
            f"A shopper is thinking of buying this secondhand piece:\n{item_line}\n\n"
            f"Here is what they already own:\n{owned}\n\n"
            "Suggest one or two outfits that combine the new piece with items "
            "from that list. Name the owned pieces exactly as listed. Do not "
            "invent pieces they don't own. Keep it under 120 words, plain text, "
            "no headings."
        )

    text = generate(prompt, temperature=config.TEMPERATURE).strip()
    if not text:
        return (
            f"Style the {new_item.get('title', 'piece')} with simple basics in "
            "a neutral colour and let it be the statement."
        )
    return text


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Write a short caption someone would actually post about the find.

    This calls the model too.

    Args:
        outfit:   the outfit suggestion string from suggest_outfit().
        new_item: the listing dict for the item.

    Returns:
        A two-to-four sentence caption.
        If `outfit` is empty or whitespace, return a descriptive message rather
        than raising.

    The caption should read like a real post rather than a product description,
    mention the item and its price and platform once each, and be specific about
    the vibe.

    It should also come out **differently for different inputs**. If you run
    this three times on the same item and get three word-for-word identical
    strings, it's one of two things, and both are near the top of `config.py`:

        • CACHE_ENABLED — the adapter handed back an answer it already had
        • TEMPERATURE   — at 0.0 the model gives the same words every time

    TODO:
        1. Guard against an empty or whitespace-only `outfit`.
        2. Build a prompt with the item details and the outfit.
        3. Call generate() and return the response.

    Test it from a terminal before you move on:
        python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('jeans and white sneakers', load_listings()[0]))"
    """
    if not outfit or not outfit.strip():
        return "No fit card: there was no outfit suggestion to write about."

    prompt = (
        "Write a social-media caption (a 'fit card') for a thrift find.\n"
        f"Item: {new_item['title']}\n"
        f"Price: ${new_item['price']:.0f}\n"
        f"Platform: {new_item['platform']}\n"
        f"Outfit idea: {outfit}\n\n"
        "Rules: 2 to 4 sentences. Sound like a real person posting, not a "
        "product listing. Mention the item, the price, and the platform once "
        "each, and be specific about the vibe. At most two emoji. Output only "
        "the caption."
    )
    text = generate(prompt, temperature=config.TEMPERATURE).strip()
    if not text:
        return "No fit card: the model returned an empty caption."
    return text
