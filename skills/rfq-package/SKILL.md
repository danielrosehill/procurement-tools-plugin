---
name: rfq-package
description: Assemble a request for quotation from a bill of materials — line descriptions a supplier can actually quote, substitution rules, delivery and terms, and the questions worth asking. Use when a shopping list is ready to go out to suppliers, when comparing quotes from several suppliers on the same basis, or when a purchase needs a supplier's input on what they carry. Produces a JSON RFQ document plus a plain-text version for an email body; branded PDF rendering and sending are handed to the dsrholdings-rfq plugin.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(python3 *), Bash(ls *), Bash(cat *), Bash(mkdir *), Bash(date *)
---

# RFQ package

Turns a BOM into a document a supplier can quote against, and — where several
suppliers are being asked — into the *same* document for each, so the quotes
that come back are comparable.

This skill builds the **content**. It does not render a branded PDF and does not
send anything. See "Where this stops", below.

Requires a `bom.yaml` — see the `bom-build` skill.

## 1. Decide the scope of the request

One RFQ per supplier per coherent set of lines. A BOM spanning three trades sent
whole to one supplier gets a partial quote with silent omissions, which is worse
than three focused requests. Use BOM groups:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/spec_tools.py" rfq bom.yaml \
  --vendor "Supplier name" --number RFQ-2026-014 --group measurement \
  -o rfq/RFQ-2026-014.json
```

Contingent lines are dropped automatically. Optional lines are kept and marked
to be priced separately.

## 2. Read the generated document before it goes anywhere

The projection is mechanical; the judgement is not. Check:

**Descriptions stand alone.** The supplier has not read your spec. Every line
must be quotable by someone who knows their catalogue and nothing about your
project. If a description only makes sense next to `spec.yaml`, rewrite it in
the BOM and regenerate — not in the RFQ, or the two drift.

**The substitution rule is right per line.** Generated notes say what latitude
the supplier has. A blanket "no substitutions" reads as inflexible and loses you
the alternative they would otherwise have proposed.

**The purpose statement is there and is honest.** Suppliers quote better against
a stated purpose, and it is what lets them propose something that actually
works. It also protects you: a supplier who knows what the kit is for will often
say "that won't do what you want" before taking your money.

**Quantities and units match how this trade sells.** Per unit, per pack, per
metre. Get it wrong and the cheapest quote is the one that misread it.

## 3. Target prices are opt-in, and ask first

`--targets` carries `target_price` from the BOM into the document. It is off by
default because it anchors the supplier: quotes cluster just under a stated
target, including quotes that would have come in below it.

It is worth including when the target is a genuine ceiling and you would rather
be told "not at that price" than receive an unaffordable quote — for a
long-lead or made-to-order item, that saves a round trip. Ask the user which
they want rather than deciding for them.

## 4. Sharpen the questions

The generated set is a floor: stock, lead time, alternatives, price breaks, what
is included in the price. Add what this purchase actually turns on:

- Whether the regional part number they stock is the one that was evaluated —
  attach the equivalence finding if there is one.
- Country of manufacture, where it decides warranty or lead time.
- Whether a listed price is trade or list, and what account is needed for trade.
- Whether they can supply against a specification rather than a part number.
- Certification or documentation that has to arrive with the goods.

Each question should be one a supplier can answer in a line. A list of fifteen
gets a reply to the first three.

## 5. Delivery and terms

The generated document names the **destination profile**, not the address —
addresses live in the private config that `price-scan` reads, and the RFQ is a
file in a repo. Fill the real address at send time, or say "full address on
request" and let the supplier ask.

Where relevant, state incoterms explicitly. For cross-border quotes, "delivered"
means different things to different suppliers, and a quote that turns out to
exclude duty is not comparable with one that includes it.

## 6. Track what comes back

Log each supplier's response against the **line ids**, not against product
names. Line ids are stable across BOM revisions, which is what makes a quote
received at revision 2 still matchable at revision 4. Record no-quotes and
substitution proposals too: a supplier declining a line is information about the
market, and a proposed alternative is a candidate that belongs in
`evaluation-matrix` rather than accepted on the supplier's word.

## Where this stops

**This skill does not send anything.** Emailing a supplier is an outward-facing
action; it gets explicit confirmation each time, and approval for one does not
carry to the next.

**Rendering and sending are handled elsewhere.** The generated JSON conforms
exactly to the input schema of the
[`dsrholdings-rfq`](https://github.com/danielrosehill/dsrholdings-rfq-plugin)
plugin, which renders a branded PDF and sends it from the business address. Hand
over to `dsrholdings-rfq:create-rfq` / `:send-rfq` for anything going out under
the business identity.

That schema is `additionalProperties: false`, so nothing procurement-tools
specific can be smuggled into the document — no line ids, no spec references, no
provenance. Those stay in `bom.yaml` and in a sidecar next to the RFQ. If you
add a field to the generated JSON, add it to the renderer's schema first, or the
document will be rejected.

For an RFQ that is **not** going out under the business identity — an informal
request, a personal purchase, a list pasted into a supplier's web form — the
JSON plus a plain-text rendering of it is the deliverable. Write the plain-text
version alongside it; most trade counters want a pasteable list, not an
attachment.

## Hands off to

- `dsrholdings-rfq:create-rfq` — branded PDF and supplier correspondence.
- `evaluation-matrix` — for judging a supplier's proposed alternative against the spec instead of taking their word for it.
- `price-scan` — the retail-side counterpart. A price scan asks what a marketplace charges today; an RFQ asks a supplier what they will charge you.
