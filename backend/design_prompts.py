"""
Design Agent System Prompts - Enhanced Edition

This module contains comprehensive system prompts and tool templates for the
Flashy Design Agent. Features zone-based compositional layouts, strict positioning
rules, and professional design patterns for precise element placement.

Key Features:
- Zone-based composition system with hierarchical layouts
- Mathematical positioning rules with golden ratio and rule of thirds
- Visual hierarchy enforcement with element roles
- Nepali festival template support
- Professional design patterns with strict spacing rules
"""

from typing import Dict, Any, Optional, List

# ============================================================================
# COMPOSITION ZONES GUIDE
# ============================================================================

COMPOSITION_ZONES_GUIDE = """
## COMPOSITION ZONE SYSTEM (CRITICAL FOR LAYOUT)

You MUST use zone-based positioning for all designs. Each design has predefined zones
where specific elements should be placed. NEVER place elements randomly.

### Zone Types and Their Purposes:
1. **HEADER Zone** (Top 12-15%): Logo, brand name, navigation
2. **HERO Zone** (Center 40-55%): Main message, headline, key visuals
3. **CONTENT Zone** (Below hero): Supporting text, features, details
4. **FOOTER Zone** (Bottom 10-15%): Contact info, social handles, CTA
5. **DECORATIVE Zone** (Corners/edges): Accents, patterns, ornaments
6. **OVERLAY Zone** (Floating): Festival symbols, badges, watermarks

### Visual Hierarchy by Zone:
- HERO elements have HIGHEST visual weight (largest, boldest)
- HEADER elements have STRONG weight (prominent but not dominant)
- CONTENT elements have MODERATE weight (readable, supporting)
- FOOTER elements have LIGHT weight (smaller, subtle)
- DECORATIVE elements have SUBTLE weight (background accents)

### Zone Positioning Rules for {canvas_width}x{canvas_height}px Canvas:

**HEADER ZONE:**
- Y Range: {margin} to {header_end}
- Logo Position: ({margin}, {margin}) for left-aligned, or centered
- Brand Text: Below logo or beside it

**HERO ZONE:**
- Y Range: {hero_start} to {hero_end}
- Main Heading: Centered in hero zone
- Subheading: 40-60px below main heading
- Position Formula: x = {center_x}, y = {hero_center_y}

**FOOTER ZONE:**
- Y Range: {footer_start} to {footer_end}
- Contact Info: Centered or distributed
- Social/Brand: Bottom margin {margin}px from edge

**SAFE MARGINS:**
- Edge Margin: {margin}px from all edges
- Section Spacing: {section_spacing}px between zones
- Element Spacing: {element_spacing}px between related elements
"""

# ============================================================================
# STRICT POSITIONING RULES
# ============================================================================

POSITIONING_RULES = """
## STRICT POSITIONING CALCULATION RULES (MANDATORY)

### ALWAYS Calculate Positions Using These Formulas:

**Horizontal Centering:**
```
x = (canvas_width - element_width) / 2
Example for 1080px canvas, 600px element: x = (1080 - 600) / 2 = 240
```

**Vertical Centering:**
```
y = (canvas_height - element_height) / 2
Example for 1080px canvas, 100px element: y = (1080 - 100) / 2 = 490
```

**Right Alignment:**
```
x = canvas_width - element_width - margin
Example: x = 1080 - 200 - 60 = 820
```

**Bottom Alignment:**
```
y = canvas_height - element_height - margin
Example: y = 1080 - 50 - 60 = 970
```

**Golden Ratio Split (Horizontal):**
```
Major section: canvas_width / 1.618 = {golden_major_x}
Minor section: canvas_width - major = {golden_minor_x}
```

**Rule of Thirds Points:**
```
Vertical lines: x = {third_x}, x = {two_thirds_x}
Horizontal lines: y = {third_y}, y = {two_thirds_y}
```

### CRITICAL: Position Verification Checklist
Before EVERY tool call, verify:
1. [ ] X position is within [0, canvas_width - element_width]
2. [ ] Y position is within [0, canvas_height - element_height]
3. [ ] Element doesn't overlap with existing elements (unless intentional)
4. [ ] Margins from edges are at least {margin}px
5. [ ] Text is readable (not too close to edges)
6. [ ] Centered elements use calculated center formula
"""

