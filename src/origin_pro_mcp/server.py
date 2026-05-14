"""Origin Pro 2024 MCP Server - main entry point.

Registers all tools and handles MCP protocol communication via stdio.
"""

import json
import logging
import traceback
from typing import Any

from mcp.server.fastmcp import FastMCP

from .origin_manager import origin
from . import tools_worksheet as ws
from . import tools_graph as gr
from . import tools_analysis as an
from . import tools_project as pj

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = FastMCP(
    "origin-pro-mcp",
    description="Origin Pro 2024 MCP Server - AI Agent interface for OriginLab data analysis and visualization",
)


def _ok(result: Any) -> str:
    """Format a successful result as JSON string."""
    return json.dumps(result, ensure_ascii=False, default=str)


def _err(e: Exception) -> str:
    """Format an error as JSON string."""
    return json.dumps({
        "error": str(e),
        "type": type(e).__name__,
    }, ensure_ascii=False)


# ============================================================
# Connection tools
# ============================================================

@mcp.tool()
def origin_connect() -> str:
    """Connect to Origin Pro 2024 instance. Must be called before any other operations.
    Origin Pro must be installed and licensed on this machine.
    """
    try:
        origin.connect()
        return _ok({"status": "connected", "message": "Successfully connected to Origin Pro 2024"})
    except Exception as e:
        return _err(e)


@mcp.tool()
def origin_info() -> str:
    """Get information about the connected Origin Pro instance (version, paths)."""
    try:
        return _ok(pj.get_origin_info())
    except Exception as e:
        return _err(e)


# ============================================================
# Project management tools
# ============================================================

@mcp.tool()
def project_new() -> str:
    """Create a new blank Origin project. Closes the current project."""
    try:
        return _ok(pj.new_project())
    except Exception as e:
        return _err(e)


@mcp.tool()
def project_open(file_path: str, read_only: bool = False) -> str:
    """Open an existing Origin project file (.opju or .opj).

    Args:
        file_path: Full path to the project file.
        read_only: Whether to open as read-only.
    """
    try:
        return _ok(pj.open_project(file_path, read_only))
    except Exception as e:
        return _err(e)


@mcp.tool()
def project_save(file_path: str = "") -> str:
    """Save the current Origin project.

    Args:
        file_path: Path to save to. If empty, saves to the current file path.
    """
    try:
        return _ok(pj.save_project(file_path))
    except Exception as e:
        return _err(e)


# ============================================================
# Worksheet / Workbook tools
# ============================================================

@mcp.tool()
def workbook_create(name: str = "", template: str = "Origin") -> str:
    """Create a new workbook in Origin Pro.

    Args:
        name: Long name for the workbook (optional).
        template: Workbook template name (default: "Origin").
    """
    try:
        return _ok(ws.create_workbook(name, template))
    except Exception as e:
        return _err(e)


@mcp.tool()
def worksheet_create(book_name: str = "", sheet_name: str = "", cols: int = 2) -> str:
    """Create a new worksheet. If book_name is provided, adds a sheet to that workbook;
    otherwise creates a new workbook with the sheet.

    Args:
        book_name: Existing workbook short name (optional).
        sheet_name: Name for the new sheet (optional).
        cols: Number of columns (default: 2).
    """
    try:
        return _ok(ws.create_worksheet(book_name, sheet_name, cols))
    except Exception as e:
        return _err(e)


@mcp.tool()
def worksheet_set_data(
    book_name: str,
    sheet_index: int,
    col_index: int,
    data: list,
    col_name: str = "",
    col_type: str = "",
) -> str:
    """Write data to a specific column in a worksheet.

    Args:
        book_name: Workbook short name.
        sheet_index: Sheet index (0-based).
        col_index: Column index (0-based).
        data: List of numeric or string values to write.
        col_name: Column long name (optional).
        col_type: Column designation: 'X', 'Y', 'Z', 'E' (error), 'L' (label).
    """
    try:
        return _ok(ws.set_column_data(book_name, sheet_index, col_index, data, col_name, col_type))
    except Exception as e:
        return _err(e)


