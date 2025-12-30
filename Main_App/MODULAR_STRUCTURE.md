# Image Tagger UI - Modular Structure

## Overview
The Image Tagger UI has been refactored into a modular, maintainable architecture with improved visual design and proper window sizing.

## Module Structure

### 1. **ui_styles.py** - UI Styling & Constants
Contains all styling constants, colors, fonts, and layout configurations.

**Features:**
- Modern color palette with professional appearance
- Centralized font definitions
- Layout constants (window sizes, spacing, etc.)
- Utility functions for hover effects and separators

**Key Exports:**
- `COLORS` - Color palette dictionary
- `FONTS` - Font configurations
- `WINDOW` - Window sizing constants
- `SPACING` - Padding/margin values
- `ICONS` - Emoji icons for buttons

---

### 2. **ui_student_controls.py** - Student Management UI
Contains all student-related UI components.

**Classes:**
- `StudentControlPanel` - Panel with student management buttons, search, and mapping tools
- `FileOperationsPanel` - Panel for save/load/import/export operations

**Features:**
- Modern button styling with hover effects
- Search/filter functionality for students
- Organized grid layout for buttons
- Callback-based architecture for separation of concerns

---

### 3. **ui_detection_controls.py** - Detection & Playback UI
Contains detection model and playback control UI components.

**Classes:**
- `DetectionControlPanel` - Complete panel for detection configuration and playback

**Features:**
- Model weights configuration
- Confidence threshold adjustment
- Source type selection (image folder, video, camera)
- Playback controls (play, pause, stop, terminate)
- Real-time status display

---

### 4. **playback_manager.py** - Video/Camera Playback
Manages video and camera playback in a separate thread.

**Classes:**
- `PlaybackManager` - Handles threaded playback and frame queuing
- `FrameSampler` - Utility for sampling single frames from various sources

**Features:**
- Non-blocking playback with queue management
- Support for video files, video folders, and cameras
- Pause/resume functionality
- Graceful shutdown

---

### 5. **detection_processor.py** - Detection Processing
Handles detection processing, top-N tracking, and file saving.

**Classes:**
- `DetectionProcessor` - Processes detections and maintains top-N heap

**Features:**
- Top-N detection tracking with automatic pruning
- Per-student frame saving with configurable limits
- Time-gap enforcement between saves
- CSV logging of all detections
- Organized output folder structure

---

### 6. **image_tagger_ui.py** - Main Application
Refactored main application class that orchestrates all modules.

**Key Improvements:**
- Clean separation of concerns
- Proper window initialization (1600x900, min 1200x700)
- Scrollable right panel for all controls
- Modern UI with consistent styling
- Improved status messages with icons
- Better error handling

---

## File Organization

```
Main_App/
├── image_tagger_ui.py           # Main application (refactored)
├── image_tagger_ui_backup.py    # Original backup
│
├── ui_styles.py                 # UI styling constants
├── ui_student_controls.py       # Student management UI
├── ui_detection_controls.py     # Detection/playback UI
├── playback_manager.py          # Playback threading
├── detection_processor.py       # Detection processing
│
├── canvas_manager.py            # Canvas operations (existing)
├── list_manager.py              # List widgets (existing)
├── dialogs.py                   # Dialog boxes (existing)
├── file_manager.py              # File I/O (existing)
├── export_csv.py                # CSV export (existing)
├── Mapper.py                    # Coordinate mapping (existing)
├── Student.py                   # Student model (existing)
└── cheat_detector.py            # Detection model (existing)
```

---

## Key Improvements

### 1. **Modularity**
- Each module has a single, well-defined responsibility
- Easy to maintain and extend
- Reusable components

### 2. **UI/UX Enhancements**
- Modern color scheme (blues, greens, professional grays)
- Hover effects on buttons
- Icons for better visual recognition
- Proper spacing and padding
- Scrollable control panel
- Better status messages with checkmarks and icons

### 3. **Window Sizing**
- Default size: 1600x900 (everything visible without resize)
- Minimum size: 1200x700
- Responsive layout with paned window
- Canvas fits optimally in available space

### 4. **Better Organization**
- Callbacks instead of tight coupling
- Separation of UI logic from business logic
- Clear module boundaries
- Consistent naming conventions

---

## Usage

### Running the Application
```python
python image_tagger_ui.py
```

### Keyboard Shortcuts
- `Ctrl+S` - Save project
- `Ctrl+O` - Load project
- `Ctrl+I` - Import from CSV
- `Ctrl+E` - Export to CSV
- `Ctrl+N` - Add new student
- `Delete` - Remove selected mapping

---

## Customization

### Changing Colors
Edit `ui_styles.py` and modify the `COLORS` dictionary:
```python
COLORS = {
    'primary': '#2563eb',   # Change to your preferred color
    'secondary': '#10b981',
    # ...
}
```

### Adjusting Window Size
Edit `ui_styles.py` and modify the `WINDOW` dictionary:
```python
WINDOW = {
    'default_width': 1600,  # Change default width
    'default_height': 900,  # Change default height
    # ...
}
```

### Modifying Top-N Settings
Edit constants in `image_tagger_ui.py`:
```python
TOP_N = 20  # Number of top detections to keep
```

Or when creating DetectionProcessor:
```python
self.detection_processor = DetectionProcessor(
    max_entries_per_person=50,  # Max frames per student
    save_gap_seconds=2,         # Min seconds between saves
    # ...
)
```

---

## Architecture Benefits

1. **Testability** - Each module can be tested independently
2. **Maintainability** - Changes localized to specific modules
3. **Extensibility** - Easy to add new features
4. **Readability** - Clear code organization
5. **Reusability** - Components can be reused in other projects

---

## Migration Notes

The original `image_tagger_ui.py` has been backed up as `image_tagger_ui_backup.py`. All functionality has been preserved and enhanced in the refactored version.

---

## Future Enhancements

Potential areas for future improvement:
- Add dark mode support
- Implement user preferences/settings persistence
- Add more detection visualization options
- Create unit tests for each module
- Add logging framework
- Implement undo/redo functionality