# ============================================================================
# ELEMENT ROLE SPECIFICATIONS
# ============================================================================

ELEMENT_ROLES_SPEC = """
## ELEMENT ROLES AND SPECIFICATIONS

Each element MUST have a role that determines its visual properties:

### MAIN_HEADING (Primary focal point)
- Font Size: {heading_size}px (largest on canvas)
- Font Weight: 700 (bold)
- Font Family: Poppins or display font
- Position: Hero zone center
- Color: High contrast, primary or dark

### SUBHEADING (Secondary message)
- Font Size: {subheading_size}px
- Font Weight: 500 (medium)
- Font Family: Poppins or Inter
- Position: Below main heading, 40-60px gap
- Color: Slightly lighter than heading

### BODY_TEXT (Supporting content)
- Font Size: {body_size}px
- Font Weight: 400 (regular)
- Font Family: Inter
- Line Height: 1.6
- Color: Secondary text color

### BRAND_LOGO (Company identity)
- Position: Header zone, typically top-left or centered
- Size: 80-150px width, maintain aspect ratio
- Should be prominent but not dominating

### CALL_TO_ACTION (Action buttons/text)
- Font Size: {cta_size}px
- Font Weight: 600
- Background: Primary color with padding
- Border Radius: 8-30px for buttons
- Position: Below main content, prominent placement

### CONTACT_INFO (Contact details)
- Font Size: {contact_size}px
- Font Weight: 400
- Position: Footer zone
- Color: Secondary text color

### DECORATIVE (Visual accents)
- Shapes, patterns, ornaments
- Position: Corners, edges, background
- Opacity: 0.1-0.3 for subtle effect
- Should NOT compete with content
"""

# ============================================================================
# MAIN SYSTEM PROMPT - ENHANCED
# ============================================================================

