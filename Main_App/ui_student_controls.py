"""
Student Management UI Components
Handles all student-related UI controls and interactions
"""

import tkinter as tk
from tkinter import messagebox
from ui_styles import COLORS, FONTS, SPACING, BUTTON_STYLE, ICONS, apply_hover_effect, create_section_separator


class StudentControlPanel(tk.Frame):
    """Panel containing all student management controls"""
    
    def __init__(self, parent, callbacks):
        """
        Initialize student control panel
        
        Args:
            parent: Parent widget
            callbacks: Dictionary with callbacks for various actions
                - on_add_student
                - on_edit_student
                - on_remove_student
                - on_clear_mappings
                - on_remove_selected_mapping
                - on_search_changed
        """
        super().__init__(parent, bg=COLORS['white'])
        self.callbacks = callbacks
        
        # Counter label at top with elegant background
        counter_frame = tk.Frame(self, bg=COLORS['bg_secondary'])
        counter_frame.pack(fill=tk.X, padx=0, pady=0)
        
        self.counts_label = tk.Label(
            counter_frame, 
            text="Unmapped: 0 | Mapped: 0", 
            font=FONTS['small'],
            bg=COLORS['bg_secondary'],
            fg=COLORS['dark'],
            pady=SPACING['sm']
        )
        self.counts_label.pack(fill=tk.X, padx=SPACING['md'])
        
        # Search section
        self._create_search_section()
        
        create_section_separator(self)
        
        # Student management section
        self._create_student_management_section()
        
        create_section_separator(self)
        
        # Mapping tools section
        self._create_mapping_tools_section()
        
    def _create_search_section(self):
        """Create search/filter section"""
        search_frame = tk.Frame(self, bg=COLORS['white'])
        search_frame.pack(fill=tk.X, padx=SPACING['md'], pady=SPACING['sm'])
        
        # Search label with icon
        tk.Label(
            search_frame, 
            text=f"{ICONS['search']} Search Unmapped:", 
            font=FONTS['default'],
            bg=COLORS['white']
        ).pack(side=tk.LEFT)
        
        # Search entry
        self.search_var = tk.StringVar()
        search_entry = tk.Entry(
            search_frame, 
            textvariable=self.search_var, 
            font=FONTS['default'],
            relief='solid',
            bd=1
        )
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=SPACING['md'])
        search_entry.bind("<KeyRelease>", lambda e: self.callbacks.get('on_search_changed', lambda: None)())
        
        # Clear button
        clear_btn = tk.Button(
            search_frame,
            text="Clear",
            command=self._clear_search,
            font=FONTS['button'],
            bg=COLORS['light'],
            **BUTTON_STYLE
        )
        clear_btn.pack(side=tk.LEFT, padx=SPACING['sm'])
        apply_hover_effect(clear_btn, COLORS['border'], COLORS['light'])
        
    def _clear_search(self):
        """Clear search field"""
        self.search_var.set("")
        self.callbacks.get('on_search_changed', lambda: None)()
    
    def _create_student_management_section(self):
        """Create student management buttons"""
        section = tk.Frame(self, bg=COLORS['white'])
        section.pack(fill=tk.X, padx=SPACING['md'], pady=SPACING['sm'])
        
        # Section title with border
        title_frame = tk.Frame(section, bg=COLORS['bg_secondary'], relief=tk.FLAT)
        title_frame.pack(fill=tk.X, pady=(0, SPACING['sm']))
        
        tk.Label(
            title_frame, 
            text="Student Management", 
            font=FONTS['subtitle'],
            bg=COLORS['bg_secondary'],
            fg=COLORS['dark'],
            pady=SPACING['sm']
        ).pack(anchor="w", padx=SPACING['sm'])
        
        # Buttons in a grid for better layout
        btn_frame = tk.Frame(section, bg=COLORS['white'])
        btn_frame.pack(fill=tk.X)
        
        # Add button
        add_btn = self._create_styled_button(
            btn_frame,
            text=f"{ICONS['add']} Add",
            command=self.callbacks.get('on_add_student'),
            bg=COLORS['btn_add'],
            fg=COLORS['white']
        )
        add_btn.grid(row=0, column=0, padx=SPACING['xs'], pady=SPACING['xs'], sticky='ew')
        
        # Edit button
        edit_btn = self._create_styled_button(
            btn_frame,
            text=f"{ICONS['edit']} Edit",
            command=self.callbacks.get('on_edit_student'),
            bg=COLORS['btn_edit'],
            fg=COLORS['white']
        )
        edit_btn.grid(row=0, column=1, padx=SPACING['xs'], pady=SPACING['xs'], sticky='ew')
        
        # Remove button
        remove_btn = self._create_styled_button(
            btn_frame,
            text=f"{ICONS['delete']} Remove",
            command=self.callbacks.get('on_remove_student'),
            bg=COLORS['btn_delete'],
            fg=COLORS['white']
        )
        remove_btn.grid(row=1, column=0, columnspan=2, padx=SPACING['xs'], pady=SPACING['xs'], sticky='ew')
        
        # Configure grid weights for equal column width
        btn_frame.columnconfigure(0, weight=1)
        btn_frame.columnconfigure(1, weight=1)
    
    def _create_mapping_tools_section(self):
        """Create mapping tools buttons"""
        section = tk.Frame(self, bg=COLORS['white'])
        section.pack(fill=tk.X, padx=SPACING['md'], pady=SPACING['sm'])
        
        # Section title with border
        title_frame = tk.Frame(section, bg=COLORS['bg_secondary'], relief=tk.FLAT)
        title_frame.pack(fill=tk.X, pady=(0, SPACING['sm']))
        
        tk.Label(
            title_frame, 
            text="Mapping Tools", 
            font=FONTS['subtitle'],
            bg=COLORS['bg_secondary'],
            fg=COLORS['dark'],
            pady=SPACING['sm']
        ).pack(anchor="w", padx=SPACING['sm'])
        
        btn_frame = tk.Frame(section, bg=COLORS['white'])
        btn_frame.pack(fill=tk.X)
        
        # Clear all mappings
        clear_all_btn = self._create_styled_button(
            btn_frame,
            text=f"{ICONS['clear']} Clear All",
            command=self.callbacks.get('on_clear_mappings'),
            bg=COLORS['danger'],
            fg=COLORS['white']
        )
        clear_all_btn.pack(fill=tk.X, pady=SPACING['xs'])
        
        # Remove selected mapping
        remove_map_btn = self._create_styled_button(
            btn_frame,
            text=f"{ICONS['remove']} Remove Selected",
            command=self.callbacks.get('on_remove_selected_mapping'),
            bg=COLORS['warning'],
            fg=COLORS['white']
        )
        remove_map_btn.pack(fill=tk.X, pady=SPACING['xs'])
    
    def _create_styled_button(self, parent, text, command, bg, fg='black'):
        """Create a styled button with hover effect"""
        btn = tk.Button(
            parent,
            text=text,
            command=command,
            font=FONTS['button'],
            bg=bg,
            fg=fg,
            **BUTTON_STYLE
        )
        
        # Calculate lighter color for hover
        hover_bg = self._lighten_color(bg)
        apply_hover_effect(btn, hover_bg, bg)
        
        return btn
    
    def _lighten_color(self, hex_color, factor=0.9):
        """Lighten a hex color"""
        # Simple lighten - in production, use proper color manipulation
        try:
            r = int(hex_color[1:3], 16)
            g = int(hex_color[3:5], 16)
            b = int(hex_color[5:7], 16)
            
            r = min(255, int(r + (255 - r) * (1 - factor)))
            g = min(255, int(g + (255 - g) * (1 - factor)))
            b = min(255, int(b + (255 - b) * (1 - factor)))
            
            return f'#{r:02x}{g:02x}{b:02x}'
        except:
            return hex_color
    
    def update_counts(self, unmapped, mapped):
        """Update the count label"""
        self.counts_label.config(text=f"Unmapped: {unmapped} | Mapped: {mapped}")
    
    def get_search_query(self):
        """Get current search query"""
        return self.search_var.get().strip().lower()


