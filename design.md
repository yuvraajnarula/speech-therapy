# UI/UX Redesign System: Warm Tactile Paper Bento

## Core Aesthetic & Philosophy
- Anti-AI-Slop Directive: BAN all generic dark-mode purple/cyan neon gradients, floating glassmorphism blobs, fake 3D wireframe mesh renders, and excessive drop-shadow glow. 
- Paradigm: Warm, grounded, tactile Swiss-grid meets Japanese stationery / architectural newsprint. 
- Persona: Calm, intellectual, human-crafted, high-craft utility (think Teenage Engineering meets Muji or a vintage physical notebook).

## Color Palette (Warm Cream & Paper)
- Background Primary (Canvas): #F9F6F0 (Warm Unbleached Cream / Soft Rice Paper)
- Background Secondary (Cards/Compartments): #F2ECE1 (Warm Stone / Pressed Cotton Paper)
- Background Elevated (Active/Hover Cards): #EBE2D3 (Deep Oat / Recycled Cardboard)
- Text Primary: #1C1917 (Warm Charcoal / Graphite Ink — never pure #000000)
- Text Secondary: #57534E (Muted Slate / Lead Pencil)
- Accent Primary: #C25E00 (Burnt Persimmon / Aged Terracotta)
- Accent Secondary: #3F5E4D (Deep Forest / Vintage Sage Green)
- Borders & Dividers: #E4DCD0 (Fine 1px Debossed Paper Crease) with subtle inset shadows.

## Typography
- Heading Font: Editorial Serif or High-Character Grotesk (e.g.,Instrument Serif, Newsreader, or PP Neue Montreal) with tight letter-spacing.
- Body Font: Clean, neutral humanist sans-serif (e.g., Inter, Plus Jakarta Sans, or Public Sans).
- Monospace Font: Crisp technical mono (e.g., JetBrains Mono) for data points, tags, and micro-labels.
- Scale: High contrast between oversized editorial headers and grounded, readable body copy. No generic "AI Assistant" robotic speak; use clear, functional micro-copy.

## Layout Structure (Bento Grid)
- Grid System: CSS Grid with asymmetrical, multi-span compartment modules (Bento Box architecture).
- Card Treatment:
  - Corner Radius: 12px to 16px soft-rounded corners (tactile card edges).
  - Borders: 1px solid #E4DCD0 with a soft, feather-light inner top highlight (`box-shadow: inset 0 1px 0 rgba(255,255,255,0.6)`) to give cards a real physical paper lift.
  - Padding: Generous internal breathing room (min 20px–24px) to avoid visual claustrophobia.
  - Spacing / Gap: 16px–20px grid gaps acting as clean whitespace channels.
- Compartment Variety: Mix data readouts, compact interactive buttons, minimalist status badges, and typography-driven statement blocks rather than repeating identical boring card layouts.

## Surface & Micro-Texture Details
- Grain / Noise: Apply a faint, ultra-low opacity (2% to 3%) SVG noise/grain overlay across the global background to simulate fine paper fibers.
- Interactions: 
  - Hover states: Cards depress slightly or shift border color to warm terracotta (#C25E00) with a smooth, snappy transition.
  - No sci-fi particle emitters or generic neon swooshes. Keep interactions grounded, fast, and tactile (like pressing a heavy mechanical key or turning a page).
