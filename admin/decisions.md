# Design decisions

Newest first. Each entry records what was decided, why, and what would reverse it.

## 2026-11-24 — Product identifiers as a separate skill

`part-number-equivalence` maps MPNs across regions; barcodes differ: one MPN can
carry several, and listings mix siblings. So `product-identifiers` starts from a
trading name, grades each code by source, and records sibling codes to expose
mixed listings. `gtin.py` is offline; a valid check digit is never treated as
proof of product.

**Would reverse it:** a reliable open GTIN registry that returns MPN by variant.

## 2026-11-23 — Reference media in the quote loop

Sellers ask "can you send a photo?", and for made-to-order or "what would you
recommend" enquiries a photo of the current setup gets a better answer than a
description. So `check-replies` sends reference media when a seller asks for a
photo, drawing or measurements (phrases in each locale's
`media_request_phrases`), and `contact-sellers` attaches `first_contact` media
where fit matters, not for plain stock or price checks.

**Where it is declared:** a `## Reference media` table in the contact log
(path, caption, `send_when`), not a separate file or workspace config. The
skills already read the log on every run, the media is per purchase, and one
file keeps the purchase's state together. The files are the user's and stay in
the workspace, never in plugin data.

**How it is sent:** `quote_loop.messaging.send_media` in the user overlay
(staging command and its delete form, tool, request body). Most messaging
APIs take a URL rather than a local path, so a short-lived staged copy is the
general route; email uses an attachment. Missing route: describe in words.

**Privacy:** photos may show a home interior, so only to sellers in an active
enquiry, never groups or broadcasts, and staged copies are deleted after each
send.

**Would reverse it:** messaging tools accepting local file paths directly
(drop the staging step), or media needed outside the quote loop (move the
declaration to a workspace config).

## 2026-11-23 — Vendor identification as the quote loop's discovery step

`vendor-identification` replaces the one-line research step in `quote-loop`.
It is vendor-first ("who could supply this") rather than product-first ("where
is this model sold"), because the purchases the quote loop exists for often
have no retail listing: made-to-order work and local workshops. It links to
`israel-shopping:find-product` and `store-reputation` instead of duplicating
them. Channels (query idiom and commercial-word ladder, aggregators, chains,
directories, trade nouns, importer lookup, warnings) are a `vendor_identification`
block in each locale profile, consistent with the locale-as-data decision
below. It reads the contact log before searching so known operators never
reappear as "new" candidates; `seller-shortlist` still owns filtering and the
final dedupe.

**Would reverse it:** the locale's product finder gaining vendor-first and
trade/workshop search, at which point this skill becomes a thin router to it.

## 2026-11-23 — Quote loop: locale as data, private details in the overlay

The seller quote loop (`quote-loop`, `seller-shortlist`, `contact-sellers`,
`check-replies`, `quote-compare`) was generalised from a working purchase
workspace and absorbs `israel-shopping:ask-store`. Everything country-specific
(channel order, language, business hours, search idiom, reputation skill,
templates, cultural notes) is a JSON profile in `locales/`, so a new country is
a data file, not a skill fork. Tool names, callback number, exclusions and the
send-without-review switch live in the user overlay `config.json` under
`quote_loop`, because they are the user's, and the skills degrade to drafts and
forwarded replies without them. The contact log stays in the purchase workspace:
it is the user's record of a purchase, not plugin state.

**Would reverse it:** a second locale needing behaviour a profile can't express
(e.g. a channel with a different reply model), at which point that locale gets
its own skill and the profile points to it.

## 2026-09-02 — Workspace identity lives in a manifest file, not a directory naming convention

Every workspace gets `procurement.json` at its root with a stable
`PW-YYYYMMDD-XXXXXX` id.

A naming convention (`<Thing>-Purchase-MMDD`) was the previous answer and it
does not survive contact with reality: directories get renamed, folders get
promoted to repos, and a name carries no status, no spec revision and no report
trail. Parsing meaning back out of a directory name is guesswork that looks
like data.

The id is random-suffixed rather than sequential because sequential ids need a
central allocator, and there isn't one — workspaces get created on whatever
machine is to hand, sometimes offline. Date prefix keeps them sortable; six hex
characters make collision irrelevant at this volume.

**Would reverse it:** an actual database becoming the source of truth, at which
point the manifest becomes a cache of a row rather than the record itself.

## 2026-09-02 — Private is the default visibility for every workspace variant

Previously public by default, with `market-landscape` inverted to private.

The inversion had the reasoning right and the scope wrong: a landscape spec
describes what the user is planning, and so does a general-purchasing spec, a
tech-procurement rig plan and a vendor-recommendations preference profile. All
four state what someone intends to buy, what they will pay, and often where
they live. Public is the exception, not the rule.

## 2026-09-02 — Admin material ships in the repo rather than being gitignored

`admin/` is committed. Reasoning is in `admin/README.md`; the short version is
that a plugin's loadable surface is by convention directory only, so `admin/`
costs a user nothing, and a gitignored roadmap is invisible to the agent who
opens this repo cold six months from now.

The constraint that makes it safe: **no frontmatter in `admin/`**. The skill
substrate walks plugin repos and ingests skill-shaped content, so a `name:` or
`description:` block outside `skills/` is how a planning note gets indexed as a
skill by accident.

## 2026-09-02 — No GitHub template repo for the workspace scaffold

Considered, and rejected for now.

`gh repo create --template` gives GitHub-native provenance and one fewer local
step. Against that: it cannot serve **folder mode** at all, which is half the
requirement — `workspace-folder` copies a scaffold into an existing repo, and
there is no template mechanism for that. It also introduces a second release
cadence and a permanent drift risk between the template repo and the bundled
`template/` tree, and it makes provisioning need the network.

The bundled scaffold serves both modes, works offline, and is one `cp -r`.

**Would reverse it:** wanting the scaffold usable by people who do not have the
plugin installed. If that happens, the right shape is a **generated mirror** —
the bundled `template/` stays the source of truth and a script publishes it —
rather than a hand-maintained second copy.

## 2026-09-02 — The conformance matrix does not rank, and the ranker is a separate skill

Predates this file; recorded here because it keeps coming up and the separation
looks like duplication until the reason is stated.

`evaluation-matrix` answers "who qualifies" per requirement and deliberately
emits no score. `market-evaluator` is where ranking is allowed to happen. The
split exists because a weighted total buries exactly the trade-off the matrix
was built to expose, and because an `unknown` on a `must` requirement is
missing information rather than a low score — burying it in a ranking presents
ignorance as judgement.