class FileOperationsPanel(tk.Frame):
    """Panel for file operations (save, load, import, export)"""
    
    def __init__(self, parent, callbacks):
        """
        Initialize file operations panel
        
        Args:
            parent: Parent widget
            callbacks: Dictionary with callbacks for file operations
                - on_save
                - on_load
                - on_import_csv
                - on_export_csv
        """
        super().__init__(parent, bg=COLORS['white'])
        self.callbacks = callbacks
        
        # Section title with border
        title_frame = tk.Frame(self, bg=COLORS['bg_secondary'], relief=tk.FLAT)
        title_frame.pack(fill=tk.X, padx=0, pady=0)
        
        tk.Label(
            title_frame, 
            text="File Operations", 
            font=FONTS['subtitle'],
            bg=COLORS['bg_secondary'],
            fg=COLORS['dark'],
            pady=SPACING['sm']
        ).pack(anchor="w", padx=SPACING['md'])
        
        btn_frame = tk.Frame(self, bg=COLORS['white'])
        btn_frame.pack(fill=tk.X, padx=SPACING['md'])
        
        # Save and Load in first row
        save_btn = self._create_styled_button(
            btn_frame,
            text=f"{ICONS['save']} Save",
            command=self.callbacks.get('on_save'),
            bg=COLORS['info'],
            fg=COLORS['white']
        )
        save_btn.grid(row=0, column=0, padx=SPACING['xs'], pady=SPACING['xs'], sticky='ew')
        
        load_btn = self._create_styled_button(
            btn_frame,
            text=f"{ICONS['load']} Load",
            command=self.callbacks.get('on_load'),
            bg=COLORS['info'],
            fg=COLORS['white']
        )
        load_btn.grid(row=0, column=1, padx=SPACING['xs'], pady=SPACING['xs'], sticky='ew')
        
        # Import and Export in second row
        import_btn = self._create_styled_button(
            btn_frame,
            text=f"{ICONS['import']} Import CSV",
            command=self.callbacks.get('on_import_csv'),
            bg=COLORS['success'],
            fg=COLORS['white']
        )
        import_btn.grid(row=1, column=0, padx=SPACING['xs'], pady=SPACING['xs'], sticky='ew')
        
        export_btn = self._create_styled_button(
            btn_frame,
            text=f"{ICONS['export']} Export CSV",
            command=self.callbacks.get('on_export_csv'),
            bg=COLORS['success'],
            fg=COLORS['white']
        )
        export_btn.grid(row=1, column=1, padx=SPACING['xs'], pady=SPACING['xs'], sticky='ew')
        
        # Configure grid
        btn_frame.columnconfigure(0, weight=1)
        btn_frame.columnconfigure(1, weight=1)
    
    def _create_styled_button(self, parent, text, command, bg, fg='black'):
        """Create a styled button with hover effect"""
        btn = tk.Button(
            parent,
            text=text,
            command=command,
            font=FONTS['button'],
            bg=bg,
            fg=fg,
            **BUTTON_STYLE
        )
        
        # Calculate lighter color for hover
        hover_bg = self._lighten_color(bg)
        apply_hover_effect(btn, hover_bg, bg)
        
        return btn
    
    def _lighten_color(self, hex_color, factor=0.9):
        """Lighten a hex color"""
        try:
            r = int(hex_color[1:3], 16)
            g = int(hex_color[3:5], 16)
            b = int(hex_color[5:7], 16)
            
            r = min(255, int(r + (255 - r) * (1 - factor)))
            g = min(255, int(g + (255 - g) * (1 - factor)))
            b = min(255, int(b + (255 - b) * (1 - factor)))
            
            return f'#{r:02x}{g:02x}{b:02x}'
        except:
            return hex_color
