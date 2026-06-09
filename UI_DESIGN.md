# AttendAI — UI Design & Color Scheme Documentation

## Overview
AttendAI uses a **modern dark theme** with a tech-forward aesthetic. The design emphasizes clarity, accessibility, and a sleek monochromatic interface with vibrant accent colors for interactive elements.

---

## Color Palette

### Primary Colors
| Color | Hex Value | Usage | RGB |
|-------|-----------|-------|-----|
| **Background** | `#080c10` | Page background, primary dark surface | rgb(8, 12, 16) |
| **Surface** | `#0e1419` | Cards, containers, panels | rgb(14, 20, 25) |
| **Surface 2** | `#111820` | Secondary surface (dashboard panels) | rgb(17, 24, 32) |
| **Border** | `#1c2530` | Dividers, outlines, subtle borders | rgb(28, 37, 48) |
| **Very Dark** | `#050709` | Camera preview background | rgb(5, 7, 9) |
| **Darker Bar** | `#0a0f14` | Status bars, headers | rgb(10, 15, 20) |

### Accent Colors
| Color | Hex Value | Usage | Meaning |
|-------|-----------|-------|---------|
| **Accent (Mint)** | `#00e5a0` | Primary CTAs, highlights, success states | Active, positive |
| **Blue** | `#0077ff` | Secondary buttons, alternative actions | Information, links |
| **Red** | `#ff4560` | Error states, warnings, cancel actions | Negative, destructive |
| **Yellow** | `#ffc145` | Warnings, caution states | Alert |

### Text Colors
| Color | Hex Value | Usage |
|-------|-----------|-------|
| **Primary Text** | `#c8d6e5` | Main body text, readable content |
| **Muted Text** | `#4a6075` | Labels, helper text, secondary info |
| **White** | `#ffffff` | Logo, titles, high emphasis |

---

## Typography

### Font Stack
```css
Primary Font: 'DM Mono' (Monospace)
  - Weight: 400 (regular), 500 (medium)
  - Used for: Body text, input fields, buttons, labels
  
Display Font: 'Syne' (Sans-serif)
  - Weight: 600, 700, 800 (bold)
  - Used for: Logos, page titles, headings
```

### Text Sizes & Usage

| Size | CSS Value | Usage |
|------|-----------|-------|
| **Extra Large** | `1.5rem` | Login page logo |
| **Large** | `1.2rem` | Registration card logo |
| **Medium** | `1rem` | Page titles (dashboard) |
| **Body** | `0.85rem` | Button text, form inputs |
| **Small** | `0.75rem` | General UI text, messages |
| **Extra Small** | `0.62rem` | Labels, section headers |
| **Tiny** | `0.55rem` | Status text, muted info |

### Letter Spacing
- Standard: `0.03em` to `0.08em` for emphasis
- Uppercase Labels: `0.1em` to `0.12em` (increased for readability)
- Button Text: `0.05em` (subtle spacing)

---

## Layout & Structure

### Desktop Layout (Main Application)
```
┌─────────────────────────────────────────┐
│  Logo      │                    │  Date │
├─────────────────────────────────────────┤
│             │                           │
│  Sidebar    │                           │
│  (220px)    │     Main Content Area     │
│             │     (Flex: 1)             │
│             │                           │
└─────────────────────────────────────────┘
```

### Component Layout
- **Sidebar Width**: 220px (fixed)
- **Card Max Width**: 520px (login/registration forms)
- **Padding**: 28px (main content), 36px (cards)
- **Gap Spacing**: 12px (grid items), 6-10px (elements within cards)
- **Border Radius**: 8px (cards), 6-7px (inputs), 16px (large cards)

### Grid System
- **2-Column Grid**: Used in forms for side-by-side inputs
  ```css
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  ```

---

## Component Design

### Buttons

