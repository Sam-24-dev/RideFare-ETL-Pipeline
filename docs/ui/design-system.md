# RideFare Web Product Design System

## Direction

RideFare uses an `Editorial Andino` direction for the public app:

- Editorial rhythm instead of dashboard-template symmetry
- Warm stone background with copper and lagoon accents
- Strong type contrast between narrative headlines and analytical body copy
- Topographic texture and mobility-inspired separators as the visual anchor

## Brand Surfaces

- Browser identity uses an `RF` monogram designed for small-size legibility first
- Social previews reuse the same palette and editorial rhythm as the public app
- Screenshots for the portfolio README live under `docs/ui/screenshots/phase-6/`
- The product should look coherent across:
  - browser tab
  - shared-link preview
  - Vercel deployment cards
  - README visuals

## Typography

- Display: `Cormorant Garamond`
- Body and UI: `IBM Plex Sans`
- Numeric/data accents: `IBM Plex Mono`

## Color System

- `piedra`: primary background
- `obsidiana`: main text and dark surfaces
- `cobre`: highlight, CTA, key metric emphasis
- `laguna`: analytical accent and chart secondary
- `paramo`: tertiary support tone
- `borde`: low-contrast structural border

## Layout Principles

- Sticky top navigation with rounded shell
- Wide editorial headers followed by denser analytical sections
- Cards use large radius, soft borders, and atmospheric gradients
- Mobile layouts stack charts and rankings without horizontal overflow

## Data Visualization Rules

- Line and area charts for temporal stories
- Heatmaps for hourly intensity
- Horizontal bars for rankings and feature importance
- Scatter plots for price-context relationships
- Charts must always include explanatory text outside the graphic itself

## Motion

- Framer Motion only for meaningful page and section entrances
- Hover transitions should be color and opacity first, not scale-first
- Reduced-motion users must get a stable, non-animated equivalent

## Accessibility

- Visible focus states on all interactive controls
- Contrast target aligned with portfolio-grade accessibility
- Chart sections require supporting copy and not color-only meaning
- Empty states must explain which pipeline step generates the missing artifacts