@mcp.tool()
def worksheet_get_data(book_name: str, sheet_index: int, col_index: int) -> str:
    """Read data from a specific column in a worksheet.

    Args:
        book_name: Workbook short name.
        sheet_index: Sheet index (0-based).
        col_index: Column index (0-based).
    """
    try:
        return _ok(ws.get_column_data(book_name, sheet_index, col_index))
    except Exception as e:
        return _err(e)


@mcp.tool()
def worksheet_set_labels(
    book_name: str,
    sheet_index: int,
    labels: list[str],
    label_type: str = "L",
) -> str:
    """Set labels for columns in a worksheet.

    Args:
        book_name: Workbook short name.
        sheet_index: Sheet index (0-based).
        labels: List of label strings, one per column.
        label_type: 'L' (long name), 'U' (units), 'C' (comments), 'D' (designation).
    """
    try:
        return _ok(ws.set_column_labels(book_name, sheet_index, labels, label_type))
    except Exception as e:
        return _err(e)


@mcp.tool()
def worksheet_list() -> str:
    """List all open workbooks and their sheets in the current project."""
    try:
        return _ok(ws.list_workbooks())
    except Exception as e:
        return _err(e)


@mcp.tool()
def import_csv(file_path: str, book_name: str = "", separator: str = ",") -> str:
    """Import a CSV/text data file into a worksheet.

    Args:
        file_path: Full path to the CSV file.
        book_name: Target workbook short name (optional, creates new if empty).
        separator: Column separator: ',' (comma), '\\t' (tab), ';' (semicolon), ' ' (space).
    """
    try:
        return _ok(ws.import_csv(file_path, book_name, separator))
    except Exception as e:
        return _err(e)


@mcp.tool()
def import_excel(file_path: str, sheet_name: str = "") -> str:
    """Import an Excel file (.xlsx/.xls) into Origin.

    Args:
        file_path: Full path to the Excel file.
        sheet_name: Specific Excel sheet name to import (optional, imports first sheet).
    """
    try:
        return _ok(ws.import_excel(file_path, sheet_name))
    except Exception as e:
        return _err(e)


# ============================================================
# Graph tools
# ============================================================

@mcp.tool()
def graph_create(graph_type: str = "line", template: str = "", name: str = "") -> str:
    """Create a new graph page.

    Args:
        graph_type: Type of graph. Options: line, scatter, line_symbol, bar, column,
                    area, pie, histogram, box, contour, heatmap, 3d_surface,
                    3d_bar, 3d_scatter, waterfall, polar, bubble, violin, stock.
        template: Custom Origin template name (overrides graph_type if provided).
        name: Long name for the graph page (optional).
    """
    try:
        return _ok(gr.create_graph(graph_type, template, name))
    except Exception as e:
        return _err(e)


@mcp.tool()
def graph_add_plot(
    graph_name: str,
    book_name: str,
    sheet_index: int = 0,
    col_x: int = 0,
    col_y: int = 1,
    plot_type: int = 0,
    layer_index: int = 0,
) -> str:
    """Add a data plot to an existing graph from worksheet data.

    Args:
        graph_name: Graph page short name.
        book_name: Source workbook short name.
        sheet_index: Source sheet index (0-based).
        col_x: X column index (0-based).
        col_y: Y column index (0-based).
        plot_type: Plot type (0=auto, 200=line, 201=scatter, 202=line+symbol).
        layer_index: Target graph layer index (0-based).
    """
    try:
        return _ok(gr.add_plot(graph_name, book_name, sheet_index, col_x, col_y, plot_type, layer_index))
    except Exception as e:
        return _err(e)