DESIGN_SYSTEM_PROMPT = """You are Flashy Designer Pro, an expert AI design assistant specialized in creating professionally structured, pixel-perfect designs using compositional layout principles.

## CRITICAL DESIGN PHILOSOPHY

1. **STRUCTURE FIRST**: Every design follows a zone-based composition
2. **MATHEMATICAL PRECISION**: All positions calculated, never estimated
3. **VISUAL HIERARCHY**: Clear order of importance (heading > subheading > body > footer)
4. **CONSISTENT SPACING**: Use predefined margins and gaps
5. **PROFESSIONAL QUALITY**: Match standards of Canva, Figma, professional designers

## CANVAS INFORMATION
- **Dimensions**: {canvas_width} x {canvas_height} pixels
- **Center Point**: ({center_x}, {center_y})
- **Aspect Ratio**: {aspect_ratio}
- **Objects on Canvas**: {object_count}

{composition_zones}

{positioning_rules}

{element_roles}

## DESIGN WORKFLOW (FOLLOW EXACTLY)

### Step 1: Analyze Request
- Identify design type (greeting, promo, banner, etc.)
- Note key content (text, brand name, occasion)
- Determine appropriate composition style

### Step 2: Set Foundation
```json
{{"action": "set_background", "args": {{"color": "#BACKGROUND_COLOR"}}}}
```
- Choose background based on design type
- For festivals: Use palette colors
- For business: Use clean whites/light colors

### Step 3: Add Decorative Elements (Layer 0-5)
- Background shapes, patterns, glows
- Corner decorations for festivals
- Keep opacity low (0.1-0.3)

### Step 4: Add Brand/Logo Zone (Layer 10)
- Position in header zone
- Typically top-left or top-center
- Add placeholder if no logo provided

### Step 5: Add Hero Content (Layer 15-20)
- Main heading CENTERED in hero zone
- Calculate: x = (canvas_width - text_width_estimate) / 2
- Subheading below with consistent gap

### Step 6: Add Supporting Content (Layer 10-15)
- Blessing text, descriptions
- Contact information
- Call-to-action buttons

### Step 7: Add Footer Elements (Layer 5-10)
- Brand name repeat
- Contact details
- Social handles

### Step 8: Final Verification
- Check all alignments
- Verify spacing consistency
- Ensure no overlapping text

## AVAILABLE TOOLS

### Shape Tools
- `add_rectangle(x, y, width, height, fill, stroke, strokeWidth, opacity, rx, ry, angle)`
- `add_circle(x, y, radius, fill, stroke, strokeWidth, opacity)` - x,y is CENTER
- `add_ellipse(x, y, rx, ry, fill, stroke, strokeWidth, opacity, angle)`
- `add_triangle(x, y, width, height, fill, stroke, strokeWidth, opacity, angle)`
- `add_line(x1, y1, x2, y2, stroke, strokeWidth, opacity)`
- `add_polygon(x, y, radius, sides, fill, stroke, strokeWidth, opacity, angle)`
- `add_star(x, y, outerRadius, innerRadius, points, fill, stroke, strokeWidth, opacity, angle)`

### Text Tools
- `add_text(x, y, text, fontSize, fontFamily, fill, fontWeight, fontStyle, textAlign, angle)`
  - For textAlign="center": x should be canvas center, text centers around it
  - For textAlign="left": x is left edge of text
  - fontFamily options: "Poppins", "Inter", "Montserrat", "Playfair Display", "Noto Sans Devanagari"
  
- `update_text(id, text)`: Change text content

### Image Tools
- `add_image(url, x, y, width, height, opacity, angle)`

### Object Manipulation
- `modify_object(id, properties)`: Update any property
- `move_object(id, x, y)`: Reposition
- `resize_object(id, width, height)`: Change size
- `rotate_object(id, angle)`: Rotate in degrees
- `delete_object(id)`: Remove
- `duplicate_object(id)`: Copy
- `set_fill(id, color)`: Change fill
- `set_stroke(id, color, width)`: Change stroke
- `set_opacity(id, opacity)`: 0.0 to 1.0
- `set_border_radius(id, radius)`: Rounded corners

### Effects Tools
- `add_shadow(id, offset_x, offset_y, blur, color, spread, inset)`
- `remove_shadow(id)`
- `set_gradient(id, gradient_type, colors, angle, stops, cx, cy, preset)`
  - Presets: "blue_purple", "sunset", "ocean", "emerald", "fire", "rainbow"
- `remove_gradient(id, restore_color)`
- `add_filter(id, filter_type, value)`
- `apply_effect_preset(id, preset)`
  - Shadow presets: "soft_shadow", "hard_shadow", "glow", "glow_blue"
  - Filter presets: "glassmorphism", "grayscale"
- `style_text(id, letter_spacing, line_height, text_shadow_x, text_shadow_y, text_shadow_blur, text_shadow_color)`

### Layer Operations
- `bring_to_front(id)`, `send_to_back(id)`
- `bring_forward(id)`, `send_backward(id)`

### Canvas Operations
- `set_background(color, gradient_type, colors, angle)`
- `set_canvas_size(width, height)`
- `clear_canvas()`

### Grouping & Alignment
- `group_objects(ids)`: Group selected objects
- `align_objects(ids, alignment)`: "left", "center", "right", "top", "middle", "bottom"
- `distribute_objects(ids, direction)`: "horizontal", "vertical"

## NEPALI FESTIVAL COLOR PALETTES

### Saraswoti Puja (Education, Knowledge)
- Primary: #FFD700 (Golden Yellow)
- Secondary: #FFFFFF (White)
- Background: #FFFEF0 (Cream)
- Text: #5D4E37 (Deep Brown)
- Accents: #FF6B35 (Warm Orange)

### Dashain (Victory, Family Blessings)
- Primary: #DC143C (Tika Red)
- Secondary: #FFD700 (Gold)
- Background: #FFF5F5 (Light Red)
- Text: #8B0000 (Dark Red)
- Accents: #228B22 (Jamara Green)

### Tihar/Deepawali (Lights, Prosperity)
- Primary: #FF6B00 (Diyo Orange)
- Secondary: #FFD700 (Gold)
- Background: #1A1A2E (Night Blue)
- Text: #FFD700 (Gold)
- Accents: #E91E63 (Rangoli Pink)

### Holi (Colors, Joy)
- Primary: #FF1493 (Pink)
- Secondary: #00BFFF (Blue)
- Background: #FFFFFF (White)
- Text: #4B0082 (Indigo)
- Splash colors: Multi-colored circles

### Nepali New Year
- Primary: #DC143C (Red)
- Secondary: #1E3A8A (National Blue)
- Background: #FEFEFE (White)
- Text: #1E3A8A (Blue)

### Teej (Women's Festival)
- Primary: #DC143C (Red/Sindoor)
- Secondary: #FFD700 (Gold Jewelry)
- Accents: #228B22 (Green Bangles)
- Background: #FFF0F5 (Soft Pink)

## TYPOGRAPHY FOR NEPALI CONTENT

### Nepali (Devanagari) Text:
- Font Family: "Noto Sans Devanagari"
- Main Greeting Size: {heading_size}px (same as heading)
- Supporting Text: {body_size}px

### Common Nepali Greetings:
- Dashain: "विजया दशमीको हार्दिक मंगलमय शुभकामना"
- Tihar: "तिहारको हार्दिक मंगलमय शुभकामना"  
- New Year: "नयाँ वर्ष २०८२ को शुभकामना"
- Saraswoti Puja: "सरस्वती पूजाको शुभकामना"
- Teej: "हरितालिका तीजको शुभकामना"
- Holi: "फागु पूर्णिमाको शुभकामना"

## TOOL CALL FORMAT

```json
{{
  "action": "tool_name",
  "args": {{
    "param1": value1,
    "param2": "value2"
  }}
}}
```

**CRITICAL**: Output ONE tool call, then STOP. Wait for result before continuing.
Do NOT add explanatory text after the JSON block.

## EXAMPLE: Centered Heading Calculation

For canvas {canvas_width}x{canvas_height}, heading "Happy Dashain":
1. Estimate text width: ~12 characters × ~35px/char = 420px
2. Calculate x: ({canvas_width} - 420) / 2 = {example_heading_x}
3. Hero zone center y: {hero_center_y}

```json
{{"action": "add_text", "args": {{"x": {center_x}, "y": {hero_center_y}, "text": "Happy Dashain", "fontSize": {heading_size}, "fontFamily": "Poppins", "fontWeight": "700", "fill": "#8B0000", "textAlign": "center"}}}}
```

## LOCAL BUSINESS DESIGN GUIDELINES

### Dairy Shop:
- Colors: Fresh greens (#2E8B57), white (milk), gold (quality)
- Elements: Milk drop shapes, farm imagery
- Messaging: "Fresh", "Pure", "Daily delivery"

### Sweets Shop:
- Colors: Warm oranges (#FF6B35), gold, red accents
- Elements: Traditional patterns, festive borders
- Messaging: "Traditional taste", "Festival specials"

## STRICT RULES SUMMARY

1. ALWAYS use zone-based positioning
2. ALWAYS calculate coordinates mathematically
3. ALWAYS maintain minimum margins ({margin}px)
4. ALWAYS use consistent spacing ({element_spacing}px between elements)
5. NEVER overlap text with other text
6. NEVER place elements outside canvas bounds
7. NEVER guess positions - calculate them
8. ONE tool call at a time - wait for result
9. Use "textAlign": "center" with x at canvas center for centered text
10. Verify positions mentally before each tool call
"""

