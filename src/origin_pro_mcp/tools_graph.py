"""Graph creation and styling tools for Origin Pro MCP."""

import logging
from typing import Any

from .origin_manager import origin

logger = logging.getLogger(__name__)

# Mapping of friendly graph type names to Origin template names
GRAPH_TEMPLATES = {
    "line": "Line",
    "scatter": "Scatter",
    "line_symbol": "LineSymbol",
    "bar": "Bar",
    "column": "Column",
    "area": "Area",
    "pie": "Pie",
    "histogram": "Histogram",
    "box": "Box",
    "contour": "Contour",
    "heatmap": "ColorMap",
    "3d_surface": "Surface",
    "3d_bar": "3DBars",
    "3d_scatter": "3DScatter",
    "waterfall": "Waterfall",
    "polar": "Polar",
    "bubble": "Bubble",
    "violin": "Violin",
    "stock": "StockChart",
}


def create_graph(
    graph_type: str = "line",
    template: str = "",
    name: str = "",
) -> dict[str, Any]:
    """Create a new graph page in Origin Pro.

    Args:
        graph_type: Type of graph. Options: line, scatter, line_symbol, bar, column,
                     area, pie, histogram, box, contour, heatmap, 3d_surface,
                     3d_bar, 3d_scatter, waterfall, polar, bubble, violin, stock.
        template: Custom template name (overrides graph_type).
        name: Long name for the graph page (optional).

    Returns:
        dict with graph page info.
    """
    with origin.lock() as op:
        tmpl = template or GRAPH_TEMPLATES.get(graph_type.lower(), "Line")
        gp = op.new_graph(template=tmpl, lname=name or "")
        sname = gp.lt_prop("page.name$")

        return {
            "graph_name": sname,
            "long_name": name or sname,
            "template": tmpl,
            "graph_type": graph_type,
            "layers": gp.shape[0] if hasattr(gp, "shape") else 1,
        }


def add_plot(
    graph_name: str,
    book_name: str,
    sheet_index: int = 0,
    col_x: int = 0,
    col_y: int = 1,
    plot_type: int = 0,
    layer_index: int = 0,
) -> dict[str, Any]:
    """Add a data plot to an existing graph.

    Args:
        graph_name: Graph page short name.
        book_name: Source workbook short name.
        sheet_index: Source sheet index (0-based).
        col_x: X column index (0-based).
        col_y: Y column index (0-based).
        plot_type: Plot type code (0=auto from template, 200=line, 201=scatter,
                    202=line+symbol, see Origin docs for full list).
        layer_index: Target graph layer index (0-based).

    Returns:
        dict with plot info.
    """
    with origin.lock() as op:
        gp = op.find_graph(graph_name)
        if gp is None:
            raise ValueError(f"Graph '{graph_name}' not found")

        wb = op.find_book("w", book_name)
        if wb is None:
            raise ValueError(f"Workbook '{book_name}' not found")

        gl = gp[layer_index]
        wks = wb[sheet_index]

        if plot_type > 0:
            plot = gl.add_plot(wks, col_y, col_x, plot_type)
        else:
            plot = gl.add_plot(wks, col_y, col_x)

        gl.rescale()

        return {
            "graph_name": graph_name,
            "layer_index": layer_index,
            "book_name": book_name,
            "sheet_index": sheet_index,
            "col_x": col_x,
            "col_y": col_y,
        }


def set_axis_titles(
    graph_name: str,
    x_title: str = "",
    y_title: str = "",
    layer_index: int = 0,
) -> dict[str, Any]:
    """Set axis titles for a graph layer.

    Args:
        graph_name: Graph page short name.
        x_title: X axis title.
        y_title: Y axis title.
        layer_index: Graph layer index (0-based).

    Returns:
        dict confirming the operation.
    """
    with origin.lock() as op:
        gp = op.find_graph(graph_name)
        if gp is None:
            raise ValueError(f"Graph '{graph_name}' not found")

        # Use LabTalk for axis titles - most reliable approach
        op.lt_exec(f"win -a {graph_name};")
        op.lt_exec(f"layer.active = {layer_index + 1};")

        if x_title:
            escaped = x_title.replace('"', '\\"')
            op.lt_exec(f'xb.text$ = "{escaped}";')
        if y_title:
            escaped = y_title.replace('"', '\\"')
            op.lt_exec(f'yl.text$ = "{escaped}";')

        return {
            "graph_name": graph_name,
            "layer_index": layer_index,
            "x_title": x_title,
            "y_title": y_title,
        }


def set_axis_range(
    graph_name: str,
    x_min: float | None = None,
    x_max: float | None = None,
    y_min: float | None = None,
    y_max: float | None = None,
    layer_index: int = 0,
) -> dict[str, Any]:
    """Set axis range for a graph layer.

    Args:
        graph_name: Graph page short name.
        x_min, x_max: X axis range limits.
        y_min, y_max: Y axis range limits.
        layer_index: Graph layer index (0-based).

    Returns:
        dict confirming the operation.
    """
    with origin.lock() as op:
        op.lt_exec(f"win -a {graph_name};")
        op.lt_exec(f"layer.active = {layer_index + 1};")

        if x_min is not None:
            op.lt_exec(f"layer.x.from = {x_min};")
        if x_max is not None:
            op.lt_exec(f"layer.x.to = {x_max};")
        if y_min is not None:
            op.lt_exec(f"layer.y.from = {y_min};")
        if y_max is not None:
            op.lt_exec(f"layer.y.to = {y_max};")

        return {
            "graph_name": graph_name,
            "layer_index": layer_index,
            "x_range": [x_min, x_max],
            "y_range": [y_min, y_max],
        }


