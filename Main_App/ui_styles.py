"""
UI Styles and Constants for Image Tagger Application
Centralized styling configuration for consistent appearance
"""

# Color Palette - Elegant and Professional
COLORS = {
    'primary': '#4F46E5',      # Indigo
    'secondary': '#059669',    # Emerald
    'danger': '#DC2626',       # Red
    'warning': '#D97706',      # Amber
    'info': '#0891B2',         # Cyan
    'success': '#10B981',      # Green
    'light': '#F9FAFB',        # Very Light Gray
    'dark': '#111827',         # Very Dark Gray
    'white': '#FFFFFF',
    'border': '#E5E7EB',
    'accent': '#8B5CF6',       # Purple accent
    'bg_secondary': '#F3F4F6', # Secondary background
    
    # Button specific - more vibrant and elegant
    'btn_add': '#10B981',
    'btn_edit': '#F59E0B',
    'btn_delete': '#DC2626',
    'btn_info': '#4F46E5',
    'btn_success': '#059669',
    'btn_warning': '#D97706',
}

# Fonts
FONTS = {
    'default': ("Segoe UI", 10),
    'title': ("Segoe UI", 12, "bold"),
    'subtitle': ("Segoe UI", 11, "bold"),
    'small': ("Segoe UI", 9),
    'large': ("Segoe UI", 11),
    'button': ("Segoe UI", 9),
    'status': ("Segoe UI", 9),
}

# Padding and Spacing - More compact
SPACING = {
    'xs': 1,
    'sm': 3,
    'md': 6,
    'lg': 9,
    'xl': 12,
}

# Widget Styles - More elegant
BUTTON_STYLE = {
    'relief': 'flat',
    'bd': 0,
    'padx': 10,
    'pady': 5,
    'cursor': 'hand2',
}

ENTRY_STYLE = {
    'relief': 'solid',
    'bd': 1,
}

FRAME_STYLE = {
    'relief': 'flat',
    'bd': 1,
}

LABEL_STYLE = {
    'anchor': 'w',
    'padx': 4,
    'pady': 2,
}

# Emojis for modern look
ICONS = {
    'add': '➕',
    'edit': '✏️',
    'delete': '🗑️',
    'save': '💾',
    'load': '📂',
    'import': '📥',
    'export': '📤',
    'clear': '🔄',
    'remove': '🧾',
    'play': '▶',
    'pause': '⏸',
    'stop': '⏹',
    'camera': '📹',
    'folder': '📁',
    'search': '🔍',
}


WINDOW = {
    'min_width': 1200,
    'min_height': 700,
    'default_width': 1600,
    'default_height': 900,
    'canvas_min_width': 800,
    'sidebar_min_width': 370,
    'sidebar_max_width': 400,
}


CANVAS = {
    'fit_width': 1100,
    'fit_height': 850,
    'bg': COLORS['light'],
}

def apply_hover_effect(widget, enter_bg, leave_bg):
    """Apply hover effect to widget"""
    def on_enter(e):
        widget['background'] = enter_bg
    
    def on_leave(e):
        widget['background'] = leave_bg
    
    widget.bind("<Enter>", on_enter)
    widget.bind("<Leave>", on_leave)

def create_section_separator(parent, **kwargs):
    """Create a visual separator between sections"""
    import tkinter as tk
    sep = tk.Frame(parent, height=1, bg=COLORS['border'], **kwargs)
    sep.pack(fill=tk.X, pady=SPACING['sm'])
    return sep

def create_elegant_frame(parent, **kwargs):
    """Create an elegant frame with subtle styling"""
    import tkinter as tk
    frame = tk.Frame(
        parent, 
        bg=COLORS['white'],
        relief=tk.FLAT,
        bd=0,
        **kwargs
    )
    return frame
