---
name: Academic Intelligence
colors:
  surface: '#f8f9ff'
  surface-dim: '#cbdbf5'
  surface-bright: '#f8f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#eff4ff'
  surface-container: '#e5eeff'
  surface-container-high: '#dce9ff'
  surface-container-highest: '#d3e4fe'
  on-surface: '#0b1c30'
  on-surface-variant: '#464555'
  inverse-surface: '#213145'
  inverse-on-surface: '#eaf1ff'
  outline: '#777587'
  outline-variant: '#c7c4d8'
  surface-tint: '#4d44e3'
  primary: '#3525cd'
  on-primary: '#ffffff'
  primary-container: '#4f46e5'
  on-primary-container: '#dad7ff'
  inverse-primary: '#c3c0ff'
  secondary: '#006c49'
  on-secondary: '#ffffff'
  secondary-container: '#6cf8bb'
  on-secondary-container: '#00714d'
  tertiary: '#684000'
  on-tertiary: '#ffffff'
  tertiary-container: '#885500'
  on-tertiary-container: '#ffd4a4'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#e2dfff'
  primary-fixed-dim: '#c3c0ff'
  on-primary-fixed: '#0f0069'
  on-primary-fixed-variant: '#3323cc'
  secondary-fixed: '#6ffbbe'
  secondary-fixed-dim: '#4edea3'
  on-secondary-fixed: '#002113'
  on-secondary-fixed-variant: '#005236'
  tertiary-fixed: '#ffddb8'
  tertiary-fixed-dim: '#ffb95f'
  on-tertiary-fixed: '#2a1700'
  on-tertiary-fixed-variant: '#653e00'
  background: '#f8f9ff'
  on-background: '#0b1c30'
  surface-variant: '#d3e4fe'
typography:
  display:
    fontFamily: Outfit
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Outfit
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-lg-mobile:
    fontFamily: Outfit
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  headline-md:
    fontFamily: Outfit
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-md:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.05em
  source-cite:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '500'
    lineHeight: 18px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base: 8px
  xs: 4px
  sm: 12px
  md: 24px
  lg: 40px
  xl: 64px
  container-max: 1280px
  gutter: 24px
---

## Brand & Style
The design system is built for a high-stakes educational environment where clarity and focus are paramount. It follows a **Minimalist-Professional** aesthetic that prioritizes content legibility and cognitive ease. By utilizing a "White-Label Academic" feel, the interface recedes to let the student's work and the AI's insights take center stage.

The emotional response is one of **structured empowerment**. The UI feels like a high-end physical study space—organized, quiet, and filled with light. We avoid "edutainment" tropes (bright gamification, heavy illustrations) in favor of a sophisticated toolset that treats the student as a serious scholar.

## Colors
The palette is rooted in institutional trust and growth. 
- **Primary (Indigo):** Used for primary actions, active navigation states, and the AI’s "presence" markers.
- **Secondary (Emerald):** Reserved exclusively for growth indicators: progress bars, completed milestones, and positive feedback loops.
- **Tertiary (Amber):** Used for "areas of improvement" or warning states that require the student's attention without inducing panic.
- **Surface Strategy:** In light mode, use `#FFFFFF` for cards against the `#F9FAFB` background to create subtle depth. In dark mode, use `#1E293B` for elevated surfaces against a `#0F172A` base.

## Typography
This design system uses a dual-font strategy. **Outfit** is used for headings to provide a modern, clean, and slightly technical character. **Inter** is used for all functional body text and UI labels due to its exceptional readability and neutral "academic" tone.

Hierarchy is enforced through strict weight usage. Citations and footnotes should use the `source-cite` token, which provides a visual distinction from the AI’s generated prose, ensuring the student can easily identify external references.

## Layout & Spacing
The layout relies on an **8px linear grid system**. All margins and paddings must be multiples of 8. 

- **Desktop:** 12-column fluid grid with a maximum container width of 1280px. Gutters are fixed at 24px.
- **Tablet:** 8-column grid with 16px margins.
- **Mobile:** 4-column grid with 16px margins. 

Heavy use of "Negative Space" is a functional requirement; lesson content should never feel cramped. Use `xl` spacing to separate major conceptual blocks in the learning interface.

## Elevation & Depth
Depth is communicated through **Ambient Shadows** and surface-on-surface layering rather than heavy borders.

- **Level 0 (Base):** The page background (`#F9FAFB`).
- **Level 1 (Cards/Sidebar):** Pure white background with a very soft, diffused shadow: `0px 4px 20px rgba(0, 0, 0, 0.03)`.
- **Level 2 (Modals/Popovers):** Higher elevation with a more pronounced shadow: `0px 12px 32px rgba(0, 0, 0, 0.08)`.

Transitions between levels should be seamless. Use backdrop blurs (`blur(8px)`) for fixed navigation headers to maintain context of the content scrolling beneath.

## Shapes
The shape language is "Optimistically Rounded." 
- **Containers & Cards:** Use a generous `24px` radius to soften the academic environment and make the AI feel more approachable.
- **Interactive Elements:** Buttons and input fields use a tighter `8px` or `12px` radius to maintain a sense of precision and "tool-like" utility.
- **Chat Bubbles:** Student bubbles have a sharp corner on the bottom right, while AI bubbles use a consistent `16px` radius to distinguish the "voice."

## Components
- **Buttons:** Primary buttons must be high-contrast Indigo with white text. Use "Squircle" shapes for icon-only buttons.
- **Progress Bars:** Use a linear gradient from Primary Indigo to Secondary Emerald to visually represent the journey from "Start" to "Mastery."
- **Source Citations:** Small, interactive chips that appear inline or in a footer. On hover, they should reveal a Level 2 popover with the full source snippet.
- **Chat Interface:**
    - *Student:* Right-aligned, Indigo background, white text.
    - *AI:* Left-aligned, White surface (Level 1), dark text, with a subtle Indigo border-left (3px) to signify "AI Processing."
- **Input Fields:** Large, 16px font size minimum to prevent zoom on mobile. Use a 2px Indigo border-bottom on focus rather than a full box glow.
- **Learning Cards:** These should include a "Mastery Indicator" in the top right—a small circular progress ring using the Secondary Emerald color.