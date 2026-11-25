---
name: "NyayaSahayak — Civic Legal Aid"
description: "A calm, credible, Material 3 civic design system for explaining Indian law in plain language strictly from official government sources."
---

## Overview

NyayaSahayak is designed to feel like a well-organized public library or a thoughtful civic service: calm, credible, and immediately legible for first-time smartphone users, older adults, students, and legal professionals across India. The visual language avoids courtroom clichés, national emblems, and flashy "AI chatbot" tropes. Instead, it anchors trust in generous whitespace, warm paper-like surfaces, crisp deep-navy typography, and a dedicated serif voice for verbatim statutory text.

- **Brand Personality:** Calm, transparent, civic-minded, and plain-spoken.
- **Design Style:** Material 3 (Android portrait) with tonal surface layering, large touch targets (minimum `48px` height), `16px` cards, `24px` pill chips, and strict WCAG AA contrast.

## Colors

The palette pairs an off-white paper ground (`#F7F6F2`) and crisp white cards (`#FFFFFF`) with a deep navy primary (`#1B2A49`) and charcoal ink (`#1E1E1E`). A warm amber accent (`#E0A030`) is used sparingly for subtle highlights (such as Beta indicators or active emphasis), never as a large background fill behind white text.

- **Primary (`#1B2A49`):** Deep civic navy for primary actions, headers, and key navigation emphasis.
- **Accent (`#E0A030`):** Warm amber used sparingly for Beta tags and subtle library-bookmark highlights.
- **Status Colors:** Every status (Answered, Needs clarification, Not covered yet, Not enough information, Out of scope, Error) pairs its semantic color with a distinct Material Symbol icon and an explicit text label—color is never the sole indicator.
- **Dark Mode:** Uses deep warm charcoal surfaces (`#14130F` ground, `#1C1C17` cards) rather than pure black to prevent halation, with soft periwinkle-navy (`#B7C6ED`) primary actions.

```yaml
colors:
  accent: "#E0A030"
  light:
    primary: "#1B2A49"
    on-primary: "#FFFFFF"
    primary-container: "#D9E2FF"
    on-primary-container: "#0A1B39"
    secondary: "#805600"
    on-secondary: "#FFFFFF"
    secondary-container: "#FFEEDB"
    on-secondary-container: "#442C00"
    background: "#F7F6F2"
    on-background: "#1E1E1E"
    surface: "#F7F6F2"
    on-surface: "#1E1E1E"
    surface-dim: "#E6E2DB"
    surface-container-lowest: "#FFFFFF"
    surface-container-low: "#F1EFEA"
    surface-container: "#ECE9E2"
    surface-container-high: "#E6E2DB"
    on-surface-variant: "#45464E"
    outline: "#75777E"
    outline-variant: "#D4D1C9"
    answered: "#006A63"
    on-answered: "#FFFFFF"
    answered-container: "#E0F4F1"
    on-answered-container: "#00201D"
    clarification: "#2151DA"
    on-clarification: "#FFFFFF"
    clarification-container: "#DCE1FF"
    on-clarification-container: "#001551"
    not-covered: "#805600"
    on-not-covered: "#FFFFFF"
    not-covered-container: "#FFEEDB"
    on-not-covered-container: "#442C00"
    insufficient: "#635D58"
    on-insufficient: "#FFFFFF"
    insufficient-container: "#EAE1DA"
    on-insufficient-container: "#1F1B17"
    out-of-scope: "#5E5E67"
    on-out-of-scope: "#FFFFFF"
    out-of-scope-container: "#E3E1EC"
    on-out-of-scope-container: "#1A1B23"
    error: "#BA1A1A"
    on-error: "#FFFFFF"
    error-container: "#FFDAD5"
    on-error-container: "#410002"
  dark:
    primary: "#B7C6ED"
    on-primary: "#0A1B39"
    primary-container: "#21304F"
    on-primary-container: "#D9E2FF"
    secondary: "#FEBA49"
    on-secondary: "#442C00"
    secondary-container: "#614000"
    on-secondary-container: "#FFDDB0"
    background: "#14130F"
    on-background: "#E6E2DB"
    surface: "#14130F"
    on-surface: "#E6E2DB"
    surface-dim: "#0F0E0A"
    surface-container-lowest: "#1C1C17"
    surface-container-low: "#22211C"
    surface-container: "#282722"
    surface-container-high: "#31302C"
    on-surface-variant: "#C5C6CF"
    outline: "#8F9098"
    outline-variant: "#45464E"
    answered: "#51DBCE"
    on-answered: "#003733"
    answered-container: "#00504A"
    on-answered-container: "#9CF2E8"
    clarification: "#B7C4FF"
    on-clarification: "#002682"
    clarification-container: "#0039B5"
    on-clarification-container: "#DCE1FF"
    not-covered: "#FEBA49"
    on-not-covered: "#442C00"
    not-covered-container: "#614000"
    on-not-covered-container: "#FFDDB0"
    insufficient: "#CDC5BF"
    on-insufficient: "#34302B"
    insufficient-container: "#4B4641"
    on-insufficient-container: "#EAE1DA"
    out-of-scope: "#C7C5D0"
    on-out-of-scope: "#2F3038"
    out-of-scope-container: "#46464F"
    on-out-of-scope-container: "#E3E1EC"
    error: "#FFB4AB"
    on-error: "#690004"
    error-container: "#930009"
    on-error-container: "#FFDAD5"
```

## Typography

