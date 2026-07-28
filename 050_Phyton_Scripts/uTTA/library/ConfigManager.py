#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module Name:    ConfigManager.py
Description:    A clean, reusable configuration manager for Tkinter applications.
                It synchronizes GUI variables, INI-file configurations via `configparser`, and default 
                fallback values using a central schema definition.

                Features:
                - Object attribute access using dot notation (e.g., `cfg.Settings.cal_file_path`).
                - Automatic initialization of GUI variables with default fallbacks.
                - Type-safe loading and casting from INI files.
                - Automatic directory creation upon saving.

Author:         wtronics, Coauthored by Google Gemini
Email:          169440509+wtronics@users.noreply.github.com
Date:           26.07.2026
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

import configparser
from pathlib import Path
import ttkbootstrap as ttk
from typing import Any

class ConfigSection:
    """Generic container object that holds GUI variables as dynamic attributes."""
    def __getattr__(self, name: str) -> Any:
        return self.__dict__[name]

class ConfigManager:
    """Manages application configurations using a central schema definition.

    This class binds Tkinter variables to INI file sections and options. 
    It supports dot-notation access to settings and handles automatic fallback 
    values if no configuration file exists.

    Schema Format:
        A list of tuples, where each tuple represents an option:
        `[(Section, INI_Key, TkVarType, AttributeName, DefaultValue), ...]`

    Example:
        >>> schema = [
        ...     ('Settings', 'Calibration_File_Path', ttk.StringVar, 'cal_file_path', 'C:/default.cal'),
        ...     ('Communication', 'COM_Port', ttk.StringVar, 'com_port', 'COM3')
        ... ]
        >>> cfg = ConfigManager("settings.ini", schema=schema)
        >>> cfg.load()
        >>> entry = ttk.Entry(master, textvariable=cfg.Settings.cal_file_path)
    """

    def __init__(self, filepath: str | Path, scheme: list[tuple]):
        """Initializes the ConfigManager and dynamically creates section objects and variables.

        Args:
            filepath (str | Path): The path to the target INI file.
            scheme (list[tuple]): A list of 5-tuples defining the configuration layout:
                - Section (str): INI section name.
                - INI_Key (str): INI key name.
                - TkVarType (type): Tkinter variable type (e.g., ttk.StringVar, ttk.BooleanVar).
                - AttributeName (str): Name used for dot-notation access.
                - DefaultValue (Any): Fallback value if option is missing or file doesn't exist.
        """

        self.filepath = Path(filepath)
        self.scheme = scheme
        self.config = configparser.ConfigParser()

        # Dynamically create sections and variables as objects and attributes
        for section, key, var_type, attr_name, default in self.scheme:
            # Create the section in case it doesn't exist (e.g. 'Settings')
            if not hasattr(self, section):
                setattr(self, section, ConfigSection())
            
            # get the current section object
            section_obj = getattr(self, section)
            
            # Append the tkinter variable as attributes to the sections-object
            # equals: section_obj.cal_file_path = ttk.StringVar(value=default)
            setattr(section_obj, attr_name, var_type(value=default))


    def load(self):
        """Reads the INI file from disk and populates the Tkinter variables.

        If the file does not exist, the operation is skipped, and the 
        default fallback values defined in the schema remain active.
        """     

        if not self.filepath.exists():
            return

        self.config.read(self.filepath, encoding="utf-8")

        for section, key, var_type, attr_name, default in self.scheme:
            if self.config.has_option(section, key):
                # Read the right type from the ini-file
                if var_type is ttk.BooleanVar:
                    val = self.config.getboolean(section, key, fallback=default)
                elif var_type is ttk.IntVar:
                    val = self.config.getint(section, key, fallback=default)
                elif var_type is ttk.DoubleVar:
                    val = self.config.getfloat(section, key, fallback=default)
                else:
                    val = self.config.get(section, key, fallback=default)

                # Set the attribute via the section and set the value
                section_obj = getattr(self, section)
                var = getattr(section_obj, attr_name)
                var.set(val)

    def save(self):
        """Retrieves current values from the Tkinter variables and writes them to the INI file.

        Creates missing sections and missing parent directories automatically before saving.
        """
        for section, key, _, attr_name, _ in self.scheme:
            section_obj = getattr(self, section)
            var = getattr(section_obj, attr_name)
            val = str(var.get())

            if not self.config.has_section(section):
                self.config.add_section(section)

            self.config.set(section, key, val)

        # Make sure the target folder exists before saving. e.g. in case the ini file is stored in some subfolder
        self.filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(self.filepath, "w", encoding="utf-8") as f:
            self.config.write(f)