"""Graph creation and styling tools for Origin Pro MCP."""

import logging
from typing import Any

from .origin_manager import origin

logger = logging.getLogger(__name__)

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
    """Create a new graph page."""
    tmpl = template or GRAPH_TEMPLATES.get(graph_type.lower(), "Line")
    sname = origin.new_graph(template=tmpl, lname=name)
    return {
        "graph_name": sname,
        "long_name": name or sname,
        "template": tmpl,
        "graph_type": graph_type,
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
    """Add a data plot to an existing graph."""
    origin.lt_exec(f"win -a {graph_name};")
    origin.lt_exec(f"layer.active = {layer_index + 1};")

    x_range = f"[{book_name}]{sheet_index + 1}!Col({col_x + 1})"
    y_range = f"[{book_name}]{sheet_index + 1}!Col({col_y + 1})"

    if plot_type > 0:
        origin.lt_exec(f"plotxy iy:={y_range} ix:={x_range} plot:={plot_type};")
    else:
        origin.lt_exec(f"plotxy iy:={y_range} ix:={x_range};")

    origin.lt_exec("layer -a;")  # rescale

    return {
        "graph_name": graph_name,
        "layer_index": layer_index,
        "book_name": book_name,
        "col_x": col_x,
        "col_y": col_y,
    }


def set_axis_titles(
    graph_name: str,
    x_title: str = "",
    y_title: str = "",
    layer_index: int = 0,
) -> dict[str, Any]:
    """Set axis titles for a graph layer."""
    origin.lt_exec(f"win -a {graph_name};")
    origin.lt_exec(f"layer.active = {layer_index + 1};")

    if x_title:
        escaped = x_title.replace('"', '\\"')
        origin.lt_exec(f'xb.text$ = "{escaped}";')
    if y_title:
        escaped = y_title.replace('"', '\\"')
        origin.lt_exec(f'yl.text$ = "{escaped}";')

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
    """Set axis range for a graph layer."""
    origin.lt_exec(f"win -a {graph_name};")
    origin.lt_exec(f"layer.active = {layer_index + 1};")

    if x_min is not None:
        origin.lt_exec(f"layer.x.from = {x_min};")
    if x_max is not None:
        origin.lt_exec(f"layer.x.to = {x_max};")
    if y_min is not None:
        origin.lt_exec(f"layer.y.from = {y_min};")
    if y_max is not None:
        origin.lt_exec(f"layer.y.to = {y_max};")

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
    """Set visual style for a data plot."""
    origin.lt_exec(f"win -a {graph_name};")
    origin.lt_exec(f"layer.active = {layer_index + 1};")
    origin.lt_exec(f"set %C -e {plot_index + 1};")

    if line_color:
        color_val = _resolve_color(line_color)
        origin.lt_exec(f"set %C -cl color({color_val});")
    if line_width > 0:
        origin.lt_exec(f"set %C -w {line_width * 500};")
    if symbol_shape >= 0:
        origin.lt_exec(f"set %C -k {symbol_shape + 1};")
    if symbol_size > 0:
        origin.lt_exec(f"set %C -z {symbol_size};")
    if fill_color:
        color_val = _resolve_color(fill_color)
        origin.lt_exec(f"set %C -cf 1;")
        origin.lt_exec(f"set %C -c color({color_val});")

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
    """Set the title of a graph page."""
    origin.lt_exec(f"win -a {graph_name};")
    escaped = title.replace('"', '\\"')
    origin.lt_exec(f"page.title = 1;")
    origin.lt_exec(f'page.longname$ = "{escaped}";')

    return {
        "graph_name": graph_name,
        "title": title,
    }


def list_graphs() -> dict[str, Any]:
    """List all open graph pages."""
    origin.lt_exec("__mcp_int = doc.pages();")
    total_pages = origin.lt_int("__mcp_int")

    graphs = []
    for i in range(1, total_pages + 1):
        origin.lt_exec(f"__mcp_int = page{i}.type;")
        page_type = origin.lt_int("__mcp_int")
        if page_type == 3:  # graph page
            origin.lt_exec(f"__mcp_str$ = page{i}.name$;")
            sname = origin.get_lt_str("__mcp_str$")
            origin.lt_exec(f"__mcp_str$ = page{i}.longname$;")
            lname = origin.get_lt_str("__mcp_str$")
            graphs.append({
                "short_name": sname,
                "long_name": lname,
            })

    return {"graphs": graphs, "count": len(graphs)}


def rescale_graph(
    graph_name: str,
    layer_index: int = 0,
) -> dict[str, Any]:
    """Auto-rescale a graph layer to fit all data."""
    origin.lt_exec(f"win -a {graph_name};")
    origin.lt_exec(f"layer.active = {layer_index + 1};")
    origin.lt_exec("layer -a;")

    return {
        "graph_name": graph_name,
        "layer_index": layer_index,
        "rescaled": True,
    }


def _resolve_color(color_str: str) -> str:
    """Convert a color string to Origin RGB format."""
    named_colors = {
        "black": "0,0,0", "red": "255,0,0", "green": "0,128,0",
        "blue": "0,0,255", "yellow": "255,255,0", "cyan": "0,255,255",
        "magenta": "255,0,255", "white": "255,255,255", "orange": "255,165,0",
        "purple": "128,0,128", "gray": "128,128,128", "grey": "128,128,128",
        "pink": "255,192,203", "brown": "139,69,19", "navy": "0,0,128",
        "teal": "0,128,128",
    }

    color_lower = color_str.lower().strip()
    if color_lower in named_colors:
        return named_colors[color_lower]

    if color_lower.startswith("#") and len(color_lower) == 7:
        r = int(color_lower[1:3], 16)
        g = int(color_lower[3:5], 16)
        b = int(color_lower[5:7], 16)
        return f"{r},{g},{b}"

    return color_str