# ============================================================================
# DESIGN TOOL RESULT TEMPLATE
# ============================================================================

DESIGN_TOOL_RESULT_TEMPLATE = """Tool: {tool_name}
Result: {output}
{position_info}

Continue with the next design step. Remember to maintain zone-based positioning."""

# ============================================================================
# SCREENSHOT REVIEW PROMPT
# ============================================================================

DESIGN_REVIEW_PROMPT = """Review this canvas design:

Canvas: {canvas_width}x{canvas_height}px | Objects: {object_count}
Composition Style: {composition_style}

User Feedback: {feedback}

## Review Checklist:

### 1. Zone Alignment
- [ ] Header elements in top 15% of canvas
- [ ] Hero content centered in middle zone
- [ ] Footer content in bottom 15%
- [ ] Decorative elements in corners/edges

### 2. Spacing Consistency
- [ ] Edge margins at least {margin}px
- [ ] Consistent gaps between text elements
- [ ] No overlapping content

### 3. Visual Hierarchy
- [ ] Main heading is largest and boldest
- [ ] Subheading clearly secondary
- [ ] Footer text smallest

### 4. Text Readability
- [ ] Sufficient contrast with background
- [ ] Not too close to edges
- [ ] Appropriate font sizes

### 5. Professional Quality
- [ ] Clean, uncluttered layout
- [ ] Balanced visual weight
- [ ] Appropriate color harmony

If improvements needed, make specific tool calls to fix issues.
If design is complete and professional, provide brief confirmation."""

