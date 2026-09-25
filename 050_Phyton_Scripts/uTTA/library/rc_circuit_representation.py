#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module Name:    rc_circuit_representation.py
Description:    Provides functions to draw Cauer and Foster thermal RC network schematics using Schemdraw and Matplotlib.

Author:         wtronics
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
import matplotlib.pyplot as plt
import schemdraw
import schemdraw.elements as elm
from matplotlib.figure import Figure
from quantiphy import Quantity

def draw_cauer_rc_network(num_elements: int, RValues: list[float], CValues: list[float]) -> Figure:
    """ Renders a Cauer-type thermal RC network diagram using Schemdraw.

    Args:
        num_elements (int): Number of ladder stages to draw.
        RValues (list[float]): Thermal resistance values (K/W).
        CValues (list[float]): Thermal capacitance values (Ws/K).

    Returns:
        Figure: Matplotlib figure containing the generated schematic.
    """
    # Prevent GUI pop-ups during rendering
    plt.ioff() 

    d = schemdraw.Drawing(backend="matplotlib")
    d.config(unit=2.5, fontsize=9)

    p_src = d.add(elm.SourceI().down().reverse().label("$P_{th}$", "top"))
    d += elm.Ground()

    d.add(elm.Line().right().at(p_src.start).length(d.unit))
    d += elm.Dot().label("$T_{J}$", "top")

    for i in range(num_elements):
        R_label = f"$R_{{th {i+1}}}$"
        C_label = f"$C_{{th {i+1}}}$"
        Node_label = f"$T_{{th {i+1}}}$"

        if i < len(CValues):
            c_str = f"{C_label}\n\n{Quantity(CValues[i])} $\\frac{{Ws}}{{K}}$"
            C = d.add(elm.Capacitor().down().label(c_str, "bottom", halign="left"))
        else:
            C = d.add(elm.Capacitor().down().label(C_label, "bottom"))
        d.add(elm.Ground())

        if i < len(RValues):
            r_val_str = f"{Quantity(RValues[i])} $\\frac{{K}}{{W}}$"
            R = d.add(elm.ResistorIEC().right().at(C.start)
                .label(R_label, loc="top").label(r_val_str, loc="bottom"))
        else:
            R = d.add(elm.ResistorIEC().right().at(C.start)
                .label(R_label, loc="top"))

        if i < num_elements - 1:
            d.add(elm.Dot().at(R.end).label(Node_label, "top"))

    d.add(elm.Label().label("$T_{amb}$", "top"))
    d.add(elm.Line().down().length(d.unit))
    d.add(elm.Ground())

    # IMPORTANT: draw(show=False) creates and fills the matplotlib figure
    res = d.draw(show=False)
    return res.fig # type: ignore


def draw_foster_rc_network(num_elements: int, RValues: list[float], CValues: list[float]) -> Figure:
    """Renders a Foster-type thermal RC network diagram using Schemdraw.

    Args:
        num_elements (int): Number of series RC stages to draw.
        RValues (list[float]): Thermal resistance values (K/W).
        CValues (list[float]): Thermal capacitance values (Ws/K).

    Returns:
        Figure: Matplotlib figure containing the generated schematic.
    """
    # Prevent GUI pop-ups during rendering
    plt.ioff()

    d = schemdraw.Drawing(backend="matplotlib")
    d.config(unit=2.5, fontsize=9)

    p_src = d.add(elm.SourceI().down().reverse().label("$P_{th}$", "top"))
    d.add(elm.Line().down().length(d.unit / 2)) # type: ignore
    d += elm.Ground()

    d.add(elm.Line().right().at(p_src.start).length(d.unit))
    d.add(elm.Dot().label("$T_{J}$", "top"))

    for i in range(num_elements):
        R_label = f"$R_{{th {i+1}}}$"
        C_label = f"$C_{{th {i+1}}}$"

        if i < len(RValues):
            r_val_str = f"{Quantity(RValues[i])} $\\frac{{K}}{{W}}$"
            R = d.add(
                elm.ResistorIEC().right()
                .label(R_label, "top").label(r_val_str, "bottom").length(d.unit))
        else:
            R = d.add(elm.ResistorIEC().right().label(R_label, "top").length(d.unit))

        if i < num_elements - 1:
            d.add(elm.Dot().label(f"$T_{{th {i+1}}}$", "top"))

        d.add(elm.Line().down().at(R.start).length(d.unit))

        if i < len(CValues):
            c_val_str = f"{Quantity(CValues[i])} $\\frac{{Ws}}{{K}}$"
            d.add(elm.Capacitor().right()
                .label(C_label, "top").label(c_val_str, "bottom").length(d.unit))
        else:
            d.add(elm.Capacitor().right()
                .label(C_label, "top").length(d.unit))

        d.add(elm.Dot())
        d.here = (d.here[0], d.here[1] + d.unit) # type: ignore

    d.add(elm.Line().down().length(1.5 * d.unit)) # type: ignore
    d += elm.Ground()

    # IMPORTANT: draw(show=False) creates and fills the matplotlib figure
    res = d.draw(show=False)
    return res.fig # type: ignore