#### Primary Button (Accent)
- **Background**: `#00e5a0` (Mint)
- **Text Color**: `#000000` (Black)
- **Padding**: `8-12px horizontal`, `10-12px vertical`
- **Border Radius**: `6-8px`
- **Hover State**: `opacity: 0.85-0.88`
- **Font Size**: `0.75-0.85rem`
- **Font Weight**: `500-600`
- **Letter Spacing**: `0.03-0.05em`
- **Usage**: Confirm, Submit, Primary actions

#### Secondary Button (Blue)
- **Background**: `#0077ff`
- **Text Color**: White
- **Similar styling to primary**
- **Usage**: Alternative actions, secondary CTAs

#### Ghost Button (Border)
- **Background**: `var(--border)` or transparent
- **Text Color**: `var(--text)` or `var(--muted)`
- **Border**: `1px solid var(--border)`
- **Hover**: `opacity: 0.85` or lighter background
- **Usage**: Cancel, optional actions, camera controls

### Form Elements

#### Input Fields
- **Background**: `var(--bg)` (Very dark)
- **Border**: `1px solid var(--border)`
- **Text Color**: `var(--text)` (Light gray)
- **Padding**: `9-10px horizontal`, `10-12px vertical`
- **Border Radius**: `7-8px`
- **Focus State**: 
  - `border-color: var(--accent)` (Mint outline)
  - Smooth transition: `0.2s`

#### Labels
- **Font Size**: `0.62-0.68rem`
- **Color**: `var(--muted)`
- **Text Transform**: UPPERCASE
- **Letter Spacing**: `0.08-0.1em`
- **Margin Bottom**: `5-6px`

#### Select Dropdowns
- **Same styling as inputs**
- **Option Background**: `var(--bg)`

### Cards & Containers

#### Main Card (Login/Register)
- **Background**: `var(--surf)` (`#0e1419`)
- **Border**: `1px solid var(--border)`
- **Border Radius**: `16px`
- **Padding**: `36-40px`
- **Max Width**: `420-520px` (centered on screen)
- **Box Shadow**: None (flat design)

#### Section Label
- **Font Size**: `0.6rem`
- **Text Transform**: UPPERCASE
- **Color**: `var(--muted)`
- **Letter Spacing**: `0.1em`
- **Border Bottom**: `1px solid var(--border)`
- **Padding**: `6px bottom`
- **Margin**: `12px bottom`, `24px top`

### Sidebar Navigation

#### Active Navigation Item
- **Color**: `var(--accent)` (Mint)
- **Left Border**: `2px solid var(--accent)`
- **Background**: `rgba(0, 229, 160, 0.05)` (Subtle tint)
- **Font Size**: `0.78rem`

#### Inactive Navigation Item
- **Color**: `var(--muted)`
- **Hover**: 
  - Text color: `var(--text)`
  - Background: `rgba(255, 255, 255, 0.03)`

### Status Indicators

#### Pulsing Dot (Live)
```css
Background: var(--accent)
Box Shadow: 0 0 6px var(--accent)
Animation: pulse (1.8s)
- 0%, 100%: opacity 1
- 50%: opacity 0.3
Width/Height: 7px
Border Radius: 50%
```

#### Progress Dots (Capture Status)
- **Unfilled**: `border: 1px solid var(--muted)`, `background: var(--border)`
- **Filled**: `background: var(--accent)`, `border-color: var(--accent)`
- **Size**: `10px × 10px`
- **Border Radius**: `50%`
- **Spacing**: `6px gap`
- **Transition**: `0.3s`

### Messages & Feedback

#### Error Message
- **Color**: `var(--red)` (`#ff4560`)
- **Font Size**: `0.75rem`
- **Margin Top**: `10-14px`
- **Min Height**: `16-18px` (prevents layout shift)

#### Success Message
- **Color**: `var(--accent)` (Mint)
- **Same sizing as error**

#### Helper Text
- **Color**: `var(--muted)`
- **Font Size**: `0.7-0.72rem`
- **Margin Top**: `6-10px`

---

## Interactive States

### Transitions & Animations

#### Default Transitions
```css
transition: 0.15s ease (buttons, hover effects)
transition: 0.2s ease (inputs, focus states)
transition: 0.3s ease (progress dots, status changes)
```

