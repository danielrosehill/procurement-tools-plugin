# Conformance Matrix

*Every live option against every requirement. Maintained by `/purchasing:mkt-matrix`.*

**Field version**: `landscape/field.md` as of [Date] — [N] live entries
**Built**: [Date]

---

## Cell values

`yes` verified as meeting it · `no` verified as not · `partial` conditionally, condition in the notes · `?` **not verified — never a guess**

Every `yes` / `no` rests on a primary source with a date. Every `?` carries a note on what would resolve it.

---

## Must-haves

| Option | Segment | [MH1] | [MH2] | [MH3] | Clears all? |
|---|---|---|---|---|---|
| [Name] | [Segment] | yes | ? | partial | no |

---

## Hard nos

*Read each column as **the disqualifying characteristic**: `yes` means the option **has** it and is therefore out.*

| Option | [HN1] | [HN2] | Clear? |
|---|---|---|---|
| [Name] | no | no | yes |

---

## Nice-to-haves

*Not scoring — cluster detection. A nice-to-have present across one segment and absent from another is a segment boundary.*

| Option | Segment | [NTH1] | [NTH2] |
|---|---|---|---|

---

## Cell notes

*One line per non-obvious cell: source, date, and the condition attached to any `partial`.*

- **[Option] × [MH2] = `?`** — [what's missing and what would resolve it]
- **[Option] × [MH3] = `partial`** — [the condition under which it holds]

---

## What the matrix says about the field

*About the field, not about individual options.*

- **Clears everything**: [N options — which segments. If zero, that's the survey's headline.]
- **Columns nothing clears**: [Unmet requirements → `gaps.md`]
- **Columns everything clears**: [Over-served requirements → `gaps.md`]
- **Columns mostly `?`**: [Specs no vendor publishes — the buyer can't compare on these in advance]
- **Correlated columns**: [Requirements that always travel together — fewer independent choices than the spec implies]
