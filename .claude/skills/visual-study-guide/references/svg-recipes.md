# SVG recipes for guide figures

Every figure is hand-authored inline SVG using only `rect`, `polygon`, `line`, `path`, `text` and `marker`. No libraries, no images, no `<style>` or `<script>` inside the SVG. The page CSS already styles the classes below, so a figure is only coordinates and labels.

## The wrapper

```html
<figure>
  <div class="fig-scroll">
  <svg viewBox="0 0 W H" role="img" aria-label="One or two sentences stating what the picture shows.">
    <defs>
      <marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="currentColor"/></marker>
      <marker id="arr-go" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" style="fill:var(--go)"/></marker>
      <marker id="arr-done" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" style="fill:var(--done)"/></marker>
      <marker id="arr-muted" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" style="fill:var(--muted)"/></marker>
      <marker id="arr-accent" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" style="fill:var(--accent)"/></marker>
    </defs>
    ...
  </svg>
  </div>
  <div class="legend"> ... only when an encoding repeats ... </div>
  <figcaption>The claim the picture makes, in one or two sentences.</figcaption>
</figure>
```

Marker ids must be unique per page. If a page has two figures that both need arrows, either share one `<defs>` in the first figure (ids are document-wide) or suffix the ids (`arr2`, `arr2-go`).

Pick `W` for the content: 980 to 1100 for a wide flow, and `H` for the rows you draw. The CSS scales the drawing to the column width and lets it scroll horizontally on phones, so never squeeze a figure to fit a small viewBox.

## Classes

| Class | Use for |
|---|---|
| `box` | a neutral node (surface fill, ink stroke) |
| `box-accent` | the decision, the signal, the thing appended this iteration |
| `box-go` | the continue path, the request, work in progress (amber) |
| `box-done` | the finished or returned result (green) |
| `box-muted` | guards, fall-through, "other" (add `stroke-dasharray="5 4"` for a guard) |
| `tag` | a small label chip inside a box, e.g. a role name |
| `edge`, `edge-go`, `edge-done`, `edge-muted`, `edge-accent`-style via `style="stroke:var(--accent)"` | arrows, matched to the marker of the same colour |
| `text` (no class) | 12px sans label |
| `text.mono` | 11px monospace for code-ish labels (field names, calls) |
| `text.tiny` | 10.5px sans for sub-labels |
| `t-go`, `t-done`, `t-muted`, `t-accent` | text colour matching the path it labels |

## The width formula (this is the rule that keeps text inside boxes)

Estimate each label's width, then size the box from the longest label:

| Label class | px per character | Example |
|---|---|---|
| sans 12px (no class) | 7.0 | "run the matching function" = 25 chars = 175px |
| `mono` 11px | 6.9 | "TOOL_IMPLEMENTATIONS[name]" = 26 chars = 180px |
| `tiny` 10.5px | 6.1 | "safety net, never primary control" = 33 chars = 202px |

```
box width  = longest label px + 24
box height = 48 for two lines (baselines at y+20 and y+37), 64 for three (y+22, y+37, y+56)
text x     = box x + width / 2, with text-anchor="middle"
```

Labels are a word or three. If a label needs more than 30 characters, split it into two lines or move the sentence to the caption. The checker (`scripts/check_guide.py`) applies this same estimate and fails the build when a label would escape its box, so size generously and let the checker confirm.

Left-aligned text inside a box (like the message snapshots) starts at `box x + 82` when a 66px tag chip sits at the left, and the usable width is `box width - 86`.

## Layout grid

Keep everything on a grid so the drawing reads as deliberate:

- Main flow on one centre line (`y=200` in a 360-high figure), boxes centred on it.
- Row above for the return path (`y=62` to `110`), row below for guards and fall-through (`y=290` to `342`).
- 34 to 44px of gap between boxes on the same row so an arrow with its head fits.
- Arrows start at a box edge and end 6px short of the next edge (the marker is drawn at the line end).

## Pattern A: linear flow with a decision and a return loop

Used for any lifecycle or loop. Coordinates from the agentic-loops figure, viewBox `0 0 1030 360`.

