# Module Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         image_tagger_ui.py (Main)                           │
│                     Orchestrates all components                             │
└───────────────────────┬─────────────────────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┬───────────────────┐
        │               │               │                   │
        ▼               ▼               ▼                   ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  ui_styles   │ │ ui_student   │ │ui_detection  │ │  playback    │
│              │ │  _controls   │ │  _controls   │ │  _manager    │
│ • Colors     │ │              │ │              │ │              │
│ • Fonts      │ │ Student Mgmt │ │ Detection UI │ │ Video/Camera │
│ • Spacing    │ │ Panel        │ │ Panel        │ │ Threading    │
│ • Constants  │ │              │ │              │ │              │
│ • Utilities  │ │ File Ops     │ │ Playback     │ │ Frame Queue  │
│              │ │ Panel        │ │ Controls     │ │              │
└──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘
                                                    
        │                                                   │
        │                                                   │
        ▼                                                   ▼
┌──────────────┐                                   ┌──────────────┐
│ detection    │                                   │ Frame        │
│ _processor   │                                   │ Sampler      │
│              │                                   │              │
│ • Top-N Heap │                                   │ Sample from: │
│ • File Save  │                                   │ - Images     │
│ • CSV Log    │                                   │ - Videos     │
│ • Per-student│                                   │ - Camera     │
│   Tracking   │                                   │              │
└──────────────┘                                   └──────────────┘
```

## Data Flow

### Student Management Flow
```
User Action (Add/Edit/Delete Student)
        │
        ▼
StudentControlPanel (ui_student_controls.py)
        │
        ▼
Callback to Main App (image_tagger_ui.py)
        │
        ▼
Update Mapper (Mapper.py)
        │
        ▼
Refresh UI Lists & Canvas
```

### Detection Flow (Sample Frame)
```
User clicks "Sample Frame"
        │
        ▼
DetectionControlPanel (ui_detection_controls.py)
        │
        ▼
FrameSampler.sample_from_*() (playback_manager.py)
        │
        ▼
Main App receives frame
        │
        ▼
Display on Canvas (canvas_manager.py)
        │
        ▼
User clicks "Detect On Sample"
        │
        ▼
CheatDetector.detect_frame() (cheat_detector.py)
        │
        ▼
DetectionProcessor.save_sample_detection() (detection_processor.py)
        │
        ▼
Files saved, CSV logged, UI updated
```

### Playback Flow (Video/Camera)
```
User clicks "Play"
        │
        ▼
DetectionControlPanel callback
        │
        ▼
PlaybackManager.start_playback() (playback_manager.py)
        │
        ▼
Worker Thread starts
        │
        ├─> Read frames
        │   │
        │   ▼
        │   Run detection (CheatDetector)
        │   │
        │   ▼
        │   Queue frame + detections
        │
        ▼
Main thread polls queue (every 30ms)
        │
        ▼
Process detections (DetectionProcessor)
        │
        ├─> Top-N heap management
        │   ├─> Save best frames per student
        │   └─> Auto-prune lower confidence
        │
        ▼
Update Canvas & UI
```

## Component Responsibilities

### UI Layer (Presentation)
```
┌─────────────────────────────────────────┐
│ ui_styles.py                            │
│ • Visual constants                      │
│ • No business logic                     │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ ui_student_controls.py                  │
│ • Student UI components                 │
│ • File operation UI                     │
│ • Delegates actions via callbacks       │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ ui_detection_controls.py                │
│ • Detection UI components               │
│ • Playback UI controls                  │
│ • Source selection UI                   │
│ • Delegates actions via callbacks       │
└─────────────────────────────────────────┘
```

### Business Logic Layer
```
┌─────────────────────────────────────────┐
│ playback_manager.py                     │
│ • Thread management                     │
│ • Frame queue handling                  │
│ • Playback state control                │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ detection_processor.py                  │
│ • Detection processing                  │
│ • Top-N heap algorithm                  │
│ • File I/O (frames & logs)              │
│ • Per-student tracking                  │
└─────────────────────────────────────────┘
```

### Orchestration Layer
```
┌─────────────────────────────────────────┐
│ image_tagger_ui.py                      │
│ • Coordinates all modules               │
│ • Event handling                        │
│ • Canvas management                     │
│ • Student mapping                       │
│ • Main application loop                 │
└─────────────────────────────────────────┘
```

### Existing Modules (Unchanged)
```
┌──────────────┬──────────────┬──────────────┐
│ Mapper.py    │ Student.py   │ cheat_       │
│              │              │ detector.py  │
│ Coordinate   │ Student      │ Detection    │
│ mapping      │ model        │ model        │
└──────────────┴──────────────┴──────────────┘

┌──────────────┬──────────────┬──────────────┐
│ canvas_      │ list_        │ dialogs.py   │
│ manager.py   │ manager.py   │              │
│ Canvas ops   │ List widgets │ Dialog boxes │
└──────────────┴──────────────┴──────────────┘

┌──────────────┬──────────────┐
│ file_        │ export_      │
│ manager.py   │ csv.py       │
│ Load/Save    │ CSV export   │
└──────────────┴──────────────┘
```

## Benefits of This Architecture

### ✅ Separation of Concerns
- UI code separate from business logic
- Easy to change visuals without touching logic
- Easy to change logic without touching UI

### ✅ Testability
- Each module can be tested independently
- Mock dependencies easily
- Unit tests are straightforward

### ✅ Maintainability
- Changes localized to specific modules
- Clear module boundaries
- Self-documenting structure

### ✅ Reusability
- UI components can be reused
- Business logic modules portable
- Utilities can be shared

### ✅ Extensibility
- Add new UI components easily
- Extend business logic without UI changes
- Plugin-style architecture

## Callback Pattern

All UI modules use callbacks for decoupling:

```python
# UI Component
StudentControlPanel(
    parent,
    callbacks={
        'on_add_student': self.open_add_student_dialog,
        'on_edit_student': self.edit_student_ui,
        # ...
    }
)

# UI module calls callback when user acts
def _on_button_click(self):
    self.callbacks.get('on_add_student', lambda: None)()
```

This allows:
- UI components don't know about main app
- Easy to swap implementations
- Clean testing (provide mock callbacks)

## Threading Model

```
┌─────────────────────────────────────────────────────┐
│                   Main Thread                       │
│                                                     │
│  ┌──────────────┐     ┌──────────────┐            │
│  │ UI Updates   │◄────┤ Queue Poll   │            │
│  │ (tkinter)    │     │ (30ms)       │            │
│  └──────────────┘     └──────────────┘            │
│          ▲                    ▲                     │
│          │                    │                     │
│          │            ┌───────┴────────┐           │
│          │            │  Frame Queue   │           │
│          │            │  (maxsize=4)   │           │
│          │            └───────┬────────┘           │
└──────────┼────────────────────┼────────────────────┘
           │                    │
           │                    │
┌──────────┼────────────────────┼────────────────────┐
│          │        Worker Thread                    │
│          │                    │                     │
│  ┌───────┴────────┐   ┌───────▼────────┐          │
│  │  Detection     │   │  Frame Read    │          │
│  │  Processing    │   │  & Detection   │          │
│  └────────────────┘   └────────────────┘          │
│                                                     │
└─────────────────────────────────────────────────────┘
```

- Main thread: UI updates only
- Worker thread: Heavy processing
- Queue: Safe communication between threads
