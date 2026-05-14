"""Project management and export tools for Origin Pro MCP."""

import logging
import os
from typing import Any

from .origin_manager import origin

logger = logging.getLogger(__name__)


def new_project() -> dict[str, Any]:
    """Create a new blank Origin project.

    Returns:
        dict confirming the new project.
    """
    with origin.lock() as op:
        op.new()
        return {"status": "ok", "message": "New blank project created"}


def open_project(file_path: str, read_only: bool = False) -> dict[str, Any]:
    """Open an existing Origin project file (.opju/.opj).

    Args:
        file_path: Full path to the project file.
        read_only: Whether to open as read-only.

    Returns:
        dict with project info.
    """
    with origin.lock() as op:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Project file not found: {file_path}")

        op.open(file_path, readonly=read_only)
        return {
            "status": "ok",
            "file_path": file_path,
            "read_only": read_only,
        }


def save_project(file_path: str = "") -> dict[str, Any]:
    """Save the current Origin project.

    Args:
        file_path: Path to save the project to. If empty, saves to current path.

    Returns:
        dict confirming the save.
    """
    with origin.lock() as op:
        if file_path:
            op.save(file_path)
        else:
            op.save()
        return {
            "status": "ok",
            "file_path": file_path or "(current)",
        }


def export_graph(
    graph_name: str,
    file_path: str,
    width: int = 800,
    height: int = 600,
    dpi: int = 300,
) -> dict[str, Any]:
    """Export a graph as an image file.

    Supported formats: PNG, JPG, BMP, EMF, PDF, SVG, TIFF, EPS
    (determined by file extension).

    Args:
        graph_name: Graph page short name.
        file_path: Full path for the output file (extension determines format).
        width: Image width in pixels (for raster formats).
        height: Image height in pixels (for raster formats).
        dpi: Resolution in DPI (for raster formats).

    Returns:
        dict with export result info.
    """
    with origin.lock() as op:
        gp = op.find_graph(graph_name)
        if gp is None:
            raise ValueError(f"Graph '{graph_name}' not found")

        # Ensure output directory exists
        out_dir = os.path.dirname(file_path)
        if out_dir and not os.path.exists(out_dir):
            os.makedirs(out_dir, exist_ok=True)

        ext = os.path.splitext(file_path)[1].lower()

        # For vector formats, use save_fig directly
        if ext in (".pdf", ".emf", ".eps", ".svg"):
            gp.save_fig(file_path)
        else:
            # For raster formats, use LabTalk expGraph for full control
            escaped_path = file_path.replace("\\", "\\\\")
            op.lt_exec(f"win -a {graph_name};")

            fmt_map = {
                ".png": "png",
                ".jpg": "jpg",
                ".jpeg": "jpg",
                ".bmp": "bmp",
                ".tif": "tif",
                ".tiff": "tif",
            }
            fmt = fmt_map.get(ext, "png")

            op.lt_exec(
                f'expGraph type:={fmt} path:="{escaped_path}" '
                f'tr.Width:={width} tr.Height:={height} '
                f'resolution:={dpi};'
            )

        return {
            "status": "ok",
            "graph_name": graph_name,
            "file_path": file_path,
            "format": ext.lstrip("."),
            "width": width,
            "height": height,
            "dpi": dpi,
        }


def export_all_graphs(
    output_dir: str,
    file_format: str = "png",
    dpi: int = 300,
) -> dict[str, Any]:
    """Export all graphs in the current project as images.

    Args:
        output_dir: Directory to save the exported images.
        file_format: Image format (png, jpg, pdf, emf, svg, tiff, eps).
        dpi: Resolution in DPI.

    Returns:
        dict with list of exported files.
    """
    with origin.lock() as op:
        os.makedirs(output_dir, exist_ok=True)

        exported = []
        for gp in op.pages("g"):
            sname = gp.lt_prop("name$") if hasattr(gp, "lt_prop") else str(gp)
            out_path = os.path.join(output_dir, f"{sname}.{file_format}")
            try:
                gp.save_fig(out_path)
                exported.append({"graph": sname, "file": out_path})
            except Exception as e:
                exported.append({"graph": sname, "error": str(e)})

        return {
            "status": "ok",
            "output_dir": output_dir,
            "exported": exported,
            "count": len(exported),
        }


def run_labtalk(script: str) -> dict[str, Any]:
    """Execute arbitrary LabTalk script in Origin.

    This is the escape hatch for any Origin functionality not covered
    by other tools. LabTalk is Origin's scripting language with full
    access to all Origin features.

    Args:
        script: LabTalk script code to execute.

    Returns:
        dict with execution result.
    """
    with origin.lock() as op:
        op.lt_exec(script)
        return {
            "status": "ok",
            "script": script,
        }


def get_origin_info() -> dict[str, Any]:
    """Get information about the connected Origin Pro instance.

    Returns:
        dict with Origin version and path info.
    """
    with origin.lock() as op:
        try:
            version = op.get_lt_str("system.version$")
        except Exception:
            version = "unknown"

        try:
            program_path = op.path("p")
        except Exception:
            program_path = "unknown"

        try:
            user_path = op.path("u")
        except Exception:
            user_path = "unknown"

        return {
            "version": version,
            "program_path": program_path,
            "user_path": user_path,
        }


def delete_page(page_name: str) -> dict[str, Any]:
    """Delete (close) a page (workbook, graph, matrix, etc.) by name.

    Args:
        page_name: Short name of the page to delete.

    Returns:
        dict confirming deletion.
    """
    with origin.lock() as op:
        op.lt_exec(f"win -cd {page_name};")
        return {
            "status": "ok",
            "deleted": page_name,
        }
