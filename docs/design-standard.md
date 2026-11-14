# Jaxon design standard

Version 1.1 · Established November 14, 2026

This is the visual reference for future Jaxon design work. It captures the approved
direction of the landing page: warm, calm, simple, and clear. Use it when designing
new screens and when updating the application's existing components.

The current implementation is [jaxon.css](../everwealth/static/jaxon.css), with
the composition and copy in [index.html](../everwealth/templates/index.html).
The authenticated application uses the same brand values through a custom Jaxon
Tailwind/DaisyUI theme and shared component styles. The existing dark theme remains
available; the Jaxon palette defines the light theme.

## Design principles

- **Clarity first.** Make amounts, labels, and the next action easy to find.
- **Calm rather than urgency.** Use generous space, restrained color, and clear
  language. Financial information should feel approachable.
- **Warm and practical.** Pair an editorial serif with a familiar sans serif.
  Use product examples to explain the experience.
- **A small visual vocabulary.** Reuse surfaces, borders, radii, and controls.
  Let alignment and typography provide hierarchy before adding decoration.
- **Let the numbers lead.** In product screens, preserve readable, aligned data
  and explicit status labels as the marketing style is introduced.

## Brand identity and voice

Use **Jaxon** in prose, page titles, and accessible names. The visual wordmark is
lowercase **jaxon**, set in the body sans-serif at weight 700 with tight tracking.
The small supporting mark is **j.**, in Georgia on a deep teal rounded rectangle.
It is decorative when adjacent to the wordmark.

| Element | Current treatment |
| --- | --- |
| Header wordmark | 30px; weight 700; letter spacing −1.5px; 27px on mobile |
| Footer wordmark | 25px; weight 700; letter spacing −1.5px |
| Preview wordmark | 23px; weight 700; letter spacing −1px |
| Supporting mark | 32 × 36px; radius 7px; Georgia 29px; teal background and paper text |

Write short, direct, reassuring sentences. Prefer concrete actions such as
“Start your budget,” “Sign in,” and “See where you stand.” The existing brand
lines are “Your money. A clearer picture.” and “Make room for what matters.”
Avoid judgment about spending, exaggerated promises, and unsupported claims.
Label sample financial information as illustrative.

## Color palette

The standard is a **light theme** with a warm paper background. Deep teal anchors
text and actions; muted greens provide emphasis without competing with numbers.

### Core colors

| Role | Hex | Current CSS token | Usage |
| --- | --- | --- | --- |
| Paper | `#F8F7F2` | `--paper` | Page background; text on the supporting brand mark |
| Ink / deep teal | `#203C37` | `--ink` | Primary text, wordmark, primary button background |
| Muted text | `#626E66` | `--muted` | Supporting copy, metadata, captions |
| Border | `#DCDED4` | `--line` | Layout dividers and card borders |
| White | `#FFFFFF` | Literal | Preview card surface; primary button text |

### Supporting colors

These are existing literal values in the landing stylesheet. The role names
below describe their use; they are not additional implemented CSS variables.

| Role | Hex | Usage |
| --- | --- | --- |
| Action hover | `#34564E` | Primary button hover background |
| Balance highlight | `#DBE8B8` | Featured balance panel |
| Section tint | `#E9EDDF` | Closing call-to-action background |
| Pill tint | `#F0F3E9` | Small informational pill background |
| Subtle divider | `#E9EBE4` | Internal rules in the preview card |
| Meter track | `#EDF0E8` | Unfilled progress track |
| Meter fill | `#6C8D73` | Preview category progress |
| Focus | `#597D38` | Keyboard focus outline |
| Status dot | `#668046` | Small decorative dot beside the hero eyebrow |
| Decimal accent | `#587044` | Secondary digits in the featured balance |
| Decorative accent | `#6C8459` | Separators in the principles strip |
| Step label | `#56704A` | Numbered step labels |

Use paper for the canvas and white for contained information. Reserve the balance
highlight and section tint for selective emphasis. Borders should separate groups
quietly; avoid boxing every element.

The landing page does **not** establish error, warning, destructive-action, or
dark-theme colors. Preserve the application's existing semantic states until
those palettes are explicitly designed. Do not use a decorative green to imply
success, or replace a meaningful red state with a brand color. Always accompany
financial status colors with text or another non-color cue.

## Typography

Use local system fonts; the landing page requires no font downloads.

