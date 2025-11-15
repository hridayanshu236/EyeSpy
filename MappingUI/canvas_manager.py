import tkinter as tk
from PIL import Image, ImageTk

class CanvasManager:
    """
    Handles the canvas, image drawing, markers and low-level events.
    Higher-level behavior uses callbacks passed to bind_left_click and bind_right_click.
    """
    def __init__(self, parent_frame, pil_image, cursor="crosshair"):
        self.parent_frame = parent_frame
        self.pil_image = pil_image
        self.tk_image = ImageTk.PhotoImage(self.pil_image)
        self.canvas = tk.Canvas(self.parent_frame, width=self.pil_image.width, height=self.pil_image.height, bg="gray", cursor=cursor)
        self.canvas.pack(expand=True, padx=5, pady=5)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)
        self._left_click_cb = None
        self._right_click_cb = None
        self.canvas.bind("<Button-1>", self._on_left_click)
        self.canvas.bind("<Button-3>", self._on_right_click)
        self.canvas.bind("<Motion>", self._on_motion)
        # Tooltip label
        self.tooltip = tk.Label(self.canvas, bg="yellow", font=("Arial", 9, "bold"), bd=2, relief=tk.SOLID, padx=5, pady=2)
        self.tooltip.place_forget()

    def _on_left_click(self, event):
        if self._left_click_cb:
            self._left_click_cb(event.x, event.y)

    def _on_right_click(self, event):
        if self._right_click_cb:
            self._right_click_cb(event.x, event.y)

    def _on_motion(self, event):
        self.tooltip.place(x=event.x + 15, y=event.y + 15)
        self.tooltip.config(text=f"X: {event.x}, Y: {event.y}")

    def bind_left_click(self, callback):
        self._left_click_cb = callback

    def bind_right_click(self, callback):
        self._right_click_cb = callback

    # Drawing helpers
    def draw_marker(self, x, y, label, tag="marker"):
        self.canvas.create_oval(x-5, y-5, x+5, y+5, fill="red", outline="white", width=2, tags=tag)
        self.canvas.create_text(x+15, y, text=label, font=("Arial", 9, "bold"), fill="yellow", anchor=tk.W, tags=tag)

    def clear_markers(self, tag="marker"):
        self.canvas.delete(tag)

    def redraw_all_markers(self, mapped_students, mapped_student_objects, tag="marker"):
        self.clear_markers(tag=tag)
        for roll, (x, y) in mapped_students.items():
            stu = mapped_student_objects.get(roll)
            if stu:
                self.draw_marker(x, y, stu.name, tag=tag)