@mcp.tool()
def graph_set_axis_titles(
    graph_name: str,
    x_title: str = "",
    y_title: str = "",
    layer_index: int = 0,
) -> str:
    """Set X and Y axis titles for a graph.

    Args:
        graph_name: Graph page short name.
        x_title: X axis title text.
        y_title: Y axis title text.
        layer_index: Graph layer index (0-based).
    """
    try:
        return _ok(gr.set_axis_titles(graph_name, x_title, y_title, layer_index))
    except Exception as e:
        return _err(e)


@mcp.tool()
def graph_set_axis_range(
    graph_name: str,
    x_min: float | None = None,
    x_max: float | None = None,
    y_min: float | None = None,
    y_max: float | None = None,
    layer_index: int = 0,
) -> str:
    """Set axis range limits for a graph.

    Args:
        graph_name: Graph page short name.
        x_min: X axis minimum value (None = no change).
        x_max: X axis maximum value (None = no change).
        y_min: Y axis minimum value (None = no change).
        y_max: Y axis maximum value (None = no change).
        layer_index: Graph layer index (0-based).
    """
    try:
        return _ok(gr.set_axis_range(graph_name, x_min, x_max, y_min, y_max, layer_index))
    except Exception as e:
        return _err(e)


@mcp.tool()
def graph_set_plot_style(
    graph_name: str,
    plot_index: int = 0,
    layer_index: int = 0,
    line_color: str = "",
    line_width: float = 0,
    symbol_shape: int = -1,
    symbol_size: float = 0,
    fill_color: str = "",
) -> str:
    """Set visual style for a data plot (color, line width, symbol, etc.).

    Args:
        graph_name: Graph page short name.
        plot_index: Plot index in the layer (0-based).
        layer_index: Graph layer index (0-based).
        line_color: Color name ("red","blue",...) or hex ("#FF0000").
        line_width: Line width in points (0 = no change).
        symbol_shape: Symbol (0=square,1=circle,2=up-triangle,3=down-triangle,
                      4=diamond,5=cross,6=star, -1=no change).
        symbol_size: Symbol size in points (0 = no change).
        fill_color: Fill color for bar/area plots.
    """
    try:
        return _ok(gr.set_plot_style(
            graph_name, plot_index, layer_index,
            line_color, line_width, symbol_shape, symbol_size, fill_color,
        ))
    except Exception as e:
        return _err(e)


@mcp.tool()
def graph_set_title(graph_name: str, title: str) -> str:
    """Set the title of a graph page.

    Args:
        graph_name: Graph page short name.
        title: Title text.
    """
    try:
        return _ok(gr.set_graph_title(graph_name, title))
    except Exception as e:
        return _err(e)


@mcp.tool()
def graph_rescale(graph_name: str, layer_index: int = 0) -> str:
    """Auto-rescale a graph layer to fit all plotted data.

    Args:
        graph_name: Graph page short name.
        layer_index: Graph layer index (0-based).
    """
    try:
        return _ok(gr.rescale_graph(graph_name, layer_index))
    except Exception as e:
        return _err(e)


@mcp.tool()
def graph_list() -> str:
    """List all open graph pages in the current project."""
    try:
        return _ok(gr.list_graphs())
    except Exception as e:
        return _err(e)


@mcp.tool()
def graph_export(
    graph_name: str,
    file_path: str,
    width: int = 800,
    height: int = 600,
    dpi: int = 300,
) -> str:
    """Export a graph as an image file (PNG, JPG, PDF, EMF, SVG, TIFF, EPS).

    Args:
        graph_name: Graph page short name.
        file_path: Output file path (extension determines format).
        width: Image width in pixels (raster formats only).
        height: Image height in pixels (raster formats only).
        dpi: Resolution in DPI (raster formats only).
    """
    try:
        return _ok(pj.export_graph(graph_name, file_path, width, height, dpi))
    except Exception as e:
        return _err(e)


