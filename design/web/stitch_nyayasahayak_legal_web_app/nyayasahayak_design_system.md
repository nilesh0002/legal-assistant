---
name: "NyayaSahayak — Civic Legal Reference System"
description: "A calm, credible, public-library design system for NyayaSahayak, an Indian legal information assistant grounded strictly in official government sources."
---

## Overview

NyayaSahayak is designed to feel like a well-organized public library or trusted civic reference desk—calm, authoritative, and accessible to everyone in India, from first-time internet users and older adults to students and legal professionals. It avoids flashy AI-chatbot tropes, courtroom clichés, and national emblems, focusing instead on clarity, generous breathing room, and verifiable source quotes.

The visual language pairs an off-white archival paper ground (`#F7F6F2`) and crisp white reading cards (`#FFFFFF`) with a deep navy primary (`#1B2A49`) and a restrained warm amber accent (`#E0A030`). A deliberate dark theme uses deep warm charcoal surfaces (`#15130E` / `#1D1C16`) to prevent halation during extended reading. Every status signal pairs semantic color with an icon and a clear text label.

## Colors

The palette anchors on **Deep Navy** (`#1B2A49`) for primary actions and civic authority, **Warm Paper** (`#F7F6F2`) for comfortable long-form reading, **Charcoal** (`#1E1E1E`) for high-contrast body text, and **Warm Amber** (`#E0A030`) used sparingly for subtle highlights and the Beta notice indicator.

- **Status Semantics:** Six distinct status roles—`answered` (teal-green), `clarification` (blue), `not-covered` (amber), `insufficient` (warm grey), `out-of-scope` (neutral grey), and `error` (red)—always paired with an icon and text label, never color alone.
- **Dark Mode:** Deep warm-neutral surfaces (`#15130E` background, `#1D1C16` cards) paired with soft periwinkle-navy (`#B7C6ED`) primary actions and warm off-white text (`#E7E2D8`).

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
    surface-container-lowest: "#FFFFFF"
    surface-container-low: "#F9F3E9"
    surface-container: "#F1EFE9"
    surface-container-high: "#E7E4DC"
    on-surface-variant: "#49473F"
    outline: "#75777E"
    outline-variant: "#D4D1C7"
    answered: "#006B5C"
    on-answered: "#FFFFFF"
    answered-container: "#E0F5F0"
    on-answered-container: "#00382F"
    clarification: "#1D5FA8"
    on-clarification: "#FFFFFF"
    clarification-container: "#EBF1FF"
    on-clarification-container: "#00315F"
    not-covered: "#8D4F00"
    on-not-covered: "#FFFFFF"
    not-covered-container: "#FFEEE1"
    on-not-covered-container: "#4B2700"
    insufficient: "#615E56"
    on-insufficient: "#FFFFFF"
    insufficient-container: "#EFECE4"
    on-insufficient-container: "#32302A"
    out-of-scope: "#45464E"
    on-out-of-scope: "#FFFFFF"
    out-of-scope-container: "#EAEBF0"
    on-out-of-scope-container: "#2E3037"
    error: "#B4271F"
    on-error: "#FFFFFF"
    error-container: "#FFEDEA"
    on-error-container: "#690003"
  dark:
    primary: "#B7C6ED"
    on-primary: "#1B2A49"
    primary-container: "#21304F"
    on-primary-container: "#D9E2FF"
    secondary: "#FEBA49"
    on-secondary: "#442C00"
    secondary-container: "#442C00"
    on-secondary-container: "#FFEEDB"
    background: "#15130E"
    on-background: "#E7E2D8"
    surface: "#15130E"
    on-surface: "#E7E2D8"
    surface-container-lowest: "#0F0E09"
    surface-container-low: "#1D1C16"
    surface-container: "#24221B"
    surface-container-high: "#2E2C24"
    on-surface-variant: "#C5C6CF"
    outline: "#8F9098"
    outline-variant: "#45464E"
    answered: "#58DBC3"
    on-answered: "#00382F"
    answered-container: "#005045"
    on-answered-container: "#B6FFEE"
    clarification: "#A6C8FF"
    on-clarification: "#00315F"
    clarification-container: "#004787"
    on-clarification-container: "#EBF1FF"
    not-covered: "#FFB876"
    on-not-covered: "#4B2700"
    not-covered-container: "#6B3B00"
    on-not-covered-container: "#FFEEE1"
    insufficient: "#CBC6BC"
    on-insufficient: "#32302A"
    insufficient-container: "#49473F"
    on-insufficient-container: "#F6F0E6"
    out-of-scope: "#C5C6CF"
    on-out-of-scope: "#2E3037"
    out-of-scope-container: "#45464E"
    on-out-of-scope-container: "#F0F0F9"
    error: "#FFB4AA"
    on-error: "#690003"
    error-container: "#910809"
    on-error-container: "#FFEDEA"
