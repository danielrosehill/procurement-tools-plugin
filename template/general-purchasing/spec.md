# Purchase Spec

*This single file is the source of truth for **this purchase**. One repo = one purchase. Populate via `/intake`, or edit directly.*

**Standing preferences** (country, currency, trusted brands, markup threshold, risk tolerance, etc.) live in **memory** — not here. Load them with `/load-preferences` before running `/intake`. This file captures only what's specific to this decision.

**Status**: Not yet configured
**Created**: [Date]
**Last updated**: [Date]

---

## What I'm buying

[Short description — e.g. "14-inch laptop for technical writing and light dev work"]

**Category**: [Free-form label — e.g. "laptop", "drill", "office chair"]

**Primary use case**: [The one thing this product needs to do well]

---

## Must-haves

*Hard positive requirements. A product that fails any of these is disqualified.*

- [ ] [Requirement 1]
- [ ] [Requirement 2]
- [ ] [Requirement 3]

---

## Hard nos / Dealbreakers

*Disqualifying characteristics — distinct from must-haves. Standing "avoided brands" from memory also apply here, but anything listed here overrides and extends the standing list for this purchase.*

- [ ] [Dealbreaker 1 — e.g. "No soldered RAM"]
- [ ] [Dealbreaker 2 — e.g. "No glossy screens"]
- [ ] [Dealbreaker 3]

---

## Nice-to-haves

*Soft preferences. Break ties but don't disqualify.*

- [Feature 1]
- [Feature 2]

---

## Budget (this purchase)

**Target**: [Amount + currency]
**Ceiling**: [Hard upper limit]
**Flexibility**: [Hard limit / Flexible for the right product / Very flexible]

---

## Timeline

**Urgency**: [ASAP / Within a week / Within a month / No rush]
**Deal-hunting**: [Yes / No]

---

## Priorities (this purchase)

*Ranked factors that matter most for this specific decision. Overrides the standing priority order from memory if the user has one.*

1. [e.g. "Durability"]
2. [e.g. "Value vs RRP"]
3. [e.g. "Feature match"]

---

## Buyer profile

*Optional bias layer from `buyer-profiles/`. Populated by `/apply-profile`. Acts as a tie-breaker after the explicit priorities above. Leave empty if not using a profile.*

**Applied profile(s)**: [e.g. "BIFL + Power User" — or "None"]
**Applied at**: [Date or blank]

**Profile priorities** (tie-breakers after this-purchase priorities):
- [Populated by /apply-profile]

**Preferred signals**:
- [Populated by /apply-profile]

**Red flags**:
- [Populated by /apply-profile]

**Weight adjustments**:
- [Populated by /apply-profile]

**Tensions flagged**: [Only if conflicting profiles were combined]

---

## Per-purchase overrides to standing preferences

*Leave blank to inherit from memory. Populate only what differs for this purchase.*

| Standing preference | Override for this purchase |
|---------------------|----------------------------|
| Markup threshold | [e.g. "Willing to go to 60% for this one — niche item"] |
| Risk tolerance | [e.g. "High — one-off need, not critical"] |
| International shipping | [e.g. "Not this time — need it in 3 days"] |

---

## Context / history

**Replacing**: [If applicable — what and why]
**Past experience**: [Relevant products owned in this category]
**Compatibility constraints**: [Ecosystem, accessories, space limits]
**Other notes**: [Anything else]

---

## Standing preferences snapshot

*Populated automatically by `/load-preferences`. This is a read-only audit trail of the memory-backed preferences applied at intake time. Edit in memory via `/save-preferences`, not here.*

- **Country**: [from memory]
- **Currency**: [from memory]
- **VAT status**: [from memory]
- **Standing trusted brands**: [from memory]
- **Standing avoided brands**: [from memory]
- **Markup threshold (default)**: [from memory]
- **Risk tolerance (default)**: [from memory]
- **International shipping**: [from memory]
- **Preferred vendors**: [from memory]
- **Avoided vendors**: [from memory]
- **Review score floor**: [from memory]
- **Email for PDF**: [from memory]

---

*Spec populated via `/intake`. Standing preferences loaded via `/load-preferences` from the gateway `memory` server (if available).*