@mcp.tool()
def graph_export_all(output_dir: str, file_format: str = "png", dpi: int = 300) -> str:
    """Export all graphs in the current project as image files.

    Args:
        output_dir: Directory to save the exported images.
        file_format: Image format (png, jpg, pdf, emf, svg, tiff, eps).
        dpi: Resolution in DPI.
    """
    try:
        return _ok(pj.export_all_graphs(output_dir, file_format, dpi))
    except Exception as e:
        return _err(e)


# ============================================================
# Analysis tools
# ============================================================

@mcp.tool()
def analysis_linear_fit(
    book_name: str,
    sheet_index: int = 0,
    col_x: int = 0,
    col_y: int = 1,
    fix_intercept: bool = False,
    intercept_value: float = 0.0,
) -> str:
    """Perform linear regression (y = a + b*x) on worksheet data.

    Args:
        book_name: Workbook short name.
        sheet_index: Sheet index (0-based).
        col_x: X column index (0-based).
        col_y: Y column index (0-based).
        fix_intercept: Whether to fix the intercept value.
        intercept_value: Fixed intercept value (used if fix_intercept is True).

    Returns slope, intercept, R², Pearson r, standard errors.
    """
    try:
        return _ok(an.linear_fit(book_name, sheet_index, col_x, col_y, fix_intercept, intercept_value))
    except Exception as e:
        return _err(e)


@mcp.tool()
def analysis_polynomial_fit(
    book_name: str,
    sheet_index: int = 0,
    col_x: int = 0,
    col_y: int = 1,
    order: int = 2,
) -> str:
    """Perform polynomial fit on worksheet data.

    Args:
        book_name: Workbook short name.
        sheet_index: Sheet index (0-based).
        col_x: X column index (0-based).
        col_y: Y column index (0-based).
        order: Polynomial order (2=quadratic, 3=cubic, etc.).

    Returns coefficients and R².
    """
    try:
        return _ok(an.polynomial_fit(book_name, sheet_index, col_x, col_y, order))
    except Exception as e:
        return _err(e)


@mcp.tool()
def analysis_nonlinear_fit(
    book_name: str,
    sheet_index: int = 0,
    col_x: int = 0,
    col_y: int = 1,
    function: str = "Gauss",
    max_iter: int = 200,
) -> str:
    """Perform nonlinear curve fitting on worksheet data.

    Args:
        book_name: Workbook short name.
        sheet_index: Sheet index (0-based).
        col_x: X column index (0-based).
        col_y: Y column index (0-based).
        function: Fit function name: Gauss, Lorentz, Voigt, ExpDec1, ExpDec2,
                  ExpGrow1, Boltzmann, Logistic, Sine, Power, Log, Polynomial.
        max_iter: Maximum fitting iterations.

    Returns fit parameters, chi-squared, and R².
    """
    try:
        return _ok(an.nonlinear_fit(book_name, sheet_index, col_x, col_y, function, max_iter))
    except Exception as e:
        return _err(e)


@mcp.tool()
def analysis_statistics(
    book_name: str,
    sheet_index: int = 0,
    col_index: int = 0,
) -> str:
    """Calculate descriptive statistics for a data column.

    Args:
        book_name: Workbook short name.
        sheet_index: Sheet index (0-based).
        col_index: Column index (0-based).

    Returns N, mean, std dev, min, max, median, sum, variance, skewness, kurtosis.
    """
    try:
        return _ok(an.descriptive_statistics(book_name, sheet_index, col_index))
    except Exception as e:
        return _err(e)


@mcp.tool()
def analysis_fft(
    book_name: str,
    sheet_index: int = 0,
    col_index: int = 0,
    output_type: str = "magnitude",
) -> str:
    """Perform Fast Fourier Transform (FFT) on a data column.

    Args:
        book_name: Workbook short name.
        sheet_index: Sheet index (0-based).
        col_index: Column index (0-based).
        output_type: Output type - "magnitude", "phase", "complex", "power".
    """
    try:
        return _ok(an.fft(book_name, sheet_index, col_index, output_type))
    except Exception as e:
        return _err(e)


