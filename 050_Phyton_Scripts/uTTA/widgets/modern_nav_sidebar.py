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
        self.content: Optional[tk.Frame] = None
        self.index: int = 0
        self.text_value: str = ""

class ModernNavSidebar(tb.Frame):
    """ Animated navigation sidebar module for ttkbootstrap.
        Uses stable Tkinter rendering for dynamic color changes.
    """
    
    def __init__(self, parent: Any, callback: Optional[Callable[[str], None]] = None, bootstyle: str = "dark"):
        super().__init__(parent)
        
        self.callback = callback  
        self.NAVBAR_WIDTH = 65 # fixed witdh of the navigation sidebar
        self.EXPANDED_WIDTH = 350 # final width of the folded menu
        self.ANIMATION_DURATION = 300  
  
        # Get colors from the current theme
        style_instance = Style.get_instance()
        self.PRIMARY_COLOR = style_instance.colors.get(bootstyle) if style_instance else "#1f2937" # type: ignore
        self.ACCENT_COLOR = style_instance.colors.get("primary") if style_instance else "#10b981" # type: ignore
        self.HOVER_COLOR = (style_instance.colors.get("inputbg") if style_instance else None) or "#374151" # type: ignore
        self.TEXT_COLOR = (style_instance.colors.get("fg") if style_instance else None) or "#f3f4f6" # type: ignore
        
        self.is_collapsed = False         
        self.current_sash_pos = float(self.EXPANDED_WIDTH)
        self.animating = False           
        self.active_button: Optional[SidebarButtonFrame] = None        
        self.menu_buttons: list[SidebarButtonFrame] = []
        self.tooltip_window: Optional[tb.Toplevel] = None
            
        self.setup_ui(bootstyle)
    
    def setup_ui(self, bootstyle: str) -> None:
        # fixed width of the navigation sidebar
        self.configure(width=self.NAVBAR_WIDTH)
        self.pack_propagate(False)
        self.pack(side=LEFT, fill=Y)

         # The main sidebar container
        self.sidebar = tb.Frame(self, bootstyle=bootstyle, width=self.NAVBAR_WIDTH)
        self.sidebar.pack(side=LEFT, fill=Y, expand=True)
        self.sidebar.pack_propagate(False)
        
        separator = tb.Separator(self.sidebar, bootstyle="light")
        separator.pack(fill=X, padx=10, pady=(0, 15))

        # The menu-frame uses standard tkinter to have more freedome when controlling color changes
        self.menu_frame = tk.Frame(self.sidebar, background=self.PRIMARY_COLOR)
        self.menu_frame.pack(fill=BOTH, expand=True, padx=5, pady=5)
        
        bottom_frame = tk.Frame(self.sidebar, background=self.PRIMARY_COLOR)
        bottom_frame.pack(side=BOTTOM, fill=X, pady=15)
        
        # Arrow-Button at the bottom for folding the menu in and out
        self.collapse_button = tk.Button(
            bottom_frame, text="◄", font=("Arial", 12), 
            foreground=self.TEXT_COLOR, background=self.PRIMARY_COLOR,
            activeforeground=self.ACCENT_COLOR, activebackground=self.HOVER_COLOR,
            bd=0, cursor="hand2", relief="flat", command=self.toggle_menu
        )
        self.collapse_button.pack(fill=X, pady=(0, 15))

    def add_menu_item(self, text: str, icon_char: str, tooltip: str = "") -> None:
        index = len(self.menu_buttons)

         # use tkinter instead of ttkbootstrap for the immer components to have better control over colors
        button_frame = SidebarButtonFrame(self.menu_frame, height=48, width=50, background=self.PRIMARY_COLOR)
        button_frame.pack(fill=X, pady=5)
        button_frame.pack_propagate(False)
        
        indicator = tk.Frame(button_frame, width=4, background=self.PRIMARY_COLOR)
        indicator.pack(side=LEFT, fill=Y)
        
        content = tk.Frame(button_frame, background=self.PRIMARY_COLOR)
        content.pack(side=LEFT, fill=BOTH, expand=True, padx=8, pady=8)
        
        # Just show the icon, no menu text
        icon_label = tk.Label(content, text=icon_char, font=("Arial", 14), foreground=self.TEXT_COLOR, background=self.PRIMARY_COLOR)
        icon_label.pack(expand=True)
        
        button_frame.indicator = indicator
        button_frame.icon_label = icon_label
        button_frame.content = content
        button_frame.index = index
        button_frame.text_value = text
            
        for widget in [button_frame, content, icon_label]:
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

            x = widget.winfo_rootx() + 60
            y = widget.winfo_rooty() + 8
            
            self.tooltip_window = tb.Toplevel(widget) # type: ignore
            self.tooltip_window.wm_overrideredirect(True)
            self.tooltip_window.wm_geometry(f"+{x}+{y}")

            # set window-attributes for a more stable layering on Windows/Linux
            self.tooltip_window.wm_attributes("-topmost", True)
            
            label = tb.Label(self.tooltip_window, text=text, bootstyle="light-inverse", padding=(8, 4))
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

    def toggle_menu(self) -> None:
        """ Switches visibility of the menu between hidden and visible
        """
        if self.animating:
            return
        self.animating = True
        
        self.is_collapsed = not self.is_collapsed
        self.collapse_button.configure(text="►" if self.is_collapsed else "◄")
        
        parent_container = self.nametowidget(self.winfo_parent()) # this is the parent frame around the menu bar
        
        # Hide all widgets within the menu area to make the PanedWindow collapsible
        if parent_container:
            for widget in parent_container.winfo_children():
                if widget != self:
                    if self.is_collapsed:
                        widget.pack_forget()
                    else:
                        widget.pack(side=LEFT, fill=BOTH, expand=True)

        # Calculate the expanded / collapsed target position
        target_sash = self.NAVBAR_WIDTH if self.is_collapsed else self.EXPANDED_WIDTH
        
        start_sash = self.current_sash_pos
        parent_pw = self._find_parent_panedwindow()
        if parent_pw and len(parent_pw.panes()) > 1:
            try:
                curr = parent_pw.sashpos(0)
                if curr > 0:
                    start_sash = float(curr)
            except tk.TclError:
                pass

        diff = target_sash - start_sash
        start_time = time.time()
            
        def animate_step() -> None:
            """Animates the folding of the menu bar one step at a time
            """
            elapsed_time = time.time() - start_time
            if elapsed_time >= self.ANIMATION_DURATION / 1000:
                self._set_sash_position(float(target_sash))
                self.animating = False
                return
           
            progress = elapsed_time / (self.ANIMATION_DURATION / 1000)
            eased_progress = 1 - math.pow(1 - progress, 3)
            new_sash = start_sash + (diff * eased_progress)
            self._set_sash_position(new_sash)
            self.after(16, animate_step) 
        
        animate_step()

    def _find_parent_panedwindow(self) -> Optional[Any]:
        current_widget = self
        while current_widget:
            parent_name = current_widget.winfo_parent()
            if not parent_name:
                break
            parent_widget = current_widget.nametowidget(parent_name)
            if isinstance(parent_widget, (tb.Panedwindow, tk.PanedWindow)):
                return parent_widget
            current_widget = parent_widget
        return None

    def _set_sash_position(self, pos: float) -> None:
        self.current_sash_pos = pos
        parent_pw = self._find_parent_panedwindow()
        if parent_pw and len(parent_pw.panes()) > 1:
            try:
                parent_pw.sashpos(0, int(pos))
            except tk.TclError:
                pass

    def set_active_button(self, button_frame: SidebarButtonFrame) -> None:
        if self.active_button and self.active_button.indicator and self.active_button.icon_label and self.active_button.content:
            self.active_button.configure(background=self.PRIMARY_COLOR)
            self.active_button.content.configure(background=self.PRIMARY_COLOR)
            self.active_button.icon_label.configure(foreground=self.TEXT_COLOR, background=self.PRIMARY_COLOR)
            self.active_button.indicator.configure(background=self.PRIMARY_COLOR)
       
        if button_frame.indicator and button_frame.icon_label and button_frame.content:
            button_frame.configure(background=self.PRIMARY_COLOR)
            button_frame.content.configure(background=self.PRIMARY_COLOR)
            button_frame.icon_label.configure(foreground=self.ACCENT_COLOR, background=self.PRIMARY_COLOR)
            button_frame.indicator.configure(background=self.ACCENT_COLOR)
        self.active_button = button_frame

    def on_button_hover(self, button_frame: SidebarButtonFrame) -> None:
        if button_frame == self.active_button:
            return
        if button_frame.icon_label and button_frame.content:
            button_frame.configure(background=self.HOVER_COLOR)
            button_frame.content.configure(background=self.HOVER_COLOR)
            button_frame.icon_label.configure(foreground="#ffffff", background=self.HOVER_COLOR)

    def on_button_click(self, button_frame: SidebarButtonFrame, index: int) -> None:
        if self.tooltip_window:
            try: 
                self.tooltip_window.destroy()
            except: 
                pass
            self.tooltip_window = None
            
        # Highlight the active menu button in the navigation bar
        self.set_active_button(button_frame)
        
        # In case the menu is closed open it, otherwise do nothing
        if self.is_collapsed:
            self.toggle_menu()

        # execute the callback to load a new menu 
        if self.callback:
            self.callback(button_frame.text_value)

    def on_button_leave(self, button_frame: SidebarButtonFrame) -> None:
        # Safety Net to prevent orphan tooltips: As soon as the cursor leaves the button, kill tooltip
        if self.tooltip_window:
            try: 
                self.tooltip_window.destroy()
            except: 
                pass
            self.tooltip_window = None

        if button_frame == self.active_button:
            return
        if button_frame.icon_label and button_frame.content:
            button_frame.configure(background=self.PRIMARY_COLOR)
            button_frame.content.configure(background=self.PRIMARY_COLOR)
            button_frame.icon_label.configure(foreground=self.TEXT_COLOR, background=self.PRIMARY_COLOR)
