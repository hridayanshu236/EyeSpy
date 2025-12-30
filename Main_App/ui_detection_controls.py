"""
Detection and Playback UI Components
Handles detection model controls and video/camera playback UI
"""

import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
from pathlib import Path
from ui_styles import COLORS, FONTS, SPACING, BUTTON_STYLE, ICONS, apply_hover_effect, create_section_separator


class DetectionControlPanel(tk.Frame):
    """Panel for detection model configuration and controls"""
    
    def __init__(self, parent, callbacks, default_model_path="./weights/bestone.pt"):
        """
        Initialize detection control panel
        
        Args:
            parent: Parent widget
            callbacks: Dictionary with callbacks
                - on_load_detector
                - on_select_source
                - on_sample_frame
                - on_detect_sample
                - on_play
                - on_pause
                - on_stop
                - on_terminate
            default_model_path: Default path to model weights
        """
        super().__init__(parent, bg=COLORS['white'])
        self.callbacks = callbacks
        
        # Section title with elegant background
        title_frame = tk.Frame(self, bg=COLORS['bg_secondary'])
        title_frame.pack(fill=tk.X, padx=0, pady=0)
        
        tk.Label(
            title_frame, 
            text="🔍 Detection & Playback", 
            font=FONTS['subtitle'],
            bg=COLORS['bg_secondary'],
            fg=COLORS['dark'],
            pady=SPACING['sm']
        ).pack(anchor="w", padx=SPACING['md'])
        
        # Model configuration
        self._create_model_config(default_model_path)
        
        # Source selection
        self._create_source_selector()
        
        # Action buttons
        self._create_action_buttons()
        
        # Playback controls
        self._create_playback_controls()
        
        # Source label (shows selected source)
        self.source_label = tk.Label(
            self,
            text="Source: (not selected)",
            font=FONTS['small'],
            bg=COLORS['white'],
            fg='gray',
            anchor='w'
        )
        self.source_label.pack(fill=tk.X, padx=SPACING['md'], pady=SPACING['sm'])
        
        # Top-N detection counter
        self.topn_label = tk.Label(
            self,
            text="Top saved detections: 0/20",
            font=FONTS['small'],
            bg=COLORS['white'],
            fg=COLORS['info'],
            anchor='w'
        )
        self.topn_label.pack(fill=tk.X, padx=SPACING['md'], pady=(SPACING['sm'], 0))
    
    def _create_model_config(self, default_path):
        """Create model configuration section"""
        config_frame = tk.Frame(self, bg=COLORS['white'])
        config_frame.pack(fill=tk.X, padx=SPACING['md'], pady=SPACING['sm'])
        
        # Model path
        path_frame = tk.Frame(config_frame, bg=COLORS['white'])
        path_frame.pack(fill=tk.X, pady=SPACING['xs'])
        
        tk.Label(
            path_frame, 
            text="Weights:", 
            font=FONTS['default'],
            bg=COLORS['white'],
            width=12,
            anchor='w'
        ).pack(side=tk.LEFT)
        
        self.model_path_var = tk.StringVar(value=default_path)
        model_entry = tk.Entry(
            path_frame,
            textvariable=self.model_path_var,
            font=FONTS['default'],
            relief='solid',
            bd=1
        )
        model_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=SPACING['sm'])
        
        load_btn = tk.Button(
            path_frame,
            text="Load",
            command=self.callbacks.get('on_load_detector'),
            font=FONTS['button'],
            bg=COLORS['primary'],
            fg=COLORS['white'],
            **BUTTON_STYLE
        )
        load_btn.pack(side=tk.LEFT)
        apply_hover_effect(load_btn, self._lighten_color(COLORS['primary']), COLORS['primary'])
        
        # Confidence threshold
        conf_frame = tk.Frame(config_frame, bg=COLORS['white'])
        conf_frame.pack(fill=tk.X, pady=SPACING['xs'])
        
        tk.Label(
            conf_frame, 
            text="Conf Threshold:", 
            font=FONTS['default'],
            bg=COLORS['white'],
            width=12,
            anchor='w'
        ).pack(side=tk.LEFT)
        
        self.conf_thresh = tk.DoubleVar(value=0.30)
        conf_spinbox = tk.Spinbox(
            conf_frame,
            from_=0.05,
            to=1.0,
            increment=0.05,
            textvariable=self.conf_thresh,
            format="%.2f",
            width=8,
            font=FONTS['default']
        )
        conf_spinbox.pack(side=tk.LEFT, padx=SPACING['sm'])
    
    def _create_source_selector(self):
        """Create source type selection section"""
        source_frame = tk.Frame(self, bg=COLORS['white'])
        source_frame.pack(fill=tk.X, padx=SPACING['md'], pady=SPACING['md'])
        
        tk.Label(
            source_frame,
            text="Source Type:",
            font=FONTS['default'],
            bg=COLORS['white']
        ).pack(anchor='w', pady=(0, SPACING['sm']))
        
        # Radio buttons in a grid
        radio_frame = tk.Frame(source_frame, bg=COLORS['white'])
        radio_frame.pack(fill=tk.X)
        
        self.source_type = tk.StringVar(value="video_file")
        
        radio_options = [
            ("Image Folder", "image_folder", 0, 0),
            ("Video Folder", "video_folder", 0, 1),
            ("Video File", "video_file", 1, 0),
            ("Camera (realtime)", "camera", 1, 1),
        ]
        
        for text, value, row, col in radio_options:
            rb = tk.Radiobutton(
                radio_frame,
                text=text,
                variable=self.source_type,
                value=value,
                font=FONTS['default'],
                bg=COLORS['white'],
                activebackground=COLORS['white']
            )
            rb.grid(row=row, column=col, sticky='w', padx=SPACING['sm'], pady=SPACING['xs'])
    
    def _create_action_buttons(self):
        """Create action buttons (select, sample, detect)"""
        action_frame = tk.Frame(self, bg=COLORS['white'])
        action_frame.pack(fill=tk.X, padx=SPACING['md'], pady=SPACING['sm'])
        
        btn_container = tk.Frame(action_frame, bg=COLORS['white'])
        btn_container.pack(fill=tk.X)
        
        # Select Path button
        select_btn = tk.Button(
            btn_container,
            text=f"{ICONS['folder']} Select Path",
            command=self.callbacks.get('on_select_source'),
            font=FONTS['button'],
            bg=COLORS['info'],
            fg=COLORS['white'],
            **BUTTON_STYLE
        )
        select_btn.pack(side=tk.LEFT, padx=SPACING['xs'], expand=True, fill=tk.X)
        apply_hover_effect(select_btn, self._lighten_color(COLORS['info']), COLORS['info'])
        
        # Sample Frame button
        sample_btn = tk.Button(
            btn_container,
            text=f"{ICONS['camera']} Sample",
            command=self.callbacks.get('on_sample_frame'),
            font=FONTS['button'],
            bg=COLORS['secondary'],
            fg=COLORS['white'],
            **BUTTON_STYLE
        )
        sample_btn.pack(side=tk.LEFT, padx=SPACING['xs'], expand=True, fill=tk.X)
        apply_hover_effect(sample_btn, self._lighten_color(COLORS['secondary']), COLORS['secondary'])
        
        # Detect button (full width, second row)
        detect_btn = tk.Button(
            action_frame,
            text="🔍 Detect On Sample",
            command=self.callbacks.get('on_detect_sample'),
            font=FONTS['button'],
            bg=COLORS['danger'],
            fg=COLORS['white'],
            **BUTTON_STYLE
        )
        detect_btn.pack(fill=tk.X, pady=(SPACING['sm'], 0))
        apply_hover_effect(detect_btn, self._lighten_color(COLORS['danger']), COLORS['danger'])
    
    def _create_playback_controls(self):
        """Create playback control buttons"""
        playback_frame = tk.Frame(self, bg=COLORS['white'])
        playback_frame.pack(fill=tk.X, padx=SPACING['md'], pady=SPACING['md'])
        
        tk.Label(
            playback_frame,
            text="Playback Controls:",
            font=FONTS['default'],
            bg=COLORS['white']
        ).pack(anchor='w', pady=(0, SPACING['sm']))
        
        btn_frame = tk.Frame(playback_frame, bg=COLORS['white'])
        btn_frame.pack(fill=tk.X)
        
        # Play button
        play_btn = tk.Button(
            btn_frame,
            text=f"{ICONS['play']} Play",
            command=self.callbacks.get('on_play'),
            font=FONTS['button'],
            bg=COLORS['success'],
            fg=COLORS['white'],
            **BUTTON_STYLE
        )
        play_btn.grid(row=0, column=0, padx=SPACING['xs'], pady=SPACING['xs'], sticky='ew')
        apply_hover_effect(play_btn, self._lighten_color(COLORS['success']), COLORS['success'])
        
        # Pause button
        pause_btn = tk.Button(
            btn_frame,
            text=f"{ICONS['pause']} Pause",
            command=self.callbacks.get('on_pause'),
            font=FONTS['button'],
            bg=COLORS['warning'],
            fg=COLORS['white'],
            **BUTTON_STYLE
        )
        pause_btn.grid(row=0, column=1, padx=SPACING['xs'], pady=SPACING['xs'], sticky='ew')
        apply_hover_effect(pause_btn, self._lighten_color(COLORS['warning']), COLORS['warning'])
        
        # Stop button
        stop_btn = tk.Button(
            btn_frame,
            text=f"{ICONS['stop']} Stop",
            command=self.callbacks.get('on_stop'),
            font=FONTS['button'],
            bg=COLORS['btn_warning'],
            fg=COLORS['white'],
            **BUTTON_STYLE
        )
        stop_btn.grid(row=1, column=0, padx=SPACING['xs'], pady=SPACING['xs'], sticky='ew')
        apply_hover_effect(stop_btn, self._lighten_color(COLORS['btn_warning']), COLORS['btn_warning'])
        
        # Terminate button
        terminate_btn = tk.Button(
            btn_frame,
            text="⛔ Terminate",
            command=self.callbacks.get('on_terminate'),
            font=FONTS['button'],
            bg=COLORS['danger'],
            fg=COLORS['white'],
            **BUTTON_STYLE
        )
        terminate_btn.grid(row=1, column=1, padx=SPACING['xs'], pady=SPACING['xs'], sticky='ew')
        apply_hover_effect(terminate_btn, self._lighten_color(COLORS['danger']), COLORS['danger'])
        
        # Configure grid
        btn_frame.columnconfigure(0, weight=1)
        btn_frame.columnconfigure(1, weight=1)
    
    def _lighten_color(self, hex_color, factor=0.85):
        """Lighten a hex color for hover effect"""
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
    
    def update_source_label(self, text):
        """Update the source label text"""
        self.source_label.config(text=text)
    
    def update_topn_label(self, current, total):
        """Update top-N detection counter"""
        self.topn_label.config(text=f"Top saved detections: {current}/{total}")
    
    def get_model_path(self):
        """Get current model path"""
        return self.model_path_var.get().strip()
    
    def get_conf_threshold(self):
        """Get current confidence threshold"""
        return float(self.conf_thresh.get())
    
    def get_source_type(self):
        """Get selected source type"""
        return self.source_type.get()
