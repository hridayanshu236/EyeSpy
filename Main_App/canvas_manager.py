import tkinter as tk
from PIL import Image, ImageTk

class CanvasManager:
    """
    Canvas manager with coordinate-scaling utilities.
    - Keeps pil_image (original)
    - Shows a scaled image on the canvas
    - Provides conversion between display coords and image coords
    - Draws markers and detection overlays in display coordinates
    """

    def __init__(self, parent_frame, pil_image, cursor="crosshair", fit_within=(1000, 800)):
        self.parent_frame = parent_frame
        self.pil_image = pil_image.copy()
        self.fit_within = fit_within  # (max_width, max_height)

        # computed transform params (scale for x and y, offsets)
        self.scale = (1.0, 1.0)
        self.offset_x = 0
        self.offset_y = 0
        self.display_w = self.pil_image.width
        self.display_h = self.pil_image.height

        # create canvas and set image
        self._create_canvas()
        self._set_tk_image(self.pil_image)
        self.image_id = None
        self.marker_tag = "marker"
        self.det_tag = "detection"
        self.flag_tag = "flag"
        self.set_image(self.pil_image)

        # callbacks
        self._left_click_cb = None
        self._right_click_cb = None
        self.canvas.bind("<Button-1>", self._on_left_click)
        self.canvas.bind("<Button-3>", self._on_right_click)
        self.canvas.bind("<Motion>", self._on_motion)

        # Tooltip label
        self.tooltip = tk.Label(self.canvas, bg="yellow", font=("Arial", 9, "bold"), bd=2, relief=tk.SOLID, padx=5, pady=2)
        self.tooltip.place_forget()

        # tags used to group drawn items (ensure they exist)
        

    def _create_canvas(self):
        self.canvas = tk.Canvas(self.parent_frame, bg="gray", cursor="crosshair")
        self.canvas.pack(expand=True, padx=5, pady=5)

    def _set_tk_image(self, pil):
        self.tk_image = ImageTk.PhotoImage(pil)

    def set_image(self, pil_image, fit_within=None):
        """
        Set the canvas image. If fit_within provided or default fit_within is set, image will be scaled
        to fit while preserving aspect ratio. The transform (scale, offsets) is computed so that:
          image coords * scale + offset -> display coords
        Use display_to_image / image_to_display for conversions.
        """
        if fit_within:
            self.fit_within = fit_within
        self.pil_image = pil_image.copy()
        orig_w, orig_h = self.pil_image.width, self.pil_image.height
        max_w, max_h = self.fit_within

        # compute scale preserving aspect ratio (only downscale)
        scale_x = min(1.0, max_w / orig_w) if orig_w else 1.0
        scale_y = min(1.0, max_h / orig_h) if orig_h else 1.0
        scale = min(scale_x, scale_y) if (scale_x and scale_y) else 1.0
        if scale <= 0:
            scale = 1.0

        # If image needs scaling down, do it; otherwise keep original
        if scale != 1.0:
            new_w = int(orig_w * scale)
            new_h = int(orig_h * scale)
            display_img = self.pil_image.resize((new_w, new_h), Image.Resampling.LANCZOS)
            self.display_w, self.display_h = new_w, new_h
        else:
            display_img = self.pil_image.copy()
            self.display_w, self.display_h = orig_w, orig_h

        
        try:
            self.canvas.config(width=self.display_w, height=self.display_h)
        except Exception:
            pass

        
        self._set_tk_image(display_img)
        if self.image_id is None:
            self.image_id = self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)
        else:
            self.canvas.itemconfig(self.image_id, image=self.tk_image)

        # store transform (sx, sy)
        sx = self.display_w / orig_w if orig_w else 1.0
        sy = self.display_h / orig_h if orig_h else 1.0
        self.scale = (sx, sy)
        # offsets (top-left anchor used here)
        self.offset_x = 0
        self.offset_y = 0

        # clear overlays so they re-draw correctly for new scale
        self.clear_detections()
        self.clear_markers()

    def display_to_image(self, dx, dy):
        """
        Convert display coordinates (e.g., clicked pixel on canvas) to original image coordinates.
        Returns tuple (ix, iy) as floats.
        """
        sx, sy = self.scale
        ix = (dx - self.offset_x) / sx if sx else dx - self.offset_x
        iy = (dy - self.offset_y) / sy if sy else dy - self.offset_y
        return ix, iy

    def image_to_display(self, ix, iy):
        """
        Convert image coordinates to display coordinates (integers).
        """
        sx, sy = self.scale
        dx = int(ix * sx + self.offset_x)
        dy = int(iy * sy + self.offset_y)
        return dx, dy

    def _on_left_click(self, event):
        if self._left_click_cb:
            self._left_click_cb(event.x, event.y)

    def _on_right_click(self, event):
        if self._right_click_cb:
            self._right_click_cb(event.x, event.y)

    def _on_motion(self, event):
        self.tooltip.place(x=event.x + 15, y=event.y + 15)
        ix, iy = self.display_to_image(event.x, event.y)
        self.tooltip.config(text=f"X: {int(ix)}, Y: {int(iy)}")

    def bind_left_click(self, callback):
        self._left_click_cb = callback

    def bind_right_click(self, callback):
        self._right_click_cb = callback

    # Drawing helpers (coords accepted in image coordinate space)
    def draw_marker(self, ix, iy, label, tag=None):
        """
        ix,iy = image coords (original image). Convert to display coords and draw.
        """
        dx, dy = self.image_to_display(ix, iy)
        tag = tag or self.marker_tag
        self.canvas.create_oval(dx-6, dy-6, dx+6, dy+6, fill="red", outline="white", width=2, tags=tag)
        self.canvas.create_text(dx+16, dy, text=label, font=("Arial", 10, "bold"), fill="yellow", anchor=tk.W, tags=tag)

    def clear_markers(self, tag=None):
        tag = tag or self.marker_tag
        self.canvas.delete(tag)

    def redraw_all_markers(self, mapped_students, mapped_student_objects, tag=None):
        tag = tag or self.marker_tag
        self.clear_markers(tag=tag)
        for roll, (ix, iy) in mapped_students.items():
            stu = mapped_student_objects.get(roll)
            if stu:
                self.draw_marker(ix, iy, stu.name, tag=tag)

    # Detection drawing (detections are in image coordinates)
    def clear_detections(self):
        self.canvas.delete(self.det_tag)
        self.canvas.delete(self.flag_tag)

    def draw_detections(self, detections, color="red"):
        """
        Draw detections returned by detector on the canvas. detections: list of dicts x1,y1,x2,y2,conf
        Coordinates provided are image coords; convert to display coordinates for drawing.
        """
        self.canvas.delete(self.det_tag)
        for det in detections:
            x1, y1, x2, y2 = det["x1"], det["y1"], det["x2"], det["y2"]
            dx1, dy1 = self.image_to_display(x1, y1)
            dx2, dy2 = self.image_to_display(x2, y2)
            self.canvas.create_rectangle(dx1, dy1, dx2, dy2, outline=color, width=2, tags=self.det_tag)
            label = f"Cheating {det.get('conf', 0.0)*100:.1f}%"
            self.canvas.create_text(dx1 + 6, dy1 - 10, text=label, fill=color, anchor="nw", font=("Arial", 9, "bold"), tags=self.det_tag)

    def draw_flag_for_student(self, ix, iy, name, color="orange"):
        """
        Draw a flag overlay on the mapped student's display position. Inputs are image coords.
        """
        dx, dy = self.image_to_display(ix, iy)
        tag = self.flag_tag
        self.canvas.create_oval(dx-9, dy-9, dx+9, dy+9, outline=color, width=3, tags=tag)
        self.canvas.create_text(dx, dy+14, text=f"FLAG: {name}", fill=color, font=("Arial", 9, "bold"), tags=tag)

    def export_current_canvas_as_image(self):
        """
        Return a copy of the current original PIL image (image coords).
        This is used as base for saved frames (we draw bounding boxes in image coords onto this).
        """
        return self.pil_image.copy()