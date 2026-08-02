# %%
# The readablecode "terminal navy" design system (dotfiles design/STYLE.md,
# tokens in design/tokens.css) as Python constants, so every TUI/web surface
# pulls the same palette from one place instead of carrying drifting copies.

# %%
# Tokens #

BG = "#0d1420"
SURFACE = "#121b2a"
SURFACE_2 = "#182333"
HAIRLINE = "#273141"  # --border rgba(148,163,184,.16) flattened onto --surface
GRID = "#1c2739"
INK = "#dbe4f0"
INK_2 = "#9fb0c3"
MUTED = "#7d8b9e"
GREEN = "#2ea043"
GREEN_BRIGHT = "#56d364"
AMBER = "#b8860b"
AMBER_BRIGHT = "#e3b341"
RED = "#f87171"


# %%
# Textual theme (textual imported lazily - only TUI callers need it) #


def terminal_navy_textual_theme():
    """The terminal-navy palette as a Textual Theme, ready to register."""
    from textual.theme import Theme

    return Theme(
        name="terminal-navy",
        primary=GREEN,
        secondary=AMBER,
        accent=GREEN_BRIGHT,
        warning=AMBER_BRIGHT,
        error=RED,
        success=GREEN,
        foreground=INK,
        background=BG,
        surface=SURFACE,
        panel=SURFACE_2,
        dark=True,
        variables={
            "border": GREEN,
            "border-blurred": HAIRLINE,
            "footer-key-foreground": GREEN_BRIGHT,
            "block-cursor-foreground": INK,
            "block-cursor-background": GRID,
            "block-cursor-blurred-foreground": INK_2,
            "block-cursor-blurred-background": SURFACE_2,
            "block-hover-background": SURFACE_2,
            "input-selection-background": f"{GREEN} 35%",
        },
    )


# %%