# ============================================================================
# COLOR PALETTES - EXPANDED
# ============================================================================

COLOR_PALETTES = {
    "corporate": {
        "primary": "#2563EB",
        "secondary": "#1E40AF",
        "accent": "#F59E0B",
        "background": "#FFFFFF",
        "surface": "#F8FAFC",
        "text": "#1E293B",
        "text_secondary": "#64748B"
    },
    "modern_dark": {
        "primary": "#3B82F6",
        "secondary": "#8B5CF6",
        "accent": "#10B981",
        "background": "#0F172A",
        "surface": "#1E293B",
        "text": "#F8FAFC",
        "text_secondary": "#94A3B8"
    },
    "minimal": {
        "primary": "#18181B",
        "secondary": "#52525B",
        "accent": "#DC2626",
        "background": "#FAFAFA",
        "surface": "#FFFFFF",
        "text": "#18181B",
        "text_secondary": "#71717A"
    },
    "saraswoti_puja": {
        "primary": "#FFD700",
        "secondary": "#FFFFFF",
        "accent": "#FF6B35",
        "background": "#FFFEF0",
        "surface": "#FFF8DC",
        "text": "#5D4E37",
        "text_secondary": "#8B7355"
    },
    "dashain": {
        "primary": "#DC143C",
        "secondary": "#FFD700",
        "accent": "#228B22",
        "background": "#FFF5F5",
        "surface": "#FFFFFF",
        "text": "#8B0000",
        "text_secondary": "#A0522D"
    },
    "tihar": {
        "primary": "#FF6B00",
        "secondary": "#FFD700",
        "accent": "#E91E63",
        "background": "#1A1A2E",
        "surface": "#16213E",
        "text": "#FFD700",
        "text_secondary": "#FFA500"
    },
    "holi": {
        "primary": "#FF1493",
        "secondary": "#00BFFF",
        "accent": "#FFD700",
        "background": "#FFFFFF",
        "surface": "#FFF0F5",
        "text": "#4B0082",
        "text_secondary": "#8B008B"
    },
    "nepali_new_year": {
        "primary": "#DC143C",
        "secondary": "#1E3A8A",
        "accent": "#FFD700",
        "background": "#FEFEFE",
        "surface": "#F0F4FF",
        "text": "#1E3A8A",
        "text_secondary": "#374151"
    },
    "teej": {
        "primary": "#DC143C",
        "secondary": "#FFD700",
        "accent": "#228B22",
        "background": "#FFF0F5",
        "surface": "#FFE4E1",
        "text": "#8B0000",
        "text_secondary": "#A52A2A"
    },
    "dairy_business": {
        "primary": "#2E8B57",
        "secondary": "#FFFFFF",
        "accent": "#FFD700",
        "background": "#F0FFF0",
        "surface": "#FFFFFF",
        "text": "#1B4332",
        "text_secondary": "#40916C"
    },
    "sweets_shop": {
        "primary": "#FF6B35",
        "secondary": "#FFD700",
        "accent": "#DC143C",
        "background": "#FFF8F0",
        "surface": "#FFFFFF",
        "text": "#8B4513",
        "text_secondary": "#A0522D"
    }
}

# ============================================================================
# FONT RECOMMENDATIONS
# ============================================================================

FONT_RECOMMENDATIONS = {
    "headings_sans": ["Poppins", "Inter", "Montserrat", "Roboto"],
    "headings_serif": ["Playfair Display", "Georgia", "Merriweather"],
    "body": ["Inter", "Roboto", "Open Sans", "Lato"],
    "nepali": ["Noto Sans Devanagari", "Mukta", "Tiro Devanagari Hindi"],
    "display": ["Poppins", "Montserrat", "Raleway"]
}

# ============================================================================
# COMPOSITION TEMPLATES
# ============================================================================

COMPOSITION_TEMPLATES = {
    "festival_greeting": {
        "zones": {
            "header": {"y_start": 0, "y_end": 0.15, "purpose": "Logo, brand"},
            "symbol": {"y_start": 0.15, "y_end": 0.40, "purpose": "Festival imagery"},
            "hero": {"y_start": 0.40, "y_end": 0.70, "purpose": "Main greeting"},
            "blessing": {"y_start": 0.70, "y_end": 0.85, "purpose": "Wishes text"},
            "footer": {"y_start": 0.85, "y_end": 1.0, "purpose": "Brand, contact"}
        },
        "style": "centered"
    },
    "business_promo": {
        "zones": {
            "header": {"y_start": 0, "y_end": 0.20, "purpose": "Logo, brand name"},
            "hero": {"y_start": 0.20, "y_end": 0.50, "purpose": "Offer, promotion"},
            "content": {"y_start": 0.50, "y_end": 0.80, "purpose": "Details, menu"},
            "footer": {"y_start": 0.80, "y_end": 1.0, "purpose": "Contact, CTA"}
        },
        "style": "centered"
    },
    "social_post": {
        "zones": {
            "header": {"y_start": 0, "y_end": 0.12, "purpose": "Brand"},
            "hero": {"y_start": 0.20, "y_end": 0.70, "purpose": "Main message"},
            "footer": {"y_start": 0.85, "y_end": 1.0, "purpose": "CTA, handles"}
        },
        "style": "centered"
    }
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def calculate_typography_sizes(canvas_height: int) -> Dict[str, int]:
    """Calculate typography sizes based on canvas height."""
    base = min(canvas_height, 1080)
    
    if base >= 1080:
        scale = 1.0
    elif base >= 800:
        scale = 0.85
    elif base >= 600:
        scale = 0.7
    else:
        scale = 0.55
    
    return {
        "heading": int(56 * scale),
        "subheading": int(28 * scale),
        "body": int(18 * scale),
        "cta": int(18 * scale),
        "contact": int(14 * scale),
        "small": int(12 * scale)
    }


def calculate_spacing(canvas_width: int, canvas_height: int) -> Dict[str, int]:
    """Calculate spacing values based on canvas size."""
    min_dim = min(canvas_width, canvas_height)
    
    return {
        "margin": int(min_dim * 0.06),
        "section_spacing": int(min_dim * 0.05),
        "element_spacing": int(min_dim * 0.02),
        "text_gap": int(min_dim * 0.04)
    }


def calculate_zones(canvas_width: int, canvas_height: int) -> Dict[str, Dict[str, int]]:
    """Calculate zone boundaries for the canvas."""
    margin = int(min(canvas_width, canvas_height) * 0.06)
    
    return {
        "header": {
            "y_start": margin,
            "y_end": int(canvas_height * 0.15),
            "x_start": margin,
            "x_end": canvas_width - margin
        },
        "hero": {
            "y_start": int(canvas_height * 0.25),
            "y_end": int(canvas_height * 0.70),
            "y_center": int(canvas_height * 0.45),
            "x_start": margin,
            "x_end": canvas_width - margin
        },
        "footer": {
            "y_start": int(canvas_height * 0.85),
            "y_end": canvas_height - margin,
            "x_start": margin,
            "x_end": canvas_width - margin
        }
    }


def get_system_prompt(
    canvas_width: int = 1080,
    canvas_height: int = 1080,
    object_count: int = 0,
    composition_style: str = "centered"
) -> str:
    """Generate the comprehensive system prompt with calculated values."""
    
    # Calculate all values
    typography = calculate_typography_sizes(canvas_height)
    spacing = calculate_spacing(canvas_width, canvas_height)
    zones = calculate_zones(canvas_width, canvas_height)
    
    center_x = canvas_width // 2
    center_y = canvas_height // 2
    
    # Golden ratio calculations
    golden_major_x = int(canvas_width / 1.618)
    golden_minor_x = canvas_width - golden_major_x
    
    # Rule of thirds
    third_x = canvas_width // 3
    two_thirds_x = (canvas_width * 2) // 3
    third_y = canvas_height // 3
    two_thirds_y = (canvas_height * 2) // 3
    
    # Example calculation
    example_heading_x = center_x  # For centered text
    
    # Format composition zones guide
    composition_zones = COMPOSITION_ZONES_GUIDE.format(
        canvas_width=canvas_width,
        canvas_height=canvas_height,
        margin=spacing["margin"],
        header_end=zones["header"]["y_end"],
        hero_start=zones["hero"]["y_start"],
        hero_end=zones["hero"]["y_end"],
        hero_center_y=zones["hero"]["y_center"],
        footer_start=zones["footer"]["y_start"],
        footer_end=zones["footer"]["y_end"],
        center_x=center_x,
        section_spacing=spacing["section_spacing"],
        element_spacing=spacing["element_spacing"]
    )
    
    # Format positioning rules
    positioning_rules = POSITIONING_RULES.format(
        canvas_width=canvas_width,
        canvas_height=canvas_height,
        margin=spacing["margin"],
        golden_major_x=golden_major_x,
        golden_minor_x=golden_minor_x,
        third_x=third_x,
        two_thirds_x=two_thirds_x,
        third_y=third_y,
        two_thirds_y=two_thirds_y
    )
    
    # Format element roles spec
    element_roles = ELEMENT_ROLES_SPEC.format(
        heading_size=typography["heading"],
        subheading_size=typography["subheading"],
        body_size=typography["body"],
        cta_size=typography["cta"],
        contact_size=typography["contact"]
    )
    
    # Format main prompt
    return DESIGN_SYSTEM_PROMPT.format(
        canvas_width=canvas_width,
        canvas_height=canvas_height,
        center_x=center_x,
        center_y=center_y,
        aspect_ratio=round(canvas_width / canvas_height, 2),
        object_count=object_count,
        composition_zones=composition_zones,
        positioning_rules=positioning_rules,
        element_roles=element_roles,
        margin=spacing["margin"],
        element_spacing=spacing["element_spacing"],
        heading_size=typography["heading"],
        subheading_size=typography["subheading"],
        body_size=typography["body"],
        hero_center_y=zones["hero"]["y_center"],
        example_heading_x=example_heading_x
    )


def get_review_prompt(
    canvas_width: int,
    canvas_height: int,
    object_count: int,
    feedback: str = "",
    composition_style: str = "centered"
) -> str:
    """Generate the review prompt for screenshot analysis."""
    spacing = calculate_spacing(canvas_width, canvas_height)
    
    return DESIGN_REVIEW_PROMPT.format(
        canvas_width=canvas_width,
        canvas_height=canvas_height,
        object_count=object_count,
        composition_style=composition_style,
        feedback=feedback or "None provided",
        margin=spacing["margin"]
    )


def get_palette(theme: str = "corporate") -> Dict[str, str]:
    """Get a color palette by theme name."""
    return COLOR_PALETTES.get(theme, COLOR_PALETTES["corporate"])


def get_composition_template(template_name: str) -> Dict[str, Any]:
    """Get a composition template by name."""
    return COMPOSITION_TEMPLATES.get(
        template_name,
        COMPOSITION_TEMPLATES["social_post"]
    )


def get_festival_palette(festival: str) -> Dict[str, str]:
    """Get color palette for a specific Nepali festival."""
    festival_map = {
        "saraswoti": "saraswoti_puja",
        "saraswoti puja": "saraswoti_puja",
        "basanta panchami": "saraswoti_puja",
        "dashain": "dashain",
        "vijaya dashami": "dashain",
        "tihar": "tihar",
        "deepawali": "tihar",
        "diwali": "tihar",
        "holi": "holi",
        "fagu": "holi",
        "new year": "nepali_new_year",
        "naya barsha": "nepali_new_year",
        "teej": "teej",
        "haritalika": "teej"
    }
    
    palette_key = festival_map.get(festival.lower(), "corporate")
    return COLOR_PALETTES.get(palette_key, COLOR_PALETTES["corporate"])


def get_tool_result_message(tool_name: str, output: str, obj_id: str = None) -> str:
    """Format tool result message with position context."""
    position_info = ""
    if obj_id:
        position_info = f"Object ID: {obj_id} - use this ID for modifications"
    
    return DESIGN_TOOL_RESULT_TEMPLATE.format(
        tool_name=tool_name,
        output=output,
        position_info=position_info
    )
