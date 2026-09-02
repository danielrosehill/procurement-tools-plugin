// Shared styling for every report this plugin produces.
//
// Copied next to the generated report rather than imported from the plugin, so
// that `typst compile` still works in the workspace years later on a machine
// that never had the plugin installed. A report that cannot be rebuilt is a
// screenshot, not a document.
//
//   #import "base.typ": *
//   #show: report.with(
//     title: "Laser measure",
//     kind: "Recommendation",
//     date: "2026-09-02",
//     meta: (("Spec", "spec.yaml rev 3"), ("Candidates", "7")),
//   )

#let accent = rgb("#1f4e79")
#let muted = luma(110)

// Verdict glyphs. Colour carries no information on its own — the word is always
// present — because these get printed in mono and read by people who do not
// distinguish red from green.
#let verdict(v) = {
  let v = lower(v)
  if v == "pass" { text(fill: rgb("#1a7f37"))[*pass*] }
  else if v == "fail" { text(fill: rgb("#b42318"))[*fail*] }
  else if v == "partial" { text(fill: rgb("#b54708"))[*part*] }
  else { text(fill: muted)[*unknown*] }
}

#let report(
  title: "",
  kind: "Report",
  date: "",
  subtitle: none,
  meta: (),
  footer-note: none,
  body,
) = {
  set document(title: title + " — " + kind)
  set page(
    paper: "a4",
    margin: (x: 2cm, y: 2.2cm),
    footer: context {
      set text(size: 8pt, fill: muted)
      grid(
        columns: (1fr, auto),
        align: (left, right),
        [#kind · #date#if footer-note != none [ · #footer-note]],
        [#counter(page).display("1 / 1", both: true)],
      )
    },
  )
  // Fallback chain rather than one hard-coded family: the first of these that
  // exists on the machine wins, so compilation does not fail on a box that
  // happens not to ship Libertine.
  set text(
    font: ("Libertinus Serif", "Linux Libertine", "DejaVu Serif", "Liberation Serif"),
    size: 10.5pt,
    lang: "en",
  )
  set par(justify: true, leading: 0.65em)
  show heading: set block(above: 1.4em, below: 0.7em)
  show heading.where(level: 1): set text(fill: accent, size: 17pt)
  show heading.where(level: 2): set text(fill: accent, size: 13pt)
  show link: set text(fill: accent)
  set table(stroke: 0.4pt + luma(190), inset: 7pt)
  show table.cell.where(y: 0): set text(weight: "bold")

  block[
    #text(size: 20pt, weight: "bold", fill: accent)[#title]
    #linebreak()
    #text(size: 12pt, fill: muted)[#kind#if subtitle != none [ — #subtitle]]
  ]
  v(0.2em)

  if meta.len() > 0 {
    set text(size: 9pt)
    grid(
      columns: (auto,) * calc.min(meta.len(), 4),
      column-gutter: 1.6em,
      row-gutter: 0.5em,
      ..meta.map(pair => [#text(fill: muted)[#pair.at(0)] #linebreak() *#pair.at(1)*]),
    )
    v(0.3em)
  }
  line(length: 100%, stroke: 0.6pt + accent)
  v(0.6em)
  body
}

// A conformance row set. `rows` is an array of (id, requirement, verdict, note).
// Requirement ids are printed verbatim so a claim can be traced back to the spec.
#let conformance-table(rows, candidate: none) = {
  if candidate != none [ === #candidate ]
  table(
    columns: (auto, 1fr, auto, 1.4fr),
    table.header([Id], [Requirement], [Verdict], [Evidence]),
    ..rows.map(r => (
      raw(r.at(0)),
      r.at(1),
      verdict(r.at(2)),
      text(size: 9pt)[#r.at(3)],
    )).flatten(),
  )
}

// Used where a report states something it could not verify. Being visually
// distinct is the point: an unknown that reads like a finding is the failure
// this whole artefact chain exists to prevent.
#let unknown-box(body) = block(
  fill: luma(246),
  stroke: (left: 2.5pt + muted),
  inset: 9pt,
  radius: 2pt,
  width: 100%,
  [#text(size: 9.5pt, fill: muted)[*Not verified* — #body]],
)

#let finding(body) = block(
  fill: rgb("#f2f7fb"),
  stroke: (left: 2.5pt + accent),
  inset: 9pt,
  radius: 2pt,
  width: 100%,
  body,
)
