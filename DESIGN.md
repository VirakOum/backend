# Design System Specification: The Kinetic Precision Framework

## 1. Overview & Creative North Star
**Creative North Star: "The Architectural Flow"**
This design system moves away from the static, boxy nature of traditional logistics dashboards toward a high-end editorial experience. We are transcending the "Apex Grid" by infusing it with tonal depth and rhythmic spacing. The goal is to make complex global supply chain data feel as intentional and curated as a premium broadsheet layout. 

We achieve "Kinetic Precision" through:
*   **Intentional Asymmetry:** Using the `24 (5.5rem)` and `16 (3.5rem)` spacing tokens to create breathing room that guides the eye.
*   **Chromatic Authority:** Leveraging the deep `#001b44` (Primary) not just as a color, but as a structural anchor that provides weight against the airy `#fbf9f8` (Background).
*   **Softened Architecture:** Replacing rigid borders with sophisticated color-blocking and glassmorphism.

## 2. Colors & Surface Philosophy
The palette is rooted in a "Command and Control" hierarchy. Navy provides the professional foundation, while high-vibrancy accents (Emerald, Amber, Red) serve as the pulse of the dashboard.

### The "No-Line" Rule
**Prohibit 1px solid borders for sectioning.** Structural integrity must be achieved through background shifts. 
*   Use `surface_container_low` (#f5f3f3) for secondary content areas.
*   Use `surface_container_lowest` (#ffffff) for primary interactive cards.
*   Transitions between these surfaces provide enough contrast for the eye to perceive boundaries without the "cage" effect of borders.

### Surface Hierarchy & Nesting
Treat the UI as a series of layered planes:
1.  **Base Layer:** `background` (#fbf9f8).
2.  **Sectioning Layer:** `surface_container` (#efeded) or `surface_container_low` (#f5f3f3) for large layout blocks.
3.  **Content Layer:** `surface_container_lowest` (#ffffff) for individual data modules or cards.
4.  **Floating Layer:** Semi-transparent `primary_container` with a 12px backdrop-blur for temporary overlays.

### The "Glass & Gradient" Rule
To elevate the "Apex Grid," hero data points or active navigation states should use a subtle linear gradient: 
*   **Direction:** 135° 
*   **From:** `primary` (#001b44) 
*   **To:** `primary_container` (#002f6c)
*   **Effect:** This adds "soul" and dimension to otherwise flat functional elements.

## 3. Typography
We utilize a pairing of **Manrope** (Display/Headline) for an authoritative, architectural feel and **Inter** (Body/Labels) for maximum legibility at high data densities.

*   **The Power Scale:** Use `display-lg` (3.5rem) sparingly for high-level KPIs (e.g., total active shipments). This creates a bold, editorial focal point.
*   **Semantic Hierarchy:** 
    *   **Headlines:** `headline-sm` (1.5rem) in Manrope for module titles.
    *   **Data Labels:** `label-md` (0.75rem) in Inter, using `on_surface_variant` (#434750) for secondary metadata.
    *   **Body:** `body-md` (0.875rem) for general information to maintain a high information density without clutter.

## 4. Elevation & Depth
In this system, depth is a product of light and layering, never heavy shadows.

*   **Tonal Layering:** Instead of shadows, place a `surface_container_lowest` card on a `surface_container_low` background. The subtle shift from `#f5f3f3` to `#ffffff` creates a sophisticated, "natural" lift.
*   **Ambient Shadows:** For floating elements like tooltips or modals, use an ultra-diffused shadow:
    *   `box-shadow: 0 20px 40px rgba(0, 27, 68, 0.06);` (Note the use of a tinted shadow using the Primary color).
*   **The Ghost Border Fallback:** If a divider is mandatory for accessibility, use `outline_variant` (#c4c6d2) at **15% opacity**. Anything higher is considered "noise."
*   **Glassmorphism:** For map overlays or floating navigation bars, use `surface` at 80% opacity with a `blur(10px)` effect to maintain a sense of environmental context.

## 5. Components

### Map & Data Visualization
*   **The Multi-Colored Map:** The map base should use `surface_dim` (#dbd9d9) for landmasses and `surface_bright` (#fbf9f8) for water to keep it professional. Use `secondary` (#006d43), `tertiary_fixed` (#fbbc00), and `error` (#ba1a1a) for live route tracking.
*   **Data Visualization:** Use high-contrast pairings. Success states use `secondary_container` (#75f8b3) backgrounds with `on_secondary_container` (#007147) text.

### Buttons & Interaction
*   **Primary Button:** `primary` (#001b44) background with `on_primary` (#ffffff) text. Use `xl` (0.75rem) roundedness.
*   **Secondary/Action Chips:** Use `primary_fixed` (#d8e2ff) with `on_primary_fixed_variant` (#224583). 
*   **Inputs:** Use `surface_container_highest` (#e4e2e2) for the input track with no border. On focus, transition the background to `surface_container_lowest` and add a `ghost border` of `primary`.

### Cards & Lists
*   **Card Design:** Forbid dividers. Separate list items using the `3 (0.6rem)` spacing token. 
*   **Status Indicators:** Instead of a simple dot, use a "Pill" with a subtle gradient and `label-sm` text for high-end readability.

## 6. Do's and Don'ts

### Do:
*   **Use White Space as a Tool:** Use the `20` and `24` spacing tokens to separate major functional blocks.
*   **Layer Surfaces:** Always check if a background color shift can replace a line.
*   **Embrace Manrope:** Use the display scale to create a sense of "Logistics Command."

### Don't:
*   **No Pure Black:** Never use `#000000`. Use `on_surface` (#1b1c1c) for text to maintain a premium feel.
*   **No Default Shadows:** Avoid standard CSS shadows; they look "cheap." Always tint your shadows with the Primary Navy.
*   **No Grid Cramming:** If the "Apex Grid" feels tight, increase the gutter using the `8 (1.75rem)` spacing token.