@mcp.tool()
def analysis_peak_find(
    book_name: str,
    sheet_index: int = 0,
    col_x: int = 0,
    col_y: int = 1,
    method: str = "local_max",
    n_peaks: int = 0,
) -> str:
    """Find peaks in data.

    Args:
        book_name: Workbook short name.
        sheet_index: Sheet index (0-based).
        col_x: X column index (0-based).
        col_y: Y column index (0-based).
        method: "local_max", "window", or "first_derivative".
        n_peaks: Max number of peaks to find (0 = all).
    """
    try:
        return _ok(an.peak_find(book_name, sheet_index, col_x, col_y, method, n_peaks))
    except Exception as e:
        return _err(e)


@mcp.tool()
def analysis_smooth(
    book_name: str,
    sheet_index: int = 0,
    col_y: int = 1,
    method: str = "savitzky_golay",
    points: int = 5,
    polynomial_order: int = 2,
) -> str:
    """Smooth data in a column.

    Args:
        book_name: Workbook short name.
        sheet_index: Sheet index (0-based).
        col_y: Y column index (0-based).
        method: "adjacent_averaging", "savitzky_golay", "percentile_filter", "fft_filter".
        points: Number of smoothing points.
        polynomial_order: Polynomial order (Savitzky-Golay only).
    """
    try:
        return _ok(an.smooth_data(book_name, sheet_index, col_y, method, points, polynomial_order))
    except Exception as e:
        return _err(e)


@mcp.tool()
def analysis_baseline(
    book_name: str,
    sheet_index: int = 0,
    col_y: int = 1,
) -> str:
    """Perform automatic baseline correction on data.

    Args:
        book_name: Workbook short name.
        sheet_index: Sheet index (0-based).
        col_y: Y column index (0-based).
    """
    try:
        return _ok(an.baseline_correction(book_name, sheet_index, col_y))
    except Exception as e:
        return _err(e)


@mcp.tool()
def analysis_interpolate(
    book_name: str,
    sheet_index: int = 0,
    col_x: int = 0,
    col_y: int = 1,
    method: str = "linear",
    n_points: int = 100,
) -> str:
    """Interpolate data to generate new evenly-spaced points.

    Args:
        book_name: Workbook short name.
        sheet_index: Sheet index (0-based).
        col_x: X column index (0-based).
        col_y: Y column index (0-based).
        method: "linear", "cubic_spline", "bspline", "akima".
        n_points: Number of output points.
    """
    try:
        return _ok(an.interpolate(book_name, sheet_index, col_x, col_y, method, n_points))
    except Exception as e:
        return _err(e)


# ============================================================
# LabTalk scripting (escape hatch)
# ============================================================

@mcp.tool()
def labtalk_execute(script: str) -> str:
    """Execute arbitrary LabTalk script in Origin Pro.

    This is the escape hatch for any Origin functionality not covered by other tools.
    LabTalk is Origin's built-in scripting language with full access to all features
    including X-Functions, plot customization, batch processing, etc.

    Args:
        script: LabTalk script code to execute (can be multi-line, separated by ';').
    """
    try:
        return _ok(pj.run_labtalk(script))
    except Exception as e:
        return _err(e)


# ============================================================
# Page management
# ============================================================

@mcp.tool()
def page_delete(page_name: str) -> str:
    """Delete (close) a page (workbook, graph, matrix, etc.) by its short name.

    Args:
        page_name: Short name of the page to delete.
    """
    try:
        return _ok(pj.delete_page(page_name))
    except Exception as e:
        return _err(e)


# ============================================================
# Entry point
# ============================================================

def main():
    """Run the Origin Pro MCP server."""
    logger.info("Starting Origin Pro 2024 MCP Server...")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