```css
/* Body, controls, labels, and financial information */
font-family: Arial, Helvetica, sans-serif;

/* Main editorial heading */
font-family: Georgia, 'Times New Roman', serif;

/* Supporting editorial headings */
font-family: Georgia, serif;
```

### Type scale

| Role | Desktop size | Weight | Line height | Letter spacing |
| --- | --- | --- | --- | --- |
| Hero heading | `clamp(48px, 5.2vw, 70px)` | 400 | 1.06 | −3px |
| Main section heading | 40px | 400 | 1.15 | −1.3px |
| Closing heading | 34px | 400 | 1.15 | −1.3px |
| Step heading | 25px | 400 | 1.25 | −0.5px |
| Principles strip | 22px | 400 | Inherited | Normal |
| Intro paragraph | 17px | 400 | 1.8 | Normal |
| Section paragraph | 16px | 400 | 1.8 | Normal |
| Step paragraph | 14px | 400 | 1.8 | Normal |
| Primary button | 14px | 600 | 1.2 | Normal |
| Navigation | 14px | 400 | Inherited | Normal |
| Eyebrow | 11px | 600 | 1.7 | 1.7px; uppercase |
| Supporting note | 12px | 400 | Inherited | Normal |

Editorial headings use Georgia; body copy, controls, and the preview card use
Arial. The preview's balance uses 42px text, weight 500, tracking −1.5px, and
`font-variant-numeric: tabular-nums`; its decimals use 25px. Secondary preview
totals use 19px, weight 500. Preview labels and captions range from 10–12px.

For future application screens, use the serif selectively for page introductions
and section headings. Keep dense tables, form controls, and transaction details in
the sans serif. Use tabular numerals and right alignment for comparable amounts.
The miniature preview's 10–11px labels are not a sizing standard for real financial
data: use 14–16px for primary application content and at least 12px for metadata.

## Layout and spacing

### Desktop composition

- Center content in a **1160px maximum width** container, with **40px side gutters**.
- The header has **27px vertical padding** and one bottom rule.
- The hero is a two-column grid: **1.1fr / 1fr**, an **80px gap**, and vertically
  centered content. Its padding is **88px top / 80px bottom**.
- Keep introductory body copy within **460px**, section descriptions within
  **510px**, and the section introduction within **620px**.
- The principles strip uses horizontal rules and **25px vertical padding**.
- The explanatory section has **90px vertical padding**. Its three steps have a
  **42px gap** and begin **48px** below the introduction.
- The closing panel uses **44px vertical / 48px horizontal padding**. The footer
  has **45px vertical padding**.

For new layouts, favor a 4px spacing rhythm: 4, 8, 12, 16, 24, 32, 48, and 64px.
This is guidance for new work, not a claim that every existing value uses that
scale. Preserve the landing page's intentional optical adjustments.

Use whitespace and simple rules to group content. Allow long descriptions to wrap
and give flex/grid children room to shrink. Do not rely on fixed page heights.

## Component treatments

| Component | Standard |
| --- | --- |
| Primary action | Deep teal fill, white text, 1px teal border, 6px radius, 52px minimum height, 16px × 24px padding |
| Header action | Same treatment; 42px minimum height, 12px × 18px padding |
| Secondary action | Text link with a subtle bottom border; avoid a competing filled button |
| Preview card | White surface, 1px border, 14px radius, 25px top / 28px sides / 18px bottom padding |
| Card shadow | `0 16px 40px #203C370A` — a restrained teal shadow |
| Featured balance | Pale green fill, 8px radius, 22px padding |
| Closing panel | Section tint, 10px radius, no heavy shadow |
| Informational pill | Pill tint, 20px radius, 7px × 10px padding; 10px text in the miniature preview |
| Progress meter | 5px high, 8px radius, light track and muted green fill |
| Step block | One top border, 24px top padding, numbered uppercase label |

Prefer these radii by role rather than applying the largest radius everywhere.
The preview card's **1-degree rotation** is a marketing illustration treatment,
removed on mobile. Keep real application cards, tables, and dialogs level.

Directional cues are small and subordinate to labels: `↗` for calls to action,
`↓` for the page anchor, and `✳` as a decorative separator. Mark decorative symbols
as hidden from assistive technology. In the app, retain its existing Lucide icons
and accompanying labels.

## Responsive behavior

Breakpoints use inclusive `max-width` queries. Smaller-breakpoint rules override
the preceding rules.

