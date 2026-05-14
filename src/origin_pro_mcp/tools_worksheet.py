"""Worksheet and workbook operations for Origin Pro MCP."""

import logging
from typing import Any

from .origin_manager import origin

logger = logging.getLogger(__name__)


def create_workbook(name: str = "", template: str = "Origin") -> dict[str, Any]:
    """Create a new workbook in Origin Pro."""
    sname = origin.new_book(lname=name, template=template)
    return {
        "short_name": sname,
        "long_name": name or sname,
        "template": template,
    }


def create_worksheet(
    book_name: str = "",
    sheet_name: str = "",
    cols: int = 2,
) -> dict[str, Any]:
    """Create a new worksheet."""
    if book_name:
        # Add sheet to existing workbook
        origin.lt_exec(f"win -a {book_name};")
        origin.lt_exec("newsheet;")
        if sheet_name:
            escaped = sheet_name.replace('"', '\\"')
            origin.lt_exec(f'wks.name$ = "{escaped}";')
    else:
        book_name = origin.new_book(lname=sheet_name)

    if cols > 0:
        origin.lt_exec(f"wks.ncols = {cols};")

    return {
        "book_name": book_name,
        "sheet_name": sheet_name,
        "columns": cols,
    }


def set_column_data(
    book_name: str,
    sheet_index: int,
    col_index: int,
    data: list,
    col_name: str = "",
    col_type: str = "",
) -> dict[str, Any]:
    """Write data to a specific column in a worksheet."""
    origin.put_data(book_name, sheet_index, col_index, data, col_name)

    if col_type:
        origin.lt_exec(f"win -a {book_name};")
        origin.lt_exec(f"page.active = {sheet_index + 1};")
        type_map = {"X": "X", "Y": "Y", "Z": "Z", "E": "E", "L": "L"}
        t = type_map.get(col_type.upper(), "Y")
        origin.lt_exec(f'wks.col{col_index + 1}.type = {t};')

    return {
        "book_name": book_name,
        "sheet_index": sheet_index,
        "col_index": col_index,
        "rows_written": len(data),
        "col_name": col_name,
    }


def get_column_data(
    book_name: str,
    sheet_index: int,
    col_index: int,
) -> dict[str, Any]:
    """Read data from a specific column."""
    data = origin.get_data(book_name, sheet_index, col_index)
    return {
        "book_name": book_name,
        "sheet_index": sheet_index,
        "col_index": col_index,
        "data": data,
        "rows": len(data),
    }


def import_csv(
    file_path: str,
    book_name: str = "",
    separator: str = ",",
) -> dict[str, Any]:
    """Import a CSV/text file into a worksheet."""
    if book_name:
        origin.lt_exec(f"win -a {book_name};")

    escaped_path = file_path.replace("\\", "\\\\")
    sep_map = {",": 44, "\t": 9, ";": 59, " ": 32}
    sep_code = sep_map.get(separator, 44)

    origin.lt_exec(
        f'imASC fname:="{escaped_path}" '
        f'options.Separator.nSeparator:={sep_code};'
    )

    active_book = origin.get_lt_str("page.name$")
    num_cols = origin.lt_int("wks.ncols")
    num_rows = origin.lt_int("wks.nrows")

    return {
        "book_name": active_book,
        "file_path": file_path,
        "columns": num_cols,
        "rows": num_rows,
    }


def import_excel(
    file_path: str,
    sheet_name: str = "",
) -> dict[str, Any]:
    """Import an Excel file into Origin."""
    escaped_path = file_path.replace("\\", "\\\\")

    cmd = f'impExcel fname:="{escaped_path}"'
    if sheet_name:
        cmd += f' options.sparkn:="{sheet_name}"'
    cmd += ";"

    origin.lt_exec(cmd)

    active_book = origin.get_lt_str("page.name$")
    num_cols = origin.lt_int("wks.ncols")
    num_rows = origin.lt_int("wks.nrows")

    return {
        "book_name": active_book,
        "file_path": file_path,
        "columns": num_cols,
        "rows": num_rows,
    }


def list_workbooks() -> dict[str, Any]:
    """List all open workbooks."""
    origin.lt_exec("__mcp_int = doc.pages();")
    total_pages = origin.lt_int("__mcp_int")

    books = []
    for i in range(1, total_pages + 1):
        origin.lt_exec(f"__mcp_int = page{i}.type;")
        page_type = origin.lt_int("__mcp_int")
        if page_type == 2:  # worksheet page
            origin.lt_exec(f"__mcp_str$ = page{i}.name$;")
            sname = origin.get_lt_str("__mcp_str$")
            origin.lt_exec(f"__mcp_str$ = page{i}.longname$;")
            lname = origin.get_lt_str("__mcp_str$")
            books.append({
                "short_name": sname,
                "long_name": lname,
            })

    return {"workbooks": books, "count": len(books)}


def set_column_labels(
    book_name: str,
    sheet_index: int,
    labels: list[str],
    label_type: str = "L",
) -> dict[str, Any]:
    """Set labels for columns in a worksheet."""
    origin.lt_exec(f"win -a {book_name};")
    origin.lt_exec(f"page.active = {sheet_index + 1};")

    for i, label in enumerate(labels):
        escaped = label.replace('"', '\\"')
        origin.lt_exec(f'col({i + 1})[{label_type}]$ = "{escaped}";')

    return {
        "book_name": book_name,
        "sheet_index": sheet_index,
        "label_type": label_type,
        "labels_set": len(labels),
    }