UI copy uses **Noto Sans** (paired with **Noto Sans Devanagari** readiness for future Hindi support), chosen for its open apertures, high legibility at small and 200% zoomed sizes, and calm civic neutrality. Quoted statutory text uses **Noto Serif** to visually distinguish official verbatim law from plain-language explanations. Minimum body copy is `16px` (`16sp` equivalent), with generous line heights (`1.5`–`1.6`) to accommodate both Latin and future Devanagari ascenders/matras.

```yaml
typography:
  display-lg:
    fontFamily: "Noto Sans"
    fontSize: 36px
    fontWeight: 700
    lineHeight: 44px
    letterSpacing: -0.5px
  display-lg-mobile:
    fontFamily: "Noto Sans"
    fontSize: 28px
    fontWeight: 700
    lineHeight: 36px
    letterSpacing: -0.25px
  headline-lg:
    fontFamily: "Noto Sans"
    fontSize: 24px
    fontWeight: 700
    lineHeight: 32px
    letterSpacing: -0.25px
  headline-md:
    fontFamily: "Noto Sans"
    fontSize: 20px
    fontWeight: 600
    lineHeight: 28px
    letterSpacing: 0px
  title-lg:
    fontFamily: "Noto Sans"
    fontSize: 18px
    fontWeight: 600
    lineHeight: 26px
    letterSpacing: 0px
  title-md:
    fontFamily: "Noto Sans"
    fontSize: 16px
    fontWeight: 600
    lineHeight: 24px
    letterSpacing: 0.1px
  body-lg:
    fontFamily: "Noto Sans"
    fontSize: 18px
    fontWeight: 400
    lineHeight: 28px
    letterSpacing: 0px
  body-md:
    fontFamily: "Noto Sans"
    fontSize: 16px
    fontWeight: 400
    lineHeight: 24px
    letterSpacing: 0.1px
  statute-lg:
    fontFamily: "Noto Serif"
    fontSize: 18px
    fontWeight: 400
    lineHeight: 30px
    letterSpacing: 0px
  statute-md:
    fontFamily: "Noto Serif"
    fontSize: 16px
    fontWeight: 400
    lineHeight: 26px
    letterSpacing: 0px
  label-lg:
    fontFamily: "Noto Sans"
    fontSize: 15px
    fontWeight: 600
    lineHeight: 20px
    letterSpacing: 0.1px
  label-md:
    fontFamily: "Noto Sans"
    fontSize: 13px
    fontWeight: 500
    lineHeight: 18px
    letterSpacing: 0.2px
```

## Layout & Spacing

Mobile-first Android portrait layout (`390px` viewport) with a single-column fluid grid, `16px` horizontal page margins, and generous vertical rhythm (`16px`–`24px` between sections). All interactive elements—buttons, chips, list rows, and bottom navigation items—enforce a minimum `48px` tap target height so older adults and first-time smartphone users can tap comfortably without precision strain. Layouts expand cleanly without clipping at 200% font size.

```yaml
spacing:
  gutter-xs: 4px
  gutter-sm: 8px
  gutter-md: 12px
  gutter-lg: 16px
  gutter-xl: 24px
  section: 32px
  page-margin: 16px
```

## Elevation & Depth

NyayaSahayak uses **tonal surface layering** and subtle `1px` `outline-variant` borders rather than heavy drop shadows. White cards (`surface-container-lowest`) sit cleanly on the warm off-white ground (`surface`), while nested quote blocks use `surface-container-low` with a crisp `4px` left border in `primary` (or `answered`) to anchor official statute text.

## Shapes

Generous, friendly Material 3 corner radii: `16px` (`lg`) for cards, banners, and modal sheets; `24px` (`xl`) for tappable question chips and segmented controls; `12px` (`md`) for search inputs and option cards; and `full` pills for status badges.

```yaml
rounded:
  sm: 8px
  DEFAULT: 12px
  md: 12px
  lg: 16px
  xl: 24px
  full: 9999px
```

## Motion & Micro-interaction

Motion is calm, deliberate, and understated. Interactive taps respond within `100ms`, while expanding source details or opening bottom sheets decelerate smoothly over `220ms`. Respects `prefers-reduced-motion`; no bouncing, pulsing, or decorative loops.

```yaml
motion:
  state-change:
    duration: 100ms
    delay: 0ms
    timingFunction: ease-out
  surface-enter:
    duration: 220ms
    delay: 0ms
    timingFunction: cubic-bezier(0.2, 0, 0, 1)
  surface-exit:
    duration: 150ms
    delay: 0ms
    timingFunction: cubic-bezier(0.3, 0, 1, 1)
```

## Voice & Content Strategy

- **Tone:** Calm, respectful, plain-spoken, and transparent. Never legalistic in the summary; always verbatim in the source quote.
- **Capitalisation:** Sentence case across all headings, buttons, chips, and navigation labels.
- **Action Labels:** Clear, outcome-oriented phrases (`I understand`, `Show details and sources`, `Open official source`, `Try again`, `What is covered`).
- **Disclaimers & Statuses:** Never hide uncertainty. Every answer carries `General information, not legal advice`. When the app cannot answer, it states why plainly without guessing.
- **Dates:** Consistent `DD MMM YYYY` format (e.g., `15 Oct 2026`).

## Components

Component implementations live as individual HTML sticker sheet files in
`components/`. Each file contains the canonical, styled HTML components with
`<!-- COMPONENT: name -->` comment markers. Read each file before use.

- **Button** → `@components/button.html` — `button-primary`, `button-icon`, `button-with-icon`
- **Card** → `@components/card.html` — `card-elevated`, `card-action`, `card-interactive`, `card-interactive-2`
- **Chip** → `@components/chip.html` — `chip-action`, `chip-input`, `chip-with-icon`
- **Searchbar** → `@components/searchbar.html` — `searchbar-standard`, `searchbar-with-suggestions`
