---
name: Archival Scholasticism
colors:
  surface: '#fcf9f8'
  surface-dim: '#dcd9d9'
  surface-bright: '#fcf9f8'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f6f3f2'
  surface-container: '#f0eded'
  surface-container-high: '#eae7e7'
  surface-container-highest: '#e4e2e1'
  on-surface: '#1b1c1c'
  on-surface-variant: '#564241'
  inverse-surface: '#303030'
  inverse-on-surface: '#f3f0f0'
  outline: '#897171'
  outline-variant: '#dcc0bf'
  surface-tint: '#a13d41'
  primary: '#4b000b'
  on-primary: '#ffffff'
  primary-container: '#6b141d'
  on-primary-container: '#f37b7e'
  inverse-primary: '#ffb3b2'
  secondary: '#775a17'
  on-secondary: '#ffffff'
  secondary-container: '#fed486'
  on-secondary-container: '#785a17'
  tertiary: '#112425'
  on-tertiary: '#ffffff'
  tertiary-container: '#27393a'
  on-tertiary-container: '#8fa3a4'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#ffdad9'
  primary-fixed-dim: '#ffb3b2'
  on-primary-fixed: '#410008'
  on-primary-fixed-variant: '#82252c'
  secondary-fixed: '#ffdea3'
  secondary-fixed-dim: '#e9c174'
  on-secondary-fixed: '#261900'
  on-secondary-fixed-variant: '#5d4200'
  tertiary-fixed: '#d2e6e7'
  tertiary-fixed-dim: '#b6cacb'
  on-tertiary-fixed: '#0b1e1f'
  on-tertiary-fixed-variant: '#374a4b'
  background: '#fcf9f8'
  on-background: '#1b1c1c'
  surface-variant: '#e4e2e1'
typography:
  display-lg:
    fontFamily: Playfair Display
    fontSize: 56px
    fontWeight: '700'
    lineHeight: 64px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Playfair Display
    fontSize: 40px
    fontWeight: '700'
    lineHeight: 48px
  headline-lg-mobile:
    fontFamily: Playfair Display
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
  headline-md:
    fontFamily: Playfair Display
    fontSize: 28px
    fontWeight: '600'
    lineHeight: 36px
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
  label-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 20px
    letterSpacing: 0.05em
  caption:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  base: 8px
  container-max: 1280px
  gutter: 24px
  margin-mobile: 16px
  margin-desktop: 48px
---

## Brand & Style

The design system is rooted in the concept of "Digital Preservation." It bridges the gap between ancient historical artifacts and modern academic research. The visual language evokes the authority of a prestigious university library combined with the efficiency of a high-end metadata repository. 

The aesthetic style is **Minimalist / Editorial**. It prioritizes legibility, high-quality historical imagery, and a structured hierarchy that respects the complexity of sigillography. This design system avoids unnecessary ornamentation, allowing the intricate details of wax seals and parchment textures to serve as the primary visual interest. It communicates trustworthiness, intellectual rigor, and timelessness.

## Colors

The palette is inspired by traditional archival materials: aged oxblood leather, metallic wax seals, and vellum.

- **Primary (Deep Burgundy):** Used for primary brand moments, critical calls to action, and header accents. It represents the "seal" itself.
- **Secondary (Warm Gold):** Reserved for highlights, active states, and decorative rules that guide the eye. It adds a layer of prestige.
- **Neutral (Charcoal):** Provides a high-contrast, legible base for body copy and metadata, avoiding the harshness of pure black.
- **Background (Cream/Off-white):** Creates a warm, paper-like canvas that reduces eye strain during long-form research.

Functional colors (Success, Warning, Error) should be slightly desaturated to maintain the sophisticated, academic tone.

## Typography

This design system utilizes a high-contrast typographic pairing to distinguish between narrative authority and data precision.

- **Headlines (Playfair Display):** Should be used for page titles, section headers, and significant pull-quotes. The high stroke contrast conveys a sense of historical tradition.
- **Body & Metadata (Inter):** A utilitarian sans-serif chosen for its exceptional legibility at small sizes, crucial for reading dense catalogue entries and archival notes.
- **Labels:** Use uppercase and increased letter spacing for small UI elements (tags, filters, table headers) to provide a structural, modern feel that balances the serif headlines.

## Layout & Spacing

The layout philosophy follows a **Fixed Grid** model on desktop, mimicking the margins of a printed academic journal.

- **Grid:** A 12-column grid is used for the main content area. Data-heavy views (like search results) may utilize a flexible 4-column layout for seal cards.
- **Whitespace:** Emphasize generous vertical rhythm. Use large top margins for new chapters or sections to allow the content to "breathe" and signal a transition in topic.
- **Responsive Behavior:** On mobile, margins compress to 16px, and multi-column layouts stack vertically. The focus remains on a single-column, highly legible reading experience.

## Elevation & Depth

To maintain a scholarly and archival feel, depth is created through **Tonal Layers** and **Low-Contrast Outlines** rather than aggressive shadows.

1.  **Surfaces:** The background is the primary layer (Cream). Search bars and secondary containers use a slightly lighter or white surface to appear "raised."
2.  **Borders:** Use fine, 1px charcoal lines with 20% opacity for card containers and dividers. This mimics the precision of technical drawings or catalogue ledgers.
3.  **Imagery:** Artifact images (seals) should have a very subtle, soft ambient shadow to provide a sense of physical presence on the digital "page."
4.  **Overlay Blurs:** For modals, use a light backdrop blur (Glassmorphism) with a primary color tint to keep the context of the archive visible behind the focused task.

## Shapes

The shape language is conservative and structured. 

- **Corners:** A "Soft" rounding (0.25rem) is applied to buttons and input fields to keep the UI approachable but professional. 
- **Imagery:** Photographic assets of seals should be presented in circular or natural-form containers where appropriate, reflecting their actual physical shape, while metadata containers remain strictly rectangular to maintain order.

## Components

- **Buttons:** 
    - **Primary:** Deep Burgundy background with white Inter Medium text. No shadow, 1px border of the same color.
    - **Secondary:** Transparent background with Warm Gold text and border.
- **Cards (Seal Entries):** Use the background surface with a 1px Charcoal (20% opacity) border. Top-align the seal image followed by a Playfair Display title and Inter Metadata.
- **Search Inputs:** Full-width fields with a minimal bottom border in Charcoal. Use an icon of a magnifying glass in Warm Gold.
- **Chips/Tags:** Used for "Century," "Material," or "Region" filters. Small font size, rounded-sm, with a light Burgundy tint background and deep Burgundy text.
- **Lists:** Data lists should use "Zebra-striping" with a very subtle 2% opacity Burgundy fill on alternating rows to aid horizontal eye tracking across metadata points.
- **Citations:** A specialized component for researchers to quickly copy bibliographic references, styled with a light cream background and a left-side Warm Gold accent border.