# Define Spec — From a Vague Want to a Spec and a Search Vocabulary

You are running spec definition. This is the front door to the purchasing flow: the
user knows roughly what they want but not what it is called, so they cannot search
for it yet. Your job is to close that gap and emit **two** artefacts:

1. **`spec.md`** — a vendor-neutral capability specification. What the thing must do,
   in terms that do not presuppose a product.
2. **`search-terms.md`** — the search vocabulary. The exact strings to type into
   marketplaces, each annotated with what it skews toward and where to use it.

The second artefact is the point of this command. A specification the user cannot
search with is half a deliverable.

**Use this before `/procurement-tools:intake`**, not instead of it. `define-spec`
establishes *what the thing is*; `intake` captures *what this particular purchase
needs* (budget, timeline, dealbreakers). If the user already knows exactly what
they are buying, skip straight to `intake`.

## Step 0: Take the input in whatever form it arrives

Accept any of these, in any combination:

- A freeform description ("that clamp thing that holds a mic arm to a desk")
- **A photograph** — of the thing itself, of a similar thing, of the gap it has to fit
- A listing URL for something close but not right
- A part number, or a photo of a label
- The thing it has to attach to, connect to, or replace

If a photograph is supplied, read it properly before asking anything. Extract:

- Form factor and rough proportions
- Materials and finish
- Mounting or fixing method — threads, clamps, brackets, adhesive, magnets
- Connectors, ports, terminals, and their apparent standards
- Any visible markings: logos, model numbers, standards marks, certification stamps,
  moulded-in text
- Scale cues — hands, desks, standard objects in frame

State what you read off the image and what you are inferring. Do not present a guess
about a dimension in the same voice as a number stamped on the housing.

## Step 1: Identify the thing

Work out what the category is actually called by people who sell it. This is the
single highest-value step, because consumer language and trade language diverge
sharply and the trade term is what unlocks the good catalogues.

Where the answer is genuinely uncertain, say so and give the two or three candidate
identifications rather than committing to one. A wrong canonical name poisons every
term downstream.

## Step 2: Separate essential from incidental

From the description and image, sort the attributes:

- **Essential** — if this is wrong, the thing does not work. Fit dimensions, thread
  pitch, voltage, load rating, protocol.
- **Incidental** — true of the example the user showed you, but not required.
  Colour, brand, the particular shape of the housing.

Ask the user to confirm the split before writing. Users routinely over-specify from
a photograph, and every incidental attribute you promote to essential is a whole
segment of the market you have just excluded.

## Step 3: Write `spec.md`

Vendor-neutral throughout. Describe capability and constraint, never a product.

- **What it has to do** — the function, in one or two sentences
- **Fit and interface constraints** — dimensions, threads, connectors, mounting,
  the things it must physically or electrically meet
- **Performance requirements** — load, throughput, capacity, rating, with units
- **Environment** — indoor/outdoor, temperature, moisture, vibration, who handles it
- **Essential attributes** — from Step 2
- **Explicitly not required** — the incidentals, listed so that later research does
  not silently reintroduce them as filters
- **Open questions** — what you could not determine and what would settle it

## Step 4: Write `search-terms.md`

This is the deliverable the user asked for. Organise terms into **registers**,
because register is what determines which half of the market a search reaches.

Produce a table of this shape:

| Term | Register | Skews toward | Best on | Noise to expect |
| --- | --- | --- | --- | --- |
| `<exact string to type>` | consumer / trade / technical / regional | what kind of product this pulls | which marketplaces | what junk comes back |

Cover these registers, omitting any that genuinely do not apply:

- **Canonical / trade name** — what the industry calls it. Usually the highest-yield
  term and usually not what the user said.
- **Consumer register** — how retail listings title it. Broader, noisier, cheaper
  goods, better availability data.
- **Industrial / trade register** — how B2B catalogues title it. Narrower, better
  specified, higher prices, real datasheets. This is where the terms that "target
  more industrial products" belong, and they should be labelled as such.
- **Technical / spec-code searches** — standards and codes searched directly:
  thread designations, DIN/ISO/ANSI numbers, IP ratings, connector families, tolerance
  classes. These cut through naming chaos entirely when they exist.
- **Regional and language variants** — including Hebrew for Israeli retailers and
  aggregators, and US/UK English splits where they change the noun outright.
- **Decoy terms** — terms that look correct and return the wrong thing. Say what
  each one actually returns and why it is a trap. This section saves more time than
  any of the others.

Annotate freely in prose beneath the table where a term needs more than a cell of
explanation. The annotations are as valuable as the terms — "this one will target
more industrial products" is exactly the kind of note to write.

Also emit **`search-terms.txt`**: the bare strings, one per line, no annotations,
grouped by register with a comment line per group. This is the copy-paste artefact
for pasting straight into a search box, so keep it free of markdown.

## Step 5: Save and hand off

1. Write `spec.md` and `search-terms.md` to the repo root, and `search-terms.txt`
   alongside them
2. Summarise in 4–6 lines: what you identified the thing as, the confidence, and the
   two or three terms you would start with
3. Prompt: "Spec and search vocabulary saved. Run `/procurement-tools:intake` to add
   budget, timeline and dealbreakers for this purchase, or `/procurement-tools:research`
   if you want me to start finding candidates with these terms now."

If a named marketplace is already in scope, note that the `marketplace-handoff` skill
may route the actual searching to a dedicated marketplace plugin.

## Interview style

- Lead with what you worked out, not with questions. The user came here because they
  could not name the thing; make the first move.
- Ask at most two rounds of clarification before writing a first draft. A draft the
  user corrects beats an interview they abandon.
- Use `AskUserQuestion` for the essential/incidental split — it is a natural
  multiple-choice.
- Where you are uncertain about the identification, generate terms for **both**
  candidate identifications rather than picking one and being confidently wrong.

## Example opening

```
From the photo: a threaded clamp body, roughly 60 mm jaw opening, cast zinc or
aluminium, with a 5/8"-27 male stud on top — that stud is the giveaway, it is the
standard microphone thread.

So this is almost certainly a **desk-edge microphone mount clamp**, sold in the trade
as a "mic riser clamp" or "table clamp with 5/8 thread".

Two things before I write the spec: how thick is the desk edge it has to clamp to,
and does the arm you are attaching have a 5/8" or 3/8" thread?
```