```html
<!-- main row -->
<rect class="box" x="16" y="176" width="112" height="48" rx="6"/>
<text x="72" y="205" text-anchor="middle">Input</text>
<line class="edge" x1="128" y1="200" x2="162" y2="200" marker-end="url(#arr)"/>

<rect class="box" x="168" y="176" width="140" height="48" rx="6"/>
<text class="mono" x="238" y="196" text-anchor="middle">state[]</text>
<text class="tiny t-muted" x="238" y="213" text-anchor="middle">what accumulates</text>
<line class="edge" x1="308" y1="200" x2="352" y2="200" marker-end="url(#arr)"/>

<rect class="box" x="358" y="168" width="210" height="64" rx="6"/>
<text class="mono" x="463" y="190" text-anchor="middle">the_call(</text>
<text class="mono" x="463" y="205" text-anchor="middle">args)</text>
<text class="tiny t-muted" x="463" y="224" text-anchor="middle">one call per iteration</text>
<line class="edge" x1="568" y1="200" x2="582" y2="200" marker-end="url(#arr)"/>

<!-- decision diamond, centre (668,200), half-width 80, half-height 50 -->
<polygon class="box-accent" points="668,150 748,200 668,250 588,200"/>
<text class="mono t-accent" x="668" y="197" text-anchor="middle" font-weight="500">signal</text>
<text class="t-accent" x="668" y="214" text-anchor="middle">?</text>

<!-- exit right: finished -->
<line class="edge-done" x1="748" y1="200" x2="792" y2="200" marker-end="url(#arr-done)"/>
<text class="mono t-done" x="770" y="190" text-anchor="middle">done</text>
<rect class="box-done" x="798" y="176" width="216" height="48" rx="6"/>
<text x="906" y="196" text-anchor="middle">return the result</text>

<!-- exit up and back around: continue -->
<line class="edge-go" x1="668" y1="150" x2="668" y2="116" marker-end="url(#arr-go)"/>
<text class="mono t-go" x="678" y="136">continue</text>
<rect class="box-go" x="578" y="62" width="180" height="48" rx="6"/>
<text x="668" y="82" text-anchor="middle">step one</text>
<line class="edge-go" x1="578" y1="86" x2="546" y2="86" marker-end="url(#arr-go)"/>
<rect class="box-go" x="340" y="62" width="200" height="48" rx="6"/>
<text x="440" y="82" text-anchor="middle">step two</text>
<line class="edge-go" x1="340" y1="86" x2="312" y2="86" marker-end="url(#arr-go)"/>
<rect class="box-go" x="90" y="62" width="216" height="48" rx="6"/>
<text x="198" y="82" text-anchor="middle">step three: append</text>
<path class="edge-go" d="M198 110 V143 H238 V170" marker-end="url(#arr-go)"/>
<text class="tiny t-go" x="250" y="152">next iteration</text>

<!-- exit down: anything else -->
<line class="edge-muted" x1="668" y1="250" x2="668" y2="284" marker-end="url(#arr-muted)"/>
<text class="tiny t-muted" x="678" y="272">anything else</text>
<rect class="box-muted" x="550" y="290" width="236" height="52" rx="6"/>
<text x="668" y="310" text-anchor="middle">log a warning, stop</text>

<!-- a guard on an edge: dashed box below, dashed path up to the edge -->
<rect class="box-muted" x="150" y="290" width="240" height="52" rx="6" stroke-dasharray="5 4"/>
<text x="270" y="308" text-anchor="middle">guard</text>
<path class="edge-muted" d="M270 290 V262 H333 V210" marker-end="url(#arr-muted)"/>
```

## Pattern B: stacked snapshots with brackets (state over time)

Used to show a list or context growing, or what each party holds. Columns of 320px, blocks 44px high with a 52px stride, a 66px `tag` chip at the left of each block, content text at `x + 82`. A bracket on the right edge joins two related blocks:

```html
<text class="mono t-muted" x="16" y="20">after step 1 · 3 items</text>

<rect class="box-accent" x="16" y="88" width="320" height="44" rx="5"/>
<rect class="tag" x="22" y="102" width="66" height="16" rx="3"/>
<text class="tiny" x="55" y="114" text-anchor="middle">assistant</text>
<text class="mono" x="98" y="106">first line, up to 34 chars</text>
<text class="mono t-go" x="98" y="121">second line, coloured</text>

<rect class="box-accent" x="16" y="140" width="320" height="44" rx="5"/>
...
<!-- bracket from the block above (y=121) to the block below (y=158), on the right edge x=336 -->
<path class="edge-go" d="M336 121 C 352 121, 352 158, 336 158"/>
```