#### Hover Effects
- **Buttons**: `opacity: 0.85-0.88`, `transform: translateY(-1px)`
- **Navigation Items**: `color` change, `background` tint
- **Links**: Color change to accent

#### Focus States
- **Input Fields**: `border-color: var(--accent)`
- **Buttons**: Inherited hover state

#### Loading/Waiting
- **Disabled Buttons**: `opacity: 0.5-0.6`
- **Pulsing Elements**: Smooth opacity animation (1.8s loop)

---

## Responsive Design

### Breakpoints & Adjustments
- **Mobile First**: Cards take full width with padding
- **Desktop (420px+)**: Forms display at max-width with centering
- **Large Desktop**: Sidebar layout activates

### Padding & Margins
- **Mobile**: `16px` padding
- **Tablet**: `20px` padding
- **Desktop**: `28px` content padding, `18px` sidebar padding

### Typography Scaling
- Mobile: Slightly reduced font sizes where needed
- Desktop: Full size as specified

---

## Accessibility Features

### Color Contrast
- **Text on Dark**: `#c8d6e5` text on `#0e1419` background = High contrast
- **Accent Buttons**: Black text on mint = WCAG AA compliant
- **Muted Text**: Sufficient contrast for secondary content

### Focus Indicators
- **Visible Focus**: Accent-colored border on inputs
- **Keyboard Navigation**: Clear visual feedback on all interactive elements

### Semantic HTML
- Proper use of `<label>`, `<input>`, `<button>` tags
- Logical tab order for form navigation

---

## CSS Variables Summary

```css
:root {
  /* Backgrounds */
  --bg: #080c10;
  --surf: #0e1419;
  --surf2: #111820;
  
  /* UI */
  --border: #1c2530;
  --accent: #00e5a0;
  --blue: #0077ff;
  
  /* Text */
  --text: #c8d6e5;
  --muted: #4a6075;
  
  /* Status */
  --red: #ff4560;
  --yellow: #ffc145;
}
```

---

## Pages Overview

### 1. Login Page
- **Layout**: Centered card
- **Components**: Tabs (Teacher/Student), Input fields, Submit button
- **Color Accent**: Mint button with black text
- **Message Area**: Red for errors, centered below form

### 2. Student Registration
- **Layout**: Centered card with form sections
- **Sections**:
  - Personal Information (2-column grid)
  - Class Selection (dropdown)
  - Face Registration (camera feed + progress dots)
- **Progress Indicators**: 7 dots showing capture progress
- **Camera Display**: Dark background with live feed overlay

### 3. Teacher Dashboard
- **Layout**: Sidebar + Main content area
- **Sidebar**: Navigation with active state highlighting
- **Content Panels**: Different pages shown/hidden based on nav selection
- **Charts**: Using Chart.js with dark theme
- **Tables**: Dark themed data display

### 4. Student Dashboard
- **Similar structure to teacher dashboard**
- **Simplified navigation**
- **Attendance display with status colors**

---

## Design Philosophy

### Principles
1. **Dark-First**: Reduces eye strain, modern aesthetic
2. **Minimalist**: Clean lines, ample whitespace (darkspace)
3. **Tech-Forward**: Monospace font suggests "tech" interface
4. **High Contrast**: Mint accent pops against dark background
5. **Consistent**: Repeating patterns and spacing
6. **Accessible**: Good color contrast, clear interactive states

### Visual Hierarchy
1. **Titles/Logo** (Syne, bold, white)
2. **Form Fields** (slightly lighter, readable)
3. **Labels** (muted, uppercase for hierarchy)
4. **Helper Text** (very muted, small)

---

## Future Enhancement Ideas

- [ ] Dark/Light mode toggle
- [ ] Gradient accents for premium feel
- [ ] Glassmorphism effects (frosted glass panels)
- [ ] Micro-interactions (button ripples, smooth transitions)
- [ ] Custom scrollbar styling throughout
- [ ] Animated loaders/skeletons
- [ ] Toast notifications for real-time feedback
- [ ] Staggered animations on page load
