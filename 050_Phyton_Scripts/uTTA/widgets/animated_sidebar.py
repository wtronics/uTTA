#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module Name:    animated_sidebar.py
Description:    This is a ttkbootstrap custom widget the generate an animated sidebar.
                It supports multiple tabs with a common navigation bar.
                By clicking on the navigation bar, the content unfolds

Author:         wtronics
Email:          169440509+wtronics@users.noreply.github.com
Date:           01.06.2026
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

import ttkbootstrap as tb
from ttkbootstrap.constants import LEFT, RIGHT, BOTH, Y, TOP, X, W

class SidebarContent(tb.Frame):
    """ Represents the content of a single sidebar (notebook with tabs)."""
    def __init__(self, parent, title, tabs_data, style="secondary"):
        super().__init__(parent, style=style)
        
        # Header
        header = tb.Frame(self, style=style)
        header.pack(fill=X, padx=10, pady=10)
        
        tb.Label(header, text=title, font=("Helvetica", 12, "bold"), style=f"inverse").pack(side=LEFT)
        
        # Separator
        tb.Separator(self, style="light").pack(fill=X, padx=10, pady=5)

        # Notebook for tabs
        notebook = tb.Notebook(self, style="primary")
        notebook.pack(fill=BOTH, expand=True, padx=10, pady=10)

        # fill tabs
        for tab_name, content_func in tabs_data.items():
            tab_frame = tb.Frame(notebook, padding=10)
            content_func(tab_frame)
            notebook.add(tab_frame, text=tab_name)


class AnimatedMultiSidebar(tb.Frame):
    """ A hopefully reusable, animated mulit-sidebar. 
        Places a small buttoned sidebar on teh right which opens and closes a 
        common content container with a nice animation.
    """
    def __init__(self, parent, target_width=250, button_bar_width=45, 
                 style_buttons="dark", style_content="secondary", speed=15):
        # mainframe of this widget is on teh far right within the main window
        super().__init__(parent)
        self.pack(side=RIGHT, fill=Y)

        self.target_width = target_width
        self.button_bar_width = button_bar_width
        self.speed = speed # pixel per animated step
        
        self.animation_speed = 2
        self.active_key = None
        self.current_width = 0
        self.is_animating = False
        self.sidebar_contents = {}

        # common content container (on the left within the widget)
        self.container = tb.Frame(self, width=0, style=style_content)
        self.container.pack(side=LEFT, fill=Y)
        self.container.pack_propagate(False)

        # permanent button bar (on the right within the widget)
        self.button_bar = tb.Frame(self, width=self.button_bar_width, style=style_buttons)
        self.button_bar.pack(side=RIGHT, fill=Y)
        self.button_bar.pack_propagate(False)

    def add_sidebar(self, key, icon, title, tabs_data):
        """ Adds a new sidebar with an UNICODE icon to the sidebar."""
        # Create content (packing is done on demand)
        self.sidebar_contents[key] = SidebarContent(self.container, title, tabs_data, style=self.container.cget("style"))
        
        # button within the button bar
        print(self.button_bar.cget('style'))
        btn = tb.Button(self.button_bar, text=icon, style=f"dark-outline", command=lambda: self.toggle_sidebar(key), padding=1)
        btn.pack(side=TOP, fill=X, padx=3, pady=5)

    def toggle_sidebar(self, key):
        """ handles the toggling and starts the animation"""
        if self.is_animating:
            return  # lock the animation while there is an animation running

        if self.active_key == key:
            # same button pressed again -> closing animation
            self.active_key = None
            self.animate_close(key)
        elif self.active_key is not None:
            # another menu was oben -> change content without animation
            self.sidebar_contents[self.active_key].pack_forget()
            self.sidebar_contents[key].pack(fill=BOTH, expand=True)
            self.active_key = key
        else:
            # Everything was closed -> opening animation
            self.active_key = key
            self.sidebar_contents[key].pack(fill=BOTH, expand=True)
            self.animate_open()

    def animate_open(self):
        """ increase in small steps the width of the container to generate the animation"""
        self.is_animating = True
        if self.current_width < self.target_width:
            self.current_width += self.speed
            if self.current_width > self.target_width:
                self.current_width = self.target_width
            
            self.container.config(width=self.current_width)
            # Wait a few milli seconds, then do the next step
            self.after(self.animation_speed, self.animate_open)
        else:
            self.is_animating = False

    def animate_close(self, key_to_hide):
        """ decreases in small steps the width of the container to generate the closing animation"""
        self.is_animating = True
        if self.current_width > 0:
            self.current_width -= self.speed
            if self.current_width < 0:
                self.current_width = 0
                
            self.container.config(width=self.current_width)
            self.after(self.animation_speed, lambda: self.animate_close(key_to_hide))
        else:
            # Hide content as soon it is completely closed
            self.sidebar_contents[key_to_hide].pack_forget()
            self.is_animating = False