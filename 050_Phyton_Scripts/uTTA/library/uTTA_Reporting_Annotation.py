#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module Name:    uTTA_Reporting_Annotation.py
Description:    An Add-On GUI to uTTA_Reporting.py.
                This GUI features an Annotation tool to add images with captions to the generated report.
                Images can be arranged in one of the possible layouts (1, 2 or 3 columns).
                Each image will get its own caption for documentation purposes.

Author:         wtronics
Email:          169440509+wtronics@users.noreply.github.com
Date:           30.06.2026
Version:        $VERSION$

--------------------------------------------------------------------------
License:
Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International
(CC BY-NC-SA 4.0)

You are free to share and adapt this material under the following terms:
- Attribution: You must give appropriate credit.
- NonCommercial: You may not use the material for commercial purposes.
- ShareAlike: You must distribute your contributions under the same license.

The full license text can be found at:
https://creativecommons.org/licenses/by-nc-sa/4.0/
--------------------------------------------------------------------------
"""

import base64
import io
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from PIL import Image, ImageTk
from tkinter import filedialog
import ttkbootstrap as tb
from ttkbootstrap.constants import BOTH, BOTTOM, DANGER, LEFT, PRIMARY, RIGHT, SECONDARY, SUCCESS, TOP, W, X, YES
from ttkbootstrap.dialogs import MessageDialog
from ttkbootstrap.widgets.scrolled import ScrolledFrame


class ImageLayoutDialog(tb.Toplevel):
    def __init__(self, parent: tb.Window, image_paths: List[Union[str, Path]]) -> None:
        """Initializes the ImageLayoutDialog window and loads image previews.

        Args:
            parent (tb.Window): The reference to the parent GUI window.
            image_paths (List[Union[str, Path]]): A list of paths to image files.
        """
        super().__init__(title="Process Images & Select Layout", size=(900, 700), resizable=(False, False))
        self.position_center()
        self.grab_set()  # Make dialog modal

        self.parent = parent
        self.image_paths = image_paths

        # Result data that will be collected on confirmation
        self.layout_mapping: Dict[str, str] = {"1 Column (Stacked)": "grid-1",
                                               "2 Columns (Side-by-Side)": "grid-2",
                                               "3 Columns (Grid)": "grid-3"}
        self.result_layout: str = "grid-1"
        self.processed_images_html: List[str] = []
        self.confirmed: bool = False

        # Dictionary to keep track of UI elements and image data per file
        self.image_data_store: Dict[int, Dict[str, Any]] = {}

        self._build_ui()
        self._load_and_render_previews()

    def _build_ui(self) -> None:
        """ Constructs the main layout and controls of the dialog window.
        """
        # Main container with padding
        main_frame = tb.Frame(self, padding=10)
        main_frame.pack(fill=BOTH, expand=YES)

        # Top Section: Scrollable Preview Area
        preview_label_frame = tb.Labelframe(main_frame, text="Image Captions & Preview", padding=5)
        preview_label_frame.pack(fill=BOTH, expand=YES, padx=5, pady=5)

        # Scrollable Frame using ttkbootstrap's ScrolledFrame
        self.scroll_frame = ScrolledFrame(preview_label_frame, autohide=True)
        self.scroll_frame.pack(fill=BOTH, expand=YES)

        # Middle Section: Action Buttons
        button_frame = tb.Frame(main_frame)
        button_frame.pack(fill=X, side=BOTTOM)

        self.btn_cancel = tb.Button(button_frame, text="Cancel", bootstyle=DANGER, command=self.close_dialog)
        self.btn_cancel.pack(side=RIGHT, padx=5)

        self.btn_confirm = tb.Button(button_frame, text="Apply to Report", bootstyle=SUCCESS, command=self.confirm_selection)
        self.btn_confirm.pack(side=RIGHT, padx=5)

        # Bottom Section: Layout Selection
        top_frame = tb.Labelframe(main_frame, text="Image Layout Settings", padding=10)
        top_frame.pack(fill=X, side=TOP, padx=5, pady=5)

        tb.Label(top_frame, text="Choose Column Layout:").pack(side=LEFT, padx=(0, 10))
        
        self.layout_var = tb.StringVar(value= "1 Column (Stacked)")
        layout_selector = tb.Combobox(
            top_frame, 
            textvariable=self.layout_var, 
            values=["1 Column (Stacked)", "2 Columns (Side-by-Side)", "3 Columns (Grid)"],
            state="readonly",
            width=25
        )
        layout_selector.pack(side=LEFT)
        layout_selector.bind("<<ComboboxSelected>>", self._on_layout_change)

    def _load_and_render_previews(self) -> None:
        """ Loads, resizes, compresses images to WebP, and renders preview rows in the UI.
        """
        for idx, path in enumerate(self.image_paths):
            try:
                with Image.open(path) as img:
                    if img.mode in ("RGBA", "P"):
                        img = img.convert("RGB")

                    # Generate a small Tkinter thumbnail for the GUI preview
                    thumb_img = img.copy()
                    thumb_img.thumbnail((180, 140))
                    tk_thumb = ImageTk.PhotoImage(thumb_img)

                    # Compress original or resized image to WebP bytes for HTML report
                    if img.width > 1200:
                        w_percent = 1200 / float(img.width)
                        h_size = int(float(img.height) * w_percent)
                        img = img.resize((1200, h_size), Image.Resampling.LANCZOS)

                    buffer = io.BytesIO()
                    img.save(buffer, format="WEBP", quality=75)
                    base64_str = base64.b64encode(buffer.getvalue()).decode("utf-8")

                    # Store data internally
                    self.image_data_store[idx] = {
                        "base64": base64_str,
                        "tk_thumb": tk_thumb  # Retain reference to prevent garbage collection
                    }

                    # Create row UI element in ScrolledFrame
                    self._create_image_row_ui(idx, Path(path).name, tk_thumb)

            except Exception as e:
                print(f"Error processing image {path}: {e}")

    def _create_image_row_ui(self, idx: int, filename: str, tk_thumb: ImageTk.PhotoImage) -> None:
        """ Creates a single item preview row inside the scrollable container.

        Args:
            idx (int): The index of the current image item row.
            filename (str): The name of the file shown in the UI.
            tk_thumb (ImageTk.PhotoImage): The thumbnail object of the image.
        """
        row_card = tb.Frame(self.scroll_frame, padding=10, bootstyle=SECONDARY)
        row_card.pack(fill=X, pady=5, padx=5)

        # Image column
        img_label = tb.Label(row_card, image=tk_thumb)
        img_label.pack(side=LEFT, padx=5)

        # Inputs column
        info_frame = tb.Frame(row_card, bootstyle=SECONDARY)
        info_frame.pack(side=LEFT, fill=BOTH, expand=YES, padx=10)

        tb.Label(info_frame, text=filename, font=("-size", 10, "-weight", "bold"), bootstyle="inverse-secondary").pack(anchor=W, pady=(0, 5))
        tb.Label(info_frame, text="Caption:", bootstyle="inverse-secondary").pack(anchor=W)
        
        caption_entry = tb.Entry(info_frame)
        caption_entry.pack(fill=BOTH, pady=2)

        # Save reference to entry widget to extract text on confirmation
        self.image_data_store[idx]["entry_widget"] = caption_entry

    def _on_layout_change(self, event: Any) -> None:
        """ Handles combobox selection change and updates the target CSS layout class name.
        
        Args:
            event (Any): Tkinter event object triggering the selection handler.
        """
        self.result_layout = self.layout_mapping.get(self.layout_var.get(), "grid-1")

    def confirm_selection(self) -> None:
        """ Assembles final HTML figure elements and marks the dialog selection as confirmed.
        """
        self.processed_images_html = []

        for idx, data in self.image_data_store.items():
            caption_text = data["entry_widget"].get().strip()
            base64_str = data["base64"]

            original_filename = Path(self.image_paths[idx]).name

            # Construct HTML Figure element
            caption_html = f"<figcaption>{caption_text}</figcaption>" if caption_text else ""
            html_snippet = f"""
            <figure class="report-figure" data-original-filename="{original_filename}">
                <img src="data:image/webp;base64,{base64_str}" alt="Test Setup">
                {caption_html}
            </figure>
            """
            self.processed_images_html.append(html_snippet)

        self.confirmed = True
        self.close_dialog()

    def close_dialog(self) -> None:
        """ Releases window grab and destroys the modal dialog.
        """
        self.grab_release()
        self.destroy()


def select_and_process_images(root_window: tb.Window) -> Optional[Dict[str, str]]:
    """Triggers file selection dialog and opens the image layout annotation GUI.

    Args:
        root_window (tb.Window): Parent Tkinter/ttkbootstrap window reference.

    Returns:
        Optional[Dict[str, str]]: Dictionary containing chosen layout class and concatenated HTML, or None if cancelled.
    """
    file_paths = filedialog.askopenfilenames(title="Select Test Setup Images", filetypes=[("Image files", "*.jpg *.jpeg *.png *.webp")])

    if not file_paths:
        return None

    # Open the ttkbootstrap Dialog
    dialog = ImageLayoutDialog(root_window, list(file_paths))
    root_window.wait_window(dialog)  # Wait until dialog is closed

    if dialog.confirmed:
        return {
            "layout_class": dialog.result_layout,
            "images_html": "".join(dialog.processed_images_html),
        }
    return None


if __name__ == "__main__":
    # Test App to verify UI
    app = tb.Window(title="µTTA Main Application Simulation", themename="flatly", size=(400, 200))

    def on_click_upload() -> None:
        result = select_and_process_images(app)
        if result:
            MessageDialog(
                title="Success",
                message=(f"Successfully generated HTML for {len(result['images_html'])} chars.\n"
                        f"Chosen Layout: {result['layout_class']}")
            ).show()

    tb.Button(app, text="Add Setup Photos to Report", command=on_click_upload, bootstyle=PRIMARY).pack(expand=YES)
    app.mainloop()