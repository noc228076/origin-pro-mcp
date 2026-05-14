"""Project management and export tools for Origin Pro MCP."""

import logging
import os
from typing import Any

from .origin_manager import origin

logger = logging.getLogger(__name__)


def new_project() -> dict[str, Any]:
    """Create a new blank Origin project."""
    origin.lt_exec("doc -n;")
    return {"status": "ok", "message": "New blank project created"}


def open_project(file_path: str, read_only: bool = False) -> dict[str, Any]:
    """Open an existing Origin project file (.opju/.opj)."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Project file not found: {file_path}")

    escaped_path = file_path.replace("\\", "\\\\")
    if read_only:
        origin.lt_exec(f'doc -o "{escaped_path}" readonly;')
    else:
        origin.lt_exec(f'doc -o "{escaped_path}";')

    return {
        "status": "ok",
        "file_path": file_path,
        "read_only": read_only,
    }


def save_project(file_path: str = "") -> dict[str, Any]:
    """Save the current Origin project."""
    if file_path:
        escaped_path = file_path.replace("\\", "\\\\")
        origin.lt_exec(f'doc -s "{escaped_path}";')
    else:
        origin.lt_exec("doc -s;")

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
    """Export a graph as an image file."""
    out_dir = os.path.dirname(file_path)
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)

    escaped_path = file_path.replace("\\", "\\\\")
    ext = os.path.splitext(file_path)[1].lower()

    origin.lt_exec(f"win -a {graph_name};")

    fmt_map = {
        ".png": "png", ".jpg": "jpg", ".jpeg": "jpg",
        ".bmp": "bmp", ".tif": "tif", ".tiff": "tif",
        ".pdf": "pdf", ".emf": "emf", ".eps": "eps", ".svg": "svg",
    }
    fmt = fmt_map.get(ext, "png")

    origin.lt_exec(
        f'expGraph type:={fmt} path:="{escaped_path}" '
        f'tr.Width:={width} tr.Height:={height} '
        f'resolution:={dpi};'
    )

    return {
        "status": "ok",
        "graph_name": graph_name,
        "file_path": file_path,
        "format": ext.lstrip("."),
    }


def export_all_graphs(
    output_dir: str,
    file_format: str = "png",
    dpi: int = 300,
) -> dict[str, Any]:
    """Export all graphs in the current project as images."""
    os.makedirs(output_dir, exist_ok=True)
    escaped_dir = output_dir.replace("\\", "\\\\")

    origin.lt_exec(
        f'expAllGr type:={file_format} path:="{escaped_dir}" '
        f'resolution:={dpi};'
    )

    return {
        "status": "ok",
        "output_dir": output_dir,
        "format": file_format,
    }


def run_labtalk(script: str) -> dict[str, Any]:
    """Execute arbitrary LabTalk script in Origin."""
    origin.lt_exec(script)
    return {
        "status": "ok",
        "script": script,
    }


def get_origin_info() -> dict[str, Any]:
    """Get information about the connected Origin Pro instance."""
    try:
        version = origin.get_lt_str("system.version$")
    except Exception:
        version = "unknown"

    try:
        program_path = origin.get_lt_str("system.path.program$")
    except Exception:
        program_path = "unknown"

    return {
        "version": version,
        "program_path": program_path,
    }


def delete_page(page_name: str) -> dict[str, Any]:
    """Delete (close) a page by name."""
    origin.lt_exec(f"win -cd {page_name};")
    return {
        "status": "ok",
        "deleted": page_name,
    }
