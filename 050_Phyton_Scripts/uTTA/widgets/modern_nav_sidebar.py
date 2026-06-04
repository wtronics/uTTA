#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module Name:    modern_nav_sidebar.py
Description:    This is a ttkbootstrap custom widget the generate a 
                modern sidebar similar to ctk_sidebar

Author:         wtronics
Email:          169440509+wtronics@users.noreply.github.com
Date:           02.06.2026
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

import tkinter as tk
import ttkbootstrap as tb
from ttkbootstrap.constants import LEFT, Y, BOTH, X, BOTTOM, W, TOP
from ttkbootstrap import Style
import time
import math
from typing import Callable, Any, Optional

class SidebarButtonFrame(tk.Frame):
    """ Specialized standard Tkinter frame to directly control background colors."""
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.indicator: Optional[tk.Frame] = None
        self.icon_label: Optional[tk.Label] = None
        self.text_label: Optional[tk.Label] = None
        self.content: Optional[tk.Frame] = None
        self.index: int = 0
        self.text_value: str = ""

class ModernNavSidebar(tb.Frame):
    """ Animated navigation sidebar module for ttkbootstrap.
        Uses stable Tkinter rendering for dynamic color changes.
    """
    
    def __init__(self, parent: Any, callback: Optional[Callable[[str], None]] = None, bootstyle: str = "dark"):
        super().__init__(parent)
        self.pack(side=LEFT, fill=Y)
        
        self.callback = callback  
        self.EXPANDED_WIDTH = 280    
        self.COLLAPSED_WIDTH = 60    
        self.ANIMATION_DURATION = 300  
        
        # Get colors from the current theme
        style_instance = Style.get_instance()
        self.PRIMARY_COLOR = style_instance.colors.get(bootstyle) if style_instance else "#1f2937" # type: ignore
        self.ACCENT_COLOR = style_instance.colors.get("primary") if style_instance else "#10b981" # type: ignore
        self.HOVER_COLOR = (style_instance.colors.get("inputbg") if style_instance else None) or "#374151" # type: ignore
        self.TEXT_COLOR = (style_instance.colors.get("fg") if style_instance else None) or "#f3f4f6" # type: ignore
        
        self.is_collapsed = False         
        self.current_width = float(self.EXPANDED_WIDTH)
        self.animating = False           
        self.active_button: Optional[SidebarButtonFrame] = None        
        self.menu_buttons: list[SidebarButtonFrame] = []
        self.tooltip_window: Optional[tb.Toplevel] = None
            
        self.setup_ui(bootstyle)
    
    def setup_ui(self, bootstyle: str) -> None:
        self.configure(width=self.EXPANDED_WIDTH)
        self.pack_propagate(False)
        
        # The main sidebar container
        self.sidebar = tb.Frame(self, bootstyle=bootstyle, width=self.EXPANDED_WIDTH)
        self.sidebar.pack(side=LEFT, fill=Y)
        self.sidebar.pack_propagate(False) 
        
        separator = tb.Separator(self.sidebar, bootstyle="light")
        separator.pack(fill=X, padx=15, pady=(0, 15))
        
        # The menu-frame uses standard tkinter to have more freedome when controlling color changes
        self.menu_frame = tk.Frame(self.sidebar, background=self.PRIMARY_COLOR)
        self.menu_frame.pack(fill=BOTH, expand=True, padx=10, pady=5)
        
        bottom_frame = tk.Frame(self.sidebar, background=self.PRIMARY_COLOR)
        bottom_frame.pack(side=BOTTOM, fill=X, pady=15)
        
        # Create the folding button at the bottom
        self.collapse_button = tk.Button(
            bottom_frame, text="◄", font=("Arial", 12), 
            foreground=self.TEXT_COLOR, background=self.PRIMARY_COLOR,
            activeforeground=self.ACCENT_COLOR, activebackground=self.HOVER_COLOR,
            bd=0, cursor="hand2", relief="flat", command=self.toggle_sidebar
        )
        self.collapse_button.pack(fill=X, pady=(0,250))

    def add_menu_item(self, text: str, icon_char: str, tooltip: str = "") -> None:
        index = len(self.menu_buttons)
        
        # use tkinter instead of ttkbootstrap for the immer components to have better control over colors
        button_frame = SidebarButtonFrame(self.menu_frame, height=52, background=self.PRIMARY_COLOR)
        button_frame.pack(fill=X, pady=5)
        button_frame.pack_propagate(False)
        
        indicator = tk.Frame(button_frame, width=4, background=self.PRIMARY_COLOR)
        indicator.pack(side=LEFT, fill=Y)
        
        content = tk.Frame(button_frame, background=self.PRIMARY_COLOR)
        content.pack(side=LEFT, fill=BOTH, expand=True, padx=8, pady=8)
        
        icon_label = tk.Label(content, text=icon_char, font=("Arial", 14), foreground=self.TEXT_COLOR, background=self.PRIMARY_COLOR)
        icon_label.pack(side=LEFT, padx=(5, 5))
        
        text_label = tk.Label(content, text=text, font=("Arial", 11), foreground=self.TEXT_COLOR, background=self.PRIMARY_COLOR, anchor=W)
        text_label.pack(side=LEFT, fill=X, expand=True)
        
        button_frame.indicator = indicator
        button_frame.icon_label = icon_label
        button_frame.text_label = text_label
        button_frame.content = content
        button_frame.index = index
        button_frame.text_value = text
            
        for widget in [button_frame, content, icon_label, text_label]:
            widget.bind("<Button-1>", lambda e, f=button_frame, i=index: self.on_button_click(f, i))
            widget.bind("<Enter>", lambda e, f=button_frame: self.on_button_hover(f))
            widget.bind("<Leave>", lambda e, f=button_frame: self.on_button_leave(f))
        
        self.create_tooltip(button_frame, tooltip if tooltip else text)
        self.menu_buttons.append(button_frame)
        
        if index == 0:
            self.set_active_button(button_frame)

    def create_tooltip(self, widget: tk.Frame, text: str) -> None:
        def show_tooltip(event: Any) -> None:
            # delete all existing/remaining tooltips before creating a new one
            if self.tooltip_window:
                try:
                    self.tooltip_window.destroy()
                except:
                    pass
                self.tooltip_window = None

            if self.is_collapsed:
                x = widget.winfo_rootx() + 75
                y = widget.winfo_rooty() + 10
                
                self.tooltip_window = tb.Toplevel(widget) # type: ignore
                self.tooltip_window.wm_overrideredirect(True)
                self.tooltip_window.wm_geometry(f"+{x}+{y}")
                
                # set window-attributes for a more stable layering on Windows/Linux
                self.tooltip_window.wm_attributes("-topmost", True)
                
                label = tb.Label(self.tooltip_window, text=text, bootstyle="light-inverse", padding=(10, 6))
                label.pack()
        
        def hide_tooltip(event: Any = None) -> None:
            if self.tooltip_window:
                try:
                    self.tooltip_window.destroy()
                except:
                    pass
                self.tooltip_window = None
                
        widget.bind('<Enter>', show_tooltip, add="+")
        widget.bind('<Leave>', hide_tooltip, add="+")
        # Important: Delete Tooltip right after clicking!
        widget.bind('<Button-1>', lambda e: hide_tooltip(), add="+")

    def toggle_sidebar(self) -> None:
        if self.animating:
            return
        self.animating = True
        
        target_width = self.COLLAPSED_WIDTH if not self.is_collapsed else self.EXPANDED_WIDTH
        start_width = self.current_width
        width_difference = target_width - start_width
        start_time = time.time()
            
        def animate_step() -> None:
            elapsed_time = time.time() - start_time
            if elapsed_time >= self.ANIMATION_DURATION / 1000:
                self.update_sidebar_width(float(target_width))
                self.is_collapsed = not self.is_collapsed
                self.collapse_button.configure(text="►" if self.is_collapsed else "◄")
                self.update_button_layout()
                self.animating = False
                return
           
            progress = elapsed_time / (self.ANIMATION_DURATION / 1000)
            eased_progress = 1 - math.pow(1 - progress, 3)
            new_width = start_width + (width_difference * eased_progress)
            self.update_sidebar_width(new_width)
            self.after(16, animate_step) 
        
        animate_step()
    
    def update_sidebar_width(self, width: float) -> None:
        self.current_width = width
        self.configure(width=int(width))
        self.sidebar.configure(width=int(width))
    
    def update_button_layout(self) -> None:
        for button in self.menu_buttons:
            if self.is_collapsed and button.text_label and button.icon_label:
                button.text_label.pack_forget()
                button.icon_label.pack_forget()
                button.icon_label.pack(side=TOP, padx=0, pady=(12, 0), anchor="center")
            elif button.icon_label and button.text_label:
                button.icon_label.pack_forget()
                button.icon_label.pack(side=LEFT, padx=(5, 10))
                button.text_label.pack(side=LEFT, fill=X, expand=True)

        if self.active_button:
            self.set_active_button(self.active_button)

    def set_active_button(self, button_frame: SidebarButtonFrame) -> None:
        if self.active_button and self.active_button.text_label and self.active_button.indicator and self.active_button.icon_label and self.active_button.content:
            self.active_button.configure(background=self.PRIMARY_COLOR)
            self.active_button.content.configure(background=self.PRIMARY_COLOR)
            self.active_button.text_label.configure(foreground=self.TEXT_COLOR, background=self.PRIMARY_COLOR)
            self.active_button.icon_label.configure(foreground=self.TEXT_COLOR, background=self.PRIMARY_COLOR)
            self.active_button.indicator.configure(background=self.PRIMARY_COLOR)
       
        if button_frame.text_label and button_frame.indicator and button_frame.icon_label and button_frame.content:
            button_frame.configure(background=self.PRIMARY_COLOR)
            button_frame.content.configure(background=self.PRIMARY_COLOR)
            button_frame.text_label.configure(foreground=self.ACCENT_COLOR, background=self.PRIMARY_COLOR)
            button_frame.icon_label.configure(foreground=self.ACCENT_COLOR, background=self.PRIMARY_COLOR)
            button_frame.indicator.configure(background=self.ACCENT_COLOR)
        self.active_button = button_frame

    def on_button_hover(self, button_frame: SidebarButtonFrame) -> None:
        if button_frame == self.active_button:
            return
        if button_frame.text_label and button_frame.icon_label and button_frame.content:
            button_frame.configure(background=self.HOVER_COLOR)
            button_frame.content.configure(background=self.HOVER_COLOR)
            button_frame.text_label.configure(foreground="#ffffff", background=self.HOVER_COLOR)
            button_frame.icon_label.configure(foreground="#ffffff", background=self.HOVER_COLOR)


    def on_button_click(self, button_frame: SidebarButtonFrame, index: int) -> None:
        if self.tooltip_window:
            try: self.tooltip_window.destroy()
            except: pass
            self.tooltip_window = None
            
        self.set_active_button(button_frame)
        if self.callback:
            self.callback(button_frame.text_value)

    def on_button_leave(self, button_frame: SidebarButtonFrame) -> None:
        # Safety Net to prevent orphan tooltips: As soon as the cursor leaves the button, kill tooltip
        if self.tooltip_window:
            try: self.tooltip_window.destroy()
            except: pass
            self.tooltip_window = None

        if button_frame == self.active_button:
            return
        if button_frame.text_label and button_frame.icon_label and button_frame.content:
            button_frame.configure(background=self.PRIMARY_COLOR)
            button_frame.content.configure(background=self.PRIMARY_COLOR)
            button_frame.text_label.configure(foreground=self.TEXT_COLOR, background=self.PRIMARY_COLOR)
            button_frame.icon_label.configure(foreground=self.TEXT_COLOR, background=self.PRIMARY_COLOR)
