---
name: quote-compare
description: Compare and rank seller quotes on total delivered price, warranty, condition, lead time and seller grade; name the best offer
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(cat *), Bash(date *), Bash(git *)
---

# Quote compare

Ranks the offers sellers have actually confirmed, so the user can pick. Step 6
of the `quote-loop`. Different from `market-evaluator`, which ranks products
from research: this ranks **quotes in hand**, from named sellers, with what each
seller has and hasn't confirmed in writing.

## Inputs

- The contact log (default `docs/sellers-contacted.md`, or
  `quote_loop.contact_log_path` in the overlay).
- The purchase constraints (as in `seller-shortlist`) and the spec, for fit.
- Locale profile, for currency and cultural notes (e.g. whether returns are a
  realistic fallback).

## Steps

1. **Collect offers** from the log: every seller that quoted a price. A listed
   website price the seller hasn't confirmed is "unconfirmed", not an offer.
2. **Normalise to total delivered price**: item + delivery + installation if
   needed, same currency, same tax basis (state inc/ex VAT). Unknown delivery
   counts as unknown, not zero.
3. **Tabulate**, one row per offer:

   | Seller | Product | Total delivered | Warranty | Condition | Lead time | Seller verdict | Constraint fit | Unconfirmed |
   |---|---|---|---|---|---|---|---|---|

   - **Condition:** "new, sealed (confirmed)" / "new (stated, not sealed)" /
     "unconfirmed" / display-outlet.
   - **Constraint fit:** pass / fail per constraint (reputable, new-only,
     excluded seller, spec fit). Any fail drops the offer from ranking; list it
     below the table with the reason.
4. **Rank** the passing offers: total delivered price first, adjusted by seller
   verdict (an "avoid" seller ranks last whatever its price) and by warranty and
   lead time where they differ materially. Where returns are hard, weight
   certainty (confirmed stock, confirmed fit) over a small saving, and say so.
5. **Name the best option** in one line, the runner-up, and **what is still
   unconfirmed** for each (stock, condition, fit, delivery date). Those
   unknowns become the next follow-up questions for `check-replies`.
6. Write the best-option line into the log's **Best offer** section and, if the
   workspace is a git repo, commit and push.

## Data storage

Writes only the contact log in the user's purchase workspace.

## Notes

- Never place or offer an order. The user picks; ordering is theirs.
- Same model from two sellers: the price gap is the cost of the better seller.
  Say it in money, not adjectives.