| Viewport | Behavior |
| --- | --- |
| Above 960px | Desktop composition; 40px side gutters |
| 960px and below | 24px gutters; hero gap 36px and vertical padding 60px; hero heading 53px; intro 15px; preview padding 22px; step gap 24px; closing padding 36px and heading 30px |
| 700px and below | 20px gutters; hero stacks with a 42px gap and 48px vertical padding; preview stays upright and at most 450px wide; steps become one column; closing content stacks |
| 380px and below | Hide the supporting `j.` mark; tighten navigation and action gaps |

At 700px and below, the hero heading becomes `clamp(42px, 11vw, 57px)`, the intro
becomes 16px, and the main section heading becomes 34px. The explanatory section
uses 55px vertical padding and 28px between steps. The closing panel uses 30px ×
24px padding with a 32px heading. The principles strip and footer may wrap.

On mobile, hide the secondary “How it works” navigation link while keeping sign-in
and sign-up visible; the hero's “Take a look” link still reaches that section.
The header wordmark becomes 27px, navigation 13px, and the compact action 12px
with 11px × 13px padding. Primary actions retain their larger treatment.

When applying the style to the app, keep amounts, category labels, and primary
actions available at narrow widths. Use deliberate horizontal scrolling for
timelines or dense tables rather than allowing the entire page to overflow.

## Interaction and accessibility

- Keep semantic headings, navigation labels, and a visible-on-focus skip link.
- The current link focus treatment is a **3px `#597D38` outline with a 5px offset**.
  Preserve an equally visible indicator on new interactive components.
- Hover darkens primary buttons to `#34564E`; hover is not the only indication
  that something is actionable.
- Smooth anchor scrolling runs only when `prefers-reduced-motion: no-preference`.
  New motion must also respect the visitor's preference.
- Give dialogs accessible names, keyboard operation, and explicit close controls.
- Keep financial states understandable without relying on color alone.
- Aim for at least 44px touch targets in new controls. The current compact header
  action is 42px high; do not copy that exception into every application control.
- Check contrast, keyboard navigation, text zoom, and narrow layouts during
  implementation. This record of current values is not an accessibility audit.

## Applying and maintaining the standard

Start future redesigns with the core palette, font pairing, restrained surfaces,
and spacing. Adapt the landing page's spacious composition to the task: a budget
table needs readable density, while a marketing introduction can be expansive.

Shared brand values live in `everwealth/static/styles/brand.css`; both the landing
stylesheet and the application build import them. The landing page retains its
`--paper`, `--ink`, `--muted`, and `--line` aliases. The application maps those roles
to DaisyUI theme colors. Keep business status colors separate from decorative
brand accents.

### Application implementation

| Source | Responsibility |
| --- | --- |
| `static/styles/brand.css` | Exact brand colors and font families shared with marketing |
| `static/styles/theme.css` | Jaxon light theme, existing dark theme, semantic status palette, radii |
| `static/styles/app.css` | App shell, heading hierarchy, panels, controls, tables, summaries, responsive behavior |
| `static/input.css` | Tailwind build entry point and template/source scanning |
| `templates/partials/ui.html` | Shared wordmark and page header markup |
| `templates/app.html` | Navigation, mobile drawer, skip link, and main content region |

Paths in this table are relative to `everwealth/`. Keep CSS rules grouped by
component in the source stylesheets. Use the existing utility classes for local
layout. Financial values use `.amount` for Arial and tabular numerals, rather
than a monospace font. Shared card headers use `.panel-header`.

The overall workspace is centered with a maximum width of 1280px, matching the
app's original width. It has a 224px desktop sidebar at 1024px and above and a mobile drawer
below that width. Desktop content has 40px padding; narrow layouts have 20px.
App page headings scale from 32px to 40px and section headings use 22px. The
monthly overview uses three cards on desktop, with a highlighted remaining
balance; at 700px and below the balance spans the full row beneath income and
spending. Financial gains and losses retain green/red semantics, with darker
status text on the Jaxon light background for readability.

Stored light-theme preferences migrate to `jaxon`; explicit dark preferences
are retained. Keyboard focus and reduced-motion behavior remain consistent
across partial navigation.

For each design change, check:

- Does it use the established palette and typography?
- Are the main information and action easy to identify?
- Do amounts align, labels wrap, and controls remain usable on mobile?
- Are focus, status, and reduced-motion behavior preserved?
- If it establishes a new reusable pattern, has this document been updated?

New semantic palettes, a dark theme, and additional component states should be
documented here when designed. Keep this document and the relevant stylesheets
in sync as the standard evolves.