Use `box-accent` on the blocks added in that snapshot and `box` on the ones carried over, and say so in the legend.

## Pattern C: hub-and-spoke (coordinator and subagents)

viewBox `0 0 900 420`. Hub in the centre, spokes on a circle. Every edge touches the hub; there are no spoke-to-spoke edges, and if the concept forbids them draw one as a dashed muted line with a cross and label it "never".

```html
<!-- hub -->
<rect class="box-accent" x="350" y="180" width="200" height="60" rx="8"/>
<text x="450" y="205" text-anchor="middle" font-weight="500">Coordinator</text>
<text class="tiny t-muted" x="450" y="222" text-anchor="middle">decomposes · routes · aggregates</text>

<!-- spokes: four boxes at the compass points -->
<rect class="box" x="350" y="30" width="200" height="48" rx="6"/>
<text x="450" y="50" text-anchor="middle">Search subagent</text>
<text class="tiny t-muted" x="450" y="67" text-anchor="middle">fresh context each call</text>
<line class="edge-go" x1="430" y1="180" x2="430" y2="84" marker-end="url(#arr-go)"/>
<text class="tiny t-go" x="380" y="135" text-anchor="end">prompt + context</text>
<line class="edge-done" x1="470" y1="78" x2="470" y2="174" marker-end="url(#arr-done)"/>
<text class="tiny t-done" x="520" y="135">result</text>

<!-- left spoke -->
<rect class="box" x="40" y="186" width="200" height="48" rx="6"/>
<line class="edge-go" x1="350" y1="200" x2="246" y2="200" marker-end="url(#arr-go)"/>
<line class="edge-done" x1="240" y1="220" x2="344" y2="220" marker-end="url(#arr-done)"/>

<!-- the forbidden edge -->
<line class="edge-muted" x1="240" y1="54" x2="350" y2="54" marker-end="url(#arr-muted)"/>
<text class="tiny t-muted" x="295" y="46" text-anchor="middle">never</text>
```

Add the right and bottom spokes the same way. Label each pair of edges with what travels: "prompt + only the context it needs" outward, "result" inward.

## Pattern D: swimlane sequence (who does what, in order)

viewBox `0 0 1000 H`. One column per party with a header box and a vertical lifeline; time runs downward; each message is a horizontal arrow with its label above it. Use it for invocation and hand-off topics.

```html
<!-- lanes -->
<rect class="box" x="40" y="16" width="180" height="40" rx="6"/>
<text x="130" y="41" text-anchor="middle" font-weight="500">Coordinator</text>
<line class="edge-muted" x1="130" y1="56" x2="130" y2="380"/>

<rect class="box" x="410" y="16" width="180" height="40" rx="6"/>
<text x="500" y="41" text-anchor="middle" font-weight="500">Subagent A</text>
<line class="edge-muted" x1="500" y1="56" x2="500" y2="380"/>

<!-- message 1: left to right -->
<line class="edge-go" x1="130" y1="100" x2="494" y2="100" marker-end="url(#arr-go)"/>
<text class="mono t-go" x="312" y="92" text-anchor="middle">invoke(prompt, context)</text>

<!-- activation bar on the receiver -->
<rect class="box-go" x="494" y="100" width="12" height="60" rx="2"/>

<!-- message 2: right to left -->
<line class="edge-done" x1="500" y1="160" x2="136" y2="160" marker-end="url(#arr-done)"/>
<text class="mono t-done" x="318" y="152" text-anchor="middle">result</text>
```

Space messages 60px apart. Put the parsed or extracted field (what the receiver actually got) in a `tiny t-muted` line under the arrow label when the topic is about context passing.

## Pattern E: side-by-side comparison

Two half-width drawings in one SVG, a vertical `edge-muted` divider between them, each half titled with a `mono t-muted` label at `y=20`. Draw the same system twice and make the difference the only thing that changes: an extra guard box, a removed edge, a different colour on one arrow. The reader should be able to point at what they are choosing between.

## Checks before you move on

- Every `text` inside a box passes the width formula (the checker enforces this).
- Every arrow has a marker and, where meaning matters, a label with a verb.
- Colours are used only for their meaning: amber continue or request, green finished or result, blue the decision or the newly added thing, muted guards and fall-through.
- The `aria-label` and the `figcaption` both state the claim, not the title.