def set_plot_style(
    graph_name: str,
    plot_index: int = 0,
    layer_index: int = 0,
    line_color: str = "",
    line_width: float = 0,
    symbol_shape: int = -1,
    symbol_size: float = 0,
    fill_color: str = "",
) -> dict[str, Any]:
    """Set visual style for a data plot.

    Args:
        graph_name: Graph page short name.
        plot_index: Plot index in the layer (0-based).
        layer_index: Graph layer index (0-based).
        line_color: Line color name or RGB hex (e.g., "red", "#FF0000").
        line_width: Line width in points (0 = no change).
        symbol_shape: Symbol shape (0=square, 1=circle, 2=up triangle,
                       3=down triangle, 4=diamond, 5=cross, 6=star, -1=no change).
        symbol_size: Symbol size in points (0 = no change).
        fill_color: Fill color for bar/area plots.

    Returns:
        dict confirming the operation.
    """
    with origin.lock() as op:
        op.lt_exec(f"win -a {graph_name};")
        op.lt_exec(f"layer.active = {layer_index + 1};")

        # Activate the specific plot
        op.lt_exec(f"set %C -e {plot_index + 1};")

        if line_color:
            color_val = _resolve_color(line_color, op)
            op.lt_exec(f"set %C -cl color({color_val});")
        if line_width > 0:
            op.lt_exec(f"set %C -w {line_width * 500};")  # Origin uses 500ths of a point
        if symbol_shape >= 0:
            op.lt_exec(f"set %C -k {symbol_shape + 1};")
        if symbol_size > 0:
            op.lt_exec(f"set %C -z {symbol_size};")
        if fill_color:
            color_val = _resolve_color(fill_color, op)
            op.lt_exec(f"set %C -cf 1;")
            op.lt_exec(f"set %C -c color({color_val});")

        return {
            "graph_name": graph_name,
            "layer_index": layer_index,
            "plot_index": plot_index,
            "styles_applied": True,
        }


def set_graph_title(
    graph_name: str,
    title: str,
) -> dict[str, Any]:
    """Set the title of a graph page.

    Args:
        graph_name: Graph page short name.
        title: Title text.

    Returns:
        dict confirming the operation.
    """
    with origin.lock() as op:
        op.lt_exec(f"win -a {graph_name};")
        escaped = title.replace('"', '\\"')
        # Add or update graph title using LabTalk text label
        op.lt_exec(f'label -s -n Legend "{escaped}";')
        op.lt_exec(f"page.title = 1;")
        op.lt_exec(f'page.longname$ = "{escaped}";')

        return {
            "graph_name": graph_name,
            "title": title,
        }


def list_graphs() -> dict[str, Any]:
    """List all open graph pages.

    Returns:
        dict with list of graphs.
    """
    with origin.lock() as op:
        graphs = []
        for gp in op.pages("g"):
            sname = gp.lt_prop("name$") if hasattr(gp, "lt_prop") else str(gp)
            lname = gp.lt_prop("page.longname$") if hasattr(gp, "lt_prop") else ""
            layers = gp.shape[0] if hasattr(gp, "shape") else 1
            graphs.append({
                "short_name": sname,
                "long_name": lname,
                "layers": layers,
            })

        return {"graphs": graphs, "count": len(graphs)}


def rescale_graph(
    graph_name: str,
    layer_index: int = 0,
) -> dict[str, Any]:
    """Auto-rescale a graph layer to fit all data.

    Args:
        graph_name: Graph page short name.
        layer_index: Graph layer index (0-based).

    Returns:
        dict confirming the operation.
    """
    with origin.lock() as op:
        gp = op.find_graph(graph_name)
        if gp is None:
            raise ValueError(f"Graph '{graph_name}' not found")
        gl = gp[layer_index]
        gl.rescale()

        return {
            "graph_name": graph_name,
            "layer_index": layer_index,
            "rescaled": True,
        }


def _resolve_color(color_str: str, op) -> str:
    """Convert a color string to Origin color code."""
    named_colors = {
        "black": "0,0,0",
        "red": "255,0,0",
        "green": "0,128,0",
        "blue": "0,0,255",
        "yellow": "255,255,0",
        "cyan": "0,255,255",
        "magenta": "255,0,255",
        "white": "255,255,255",
        "orange": "255,165,0",
        "purple": "128,0,128",
        "gray": "128,128,128",
        "grey": "128,128,128",
        "pink": "255,192,203",
        "brown": "139,69,19",
        "navy": "0,0,128",
        "teal": "0,128,128",
    }

    color_lower = color_str.lower().strip()
    if color_lower in named_colors:
        return named_colors[color_lower]

    # Handle hex color
    if color_lower.startswith("#") and len(color_lower) == 7:
        r = int(color_lower[1:3], 16)
        g = int(color_lower[3:5], 16)
        b = int(color_lower[5:7], 16)
        return f"{r},{g},{b}"

    return color_str
