# Gaps and Compromises

*What the spec asks for that the market doesn't supply, and what it asks for that everything supplies. Maintained by `/purchasing:mkt-gaps`.*

**Derived from**: `landscape/field.md` + the conformance matrix, as of [Date]

---

## Unmet requirements

*Asked for by the spec, supplied by nothing in the field. The headline finding of most surveys.*

| Requirement | Options meeting it | Nearest miss | Why nothing meets it |
|---|---|---|---|
| [Must-have 3] | 0 | [Option — how close, what's missing] | [Structural reason if there is one — e.g. "needs a certification no consumer vendor pursues"] |

**If nothing meets a must-have**, say so plainly at the top of the report. That is a complete and valuable answer to the survey: *this does not exist yet*. Do not soften it into a nearest-fit recommendation.

---

## Over-served requirements

*Met by everything in the field. Not choosing criteria — listing them as requirements just makes the spec look more constrained than it is.*

| Requirement | Options meeting it | Implication |
|---|---|---|
| [Must-have 1] | [N of N] | [Drop from the decision criteria — it doesn't separate anything] |

---

## Compromise axes

*Where the field forces a trade. No option is strong on both ends; the buyer picks a side.*

### [Axis name] — e.g. battery life vs weight

**The trade**: [What you give up to get what]
**Strong on side A**: [Options]
**Strong on side B**: [Options]
**Anything that does both?**: [Option + what it costs, or "no"]
**Which side the spec leans**: [From the requirement — or "spec doesn't say; needs a decision"]

---

## Where the market is thin

*Segments with few or no options — the shape of the hole.*

| Description of the hole | What would fill it | Plausible reason it's empty |
|---|---|---|
| [e.g. "sub-$200 with hardware mute"] | [The product that doesn't exist] | [e.g. "mute switch is a pro feature, and pro tier starts at $400"] |

---

## Conditional narrowings

*Not a ranking. If the user weights a particular axis, the field narrows — state the condition and the result, and let them choose the weighting.*

| If you weight… | The field narrows to | Ruling out |
|---|---|---|
| [Axis / requirement] | [Options] | [What you lose by weighting it this way] |

---

## Candidates worth a decision

*The handful that survive the spec and are worth taking into an actual purchase workspace. Deliberately unranked and deliberately short.*

| Option | Segment | Survives because | Open question before buying |
|---|---|---|---|
| [Name] | [Segment] | [Which requirements it clears that others don't] | [What still needs checking — price, availability, an unverified spec] |

**Hand-off**: `/purchasing:new-workspace <thing>-purchase-MMDD --variant=general-purchasing --private`, carrying this table and the requirements from `spec.md`.

---

## Unresolved

*Open questions the sweep couldn't close. Being explicit about these is what keeps the survey honest.*

| Question | Why unresolved | What would resolve it |
|---|---|---|
| [Question] | [e.g. "no vendor publishes this figure"] | [e.g. "hands-on test, or a teardown"] |
