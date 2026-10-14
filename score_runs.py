#!/usr/bin/env python3
"""
Runs the scenarios five times each (via run_eval's own helpers, cache off),
then scores every try against the five written criteria in criteria.md and
prints the PASS/FAIL table.

    python score_runs.py --label before
    python score_runs.py --label after

run_eval.py deliberately leaves PASS/FAIL to the student. This is that
judgement, written down: each check below is one sentence of criteria.md.
It also writes the usual results/ file via run_eval.write_report.
"""

import argparse
import re
from unittest import mock

import config
import run_eval
import scenarios as scenario_module

# Criterion 5 asks for five different ceilings, so each try gets its own.
CEILING_QUERIES = [
    ("jeans under $30", 30),
    ("tee below 25", 25),
    ("jacket max 40", 40),
    ("tops $20", 20),
    ("boots under 60 dollars", 60),
]


def run_try(scenario, query):
    """One try, with the two model tools wrapped to record what reached them."""
    import agent

    seen = {"outfit_id": None, "card_id": None, "outfit_called": False}
    real_outfit, real_card = agent.suggest_outfit, agent.create_fit_card

    def outfit(item, wardrobe):
        seen["outfit_called"] = True
        seen["outfit_id"] = item["id"]
        return real_outfit(item, wardrobe)

    def card(text, item):
        seen["card_id"] = item["id"]
        return real_card(text, item)

    with mock.patch.object(agent, "suggest_outfit", outfit), \
            mock.patch.object(agent, "create_fit_card", card):
        record = run_eval.run_once({**scenario, "query": query})
    record["seen"] = seen
    return record


def sentences(text):
    return [x for x in re.split(r"(?<=[.!?])\s+", text.strip()) if x]


def first_sentence(text):
    s = sentences(text)
    return s[0].strip().lower() if s else ""


def passes(num, record, other_card=None, ceiling=None):
    session = record["session"] or {}
    seen = record["seen"]
    card = session.get("fit_card") or ""
    item = session.get("selected_item") or {}
    if record["crashed"]:
        return False
    if num == 1:
        return not session.get("error") and bool(session.get("outfit_suggestion")) and len(card.strip()) > 0
    if num == 2:
        msg = session.get("error") or ""
        return (bool(msg) and not seen["outfit_called"] and session.get("fit_card") is None
                and session.get("outfit_suggestion") is None and "Try" in msg)
    if num == 3:
        results = session.get("search_results") or []
        return bool(results) and item.get("id") == seen["outfit_id"] == seen["card_id"] == results[0]["id"]
    if num == 4:
        if not card:
            return False
        n = len(sentences(card))
        has_price = f"${item['price']:.0f}" in card or f"${item['price']}" in card
        has_platform = re.sub(r"\W", "", item["platform"]).lower() in re.sub(r"\W", "", card).lower()
        differs = other_card is None or first_sentence(card) != first_sentence(other_card)
        return 2 <= n <= 4 and has_price and has_platform and differs
    if num == 5:
        results = session.get("search_results") or []
        # an empty list is a legitimate answer to an over-budget query
        return ceiling is not None and all(r["price"] <= ceiling for r in results)
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", default="")
    parser.add_argument("--tries", type=int, default=5)
    args = parser.parse_args()
    config.CACHE_ENABLED = False

    rows = []
    for scenario in scenario_module.SCENARIOS:
        print(f"{scenario['name']}")
        tries = []
        for i in range(args.tries):
            query = scenario["query"]
            if scenario.get("criterion") == 5:
                query = CEILING_QUERIES[i % len(CEILING_QUERIES)][0]
            record = run_try(scenario, query)
            record["query"] = query
            tries.append(record)
            s = record["session"] or {}
            print(f"  try {i+1}: {'ERROR ' + s['error'][:50] if s.get('error') else 'ok'}"
                  f"{' CRASH ' + record['crashed'] if record['crashed'] else ''}")
        rows.append({"scenario": scenario, "tries": tries})

    run_eval.write_report(rows, args)

    state_rows = next(r for r in rows if r["scenario"].get("criterion") == 3)["tries"]
    table = ["| Criterion | Target | " + " | ".join(f"Try {i}" for i in range(1, args.tries + 1)) + " | Verdict |",
             "|---|---|" + "---|" * args.tries + "---|"]
    targets = {1: 4, 2: 5, 3: 5, 4: 4, 5: 5}
    for row in rows:
        num = row["scenario"].get("criterion")
        if not num:
            continue
        marks = []
        for i, rec in enumerate(row["tries"]):
            kw = {}
            if num == 4:
                kw["other_card"] = (state_rows[i]["session"] or {}).get("fit_card")
            if num == 5:
                kw["ceiling"] = CEILING_QUERIES[i % len(CEILING_QUERIES)][1]
            marks.append(passes(num, rec, **kw))
        n = sum(1 for m in marks if m)
        verdict = "MET" if n >= targets[num] else "MISSED"
        table.append(f"| {num}. {row['scenario']['name']} | {targets[num]} of 5 | "
                     + " | ".join("PASS" if m else "FAIL" for m in marks)
                     + f" | {verdict} ({n}/{args.tries}) |")
    print("\n" + "\n".join(table))


if __name__ == "__main__":
    main()