```

## Typography

**Noto Sans** is used across the interface for clean legibility and seamless future support for **Noto Sans Devanagari**. **Noto Serif** is reserved exclusively for verbatim statutory and constitutional quotes so users can immediately distinguish official legal text from plain-language explanation. **Source Code Pro** is used for section numbers, dates, and technical identifiers when tabular precision is needed.

Body text is at least `16px` (`body-md`) with comfortable `1.5` line-height and a ~70-character maximum measure (`max-w-prose`) to survive 200% browser zoom cleanly.

```yaml
typography:
  display-lg:
    fontFamily: "Noto Sans"
    fontSize: 40px
    fontWeight: 700
    lineHeight: 48px
    letterSpacing: -0.5px
  display-lg-mobile:
    fontFamily: "Noto Sans"
    fontSize: 28px
    fontWeight: 700
    lineHeight: 36px
    letterSpacing: -0.25px
  headline-lg:
    fontFamily: "Noto Sans"
    fontSize: 28px
    fontWeight: 700
    lineHeight: 36px
    letterSpacing: -0.25px
  headline-md:
    fontFamily: "Noto Sans"
    fontSize: 22px
    fontWeight: 600
    lineHeight: 30px
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
    letterSpacing: 0px
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
    letterSpacing: 0px
  body-sm:
    fontFamily: "Noto Sans"
    fontSize: 14px
    fontWeight: 400
    lineHeight: 20px
    letterSpacing: 0px
  label-lg:
    fontFamily: "Noto Sans"
    fontSize: 15px
    fontWeight: 600
    lineHeight: 20px
    letterSpacing: 0px
  label-md:
    fontFamily: "Noto Sans"
    fontSize: 13px
    fontWeight: 600
    lineHeight: 18px
    letterSpacing: 0.1px
  label-sm:
    fontFamily: "Noto Sans"
    fontSize: 12px
    fontWeight: 500
    lineHeight: 16px
    letterSpacing: 0.2px
  statute-quote:
    fontFamily: "Noto Serif"
    fontSize: 17px
    fontWeight: 400
    lineHeight: 28px
    letterSpacing: 0px
  mono-sm:
    fontFamily: "Source Code Pro"
    fontSize: 13px
    fontWeight: 500
    lineHeight: 18px
    letterSpacing: 0px
```

## Layout & Spacing

Mobile-first layout (`390px`), scaling cleanly to tablet (`768px`) and desktop (`1280px`).
- **Desktop (`1280px`):** Slim sticky top bar (brand mark + name, navigation links: Ask, History, Coverage, About, theme toggle, language indicator "English | Hindi soon"), persistent Beta strip directly beneath, and a centered content column up to `760px` wide for reading. On the Answer screen, desktop expands to a 2-column layout with the short answer on the left (up to `760px`) and a sticky right-hand **Sources** panel (`380px`–`420px`) holding verbatim quotes and official links.
- **Tablet (`768px`):** Top bar with full nav links, centered `760px` max-width reading column, and collapsible/stacked sources beneath the answer.
- **Mobile (`390px`):** Compact top bar with menu button, persistent Beta strip, single-column content, and sticky bottom search/ask input bar where appropriate. All interactive targets are at least `44px` × `44px`.

```yaml
spacing:
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  2xl: 48px
```

## Elevation & Depth

Hierarchy is established primarily through **tonal surface steps** and **subtle 1px outlines** (`outline-variant`) rather than heavy drop shadows. White cards (`surface-container-lowest`) sit cleanly on the warm off-white page ground (`surface`), with crisp `1px` borders and visible `2px` focus rings (`primary`) for keyboard accessibility. Modals and sticky drawers use a soft, low-opacity ambient shadow paired with a scrimmed backdrop.

## Shapes

Generous, approachable geometry: `16px` (`lg`) corners on primary cards and modals, `24px` (`xl`) pill-like corners on example question chips and status badges, and `12px` (`md`) on buttons and form inputs.

```yaml
rounded:
  sm: 6px
  DEFAULT: 12px
  md: 12px
  lg: 16px
  xl: 24px
  full: 9999px
```

## Motion & Micro-interaction

Motion is calm, crisp, and restrained. Interactive hover and focus transitions land in `120ms`, while expandable source drawers and modal overlays settle in `220ms` with a gentle deceleration curve. No decorative loops or bouncing animations; honours `prefers-reduced-motion`.

```yaml
motion:
  state-change:
    duration: 120ms
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

- **Tone of voice:** Calm, plain-spoken, honest, and respectful. Never patronizing, never sensational, and never pretending to be a lawyer or a sentient AI.
- **Capitalisation:** Sentence case for headings, buttons, status labels, and navigation items.
- **Status honesty:** When the system cannot answer, it says so plainly ("This topic isn't covered yet", "Not enough information in official sources") and offers concrete next steps rather than guessing.
- **Button labels:** Clear action verbs ("Ask a question", "Show details and sources", "Open official source", "See what is covered", "Try again", "I understand").
- **Dates & citations:** Standard Indian/ISO readable dates (`Last verified: 14 Nov 2026`), exact section/article numbers, and "Earlier law: CrPC Section ..." tags where BNS/BNSS/BSA replaced older codes.

## Components

Component implementations live as individual HTML sticker sheet files in
`components/`. Each file contains the canonical, styled HTML components with
`<!-- COMPONENT: name -->` comment markers. Read each file before use.

- **Badge** → `@components/badge.html` — `badge-numeric`, `badge-dot`
- **Button** → `@components/button.html` — `button-primary`, `button-icon`, `button-with-icon`
- **Card** → `@components/card.html` — `card-elevated`, `card-action`, `card-interactive`, `card-interactive-2`
- **Chip** → `@components/chip.html` — `chip-action`, `chip-input`, `chip-with-icon`
- **Searchbar** → `@components/searchbar.html` — `searchbar-standard`, `searchbar-with-suggestions`
