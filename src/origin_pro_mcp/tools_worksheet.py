"""Worksheet and workbook operations for Origin Pro MCP."""

import json
import logging
from typing import Any

from .origin_manager import origin

logger = logging.getLogger(__name__)


def create_workbook(name: str = "", template: str = "Origin") -> dict[str, Any]:
    """Create a new workbook in Origin Pro.

    Args:
        name: Long name for the workbook (optional).
        template: Workbook template name (default: "Origin").

    Returns:
        dict with workbook info including short name.
    """
    with origin.lock() as op:
        wb = op.new_book("w", lname=name, template=template)
        sname = wb.lt_prop("page.name$")
        return {
            "short_name": sname,
            "long_name": name or sname,
            "template": template,
            "num_sheets": wb.shape[0] if hasattr(wb, "shape") else 1,
        }


def create_worksheet(
    book_name: str = "",
    sheet_name: str = "",
    cols: int = 2,
) -> dict[str, Any]:
    """Create a new worksheet (or add a sheet to an existing workbook).

    Args:
        book_name: Existing workbook short name. If empty, creates a new workbook.
        sheet_name: Name for the new sheet.
        cols: Number of columns (default: 2).

    Returns:
        dict with worksheet info.
    """
    with origin.lock() as op:
        if book_name:
            wb = op.find_book("w", book_name)
            if wb is None:
                raise ValueError(f"Workbook '{book_name}' not found")
            wks = wb.add_sheet(sheet_name or None)
        else:
            wks = op.new_sheet("w", lname=sheet_name)
            wb = None

        if cols > 0:
            wks.cols = cols

        return {
            "book_name": wks.lt_prop("page.name$"),
            "sheet_name": wks.lt_prop("name$") if hasattr(wks, "lt_prop") else sheet_name,
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
    """Write data to a specific column in a worksheet.

    Args:
        book_name: Workbook short name.
        sheet_index: Sheet index (0-based).
        col_index: Column index (0-based).
        data: List of values to write.
        col_name: Column long name (optional).
        col_type: Column designation: 'X', 'Y', 'Z', 'E' (error), 'L' (label).

    Returns:
        dict confirming the operation.
    """
    with origin.lock() as op:
        wb = op.find_book("w", book_name)
        if wb is None:
            raise ValueError(f"Workbook '{book_name}' not found")

        wks = wb[sheet_index]

        # Ensure enough columns
        if col_index >= wks.cols:
            wks.cols = col_index + 1

        wks.from_list(col_index, data, col_name or None)

        # Set column type/designation
        if col_type:
            type_map = {"X": 3, "Y": 0, "Z": 5, "E": 2, "L": 4}
            if col_type.upper() in type_map:
                wks.set_label(col_index, col_type.upper(), "D")

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
    """Read data from a specific column.

    Args:
        book_name: Workbook short name.
        sheet_index: Sheet index (0-based).
        col_index: Column index (0-based).

    Returns:
        dict with column data.
    """
    with origin.lock() as op:
        wb = op.find_book("w", book_name)
        if wb is None:
            raise ValueError(f"Workbook '{book_name}' not found")

        wks = wb[sheet_index]
        data = wks.to_list(col_index)

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
    """Import a CSV/text file into a worksheet.

    Args:
        file_path: Full path to the CSV file.
        book_name: Target workbook (optional, creates new if empty).
        separator: Column separator (default: comma).

    Returns:
        dict with import result info.
    """
    with origin.lock() as op:
        if book_name:
            wb = op.find_book("w", book_name)
            if wb is None:
                raise ValueError(f"Workbook '{book_name}' not found")
        else:
            wb = None

        # Use LabTalk imASC for robust CSV import
        escaped_path = file_path.replace("\\", "\\\\")
        sep_map = {",": 44, "\t": 9, ";": 59, " ": 32}
        sep_code = sep_map.get(separator, 44)

        if book_name:
            op.lt_exec(f'win -a {book_name};')

        op.lt_exec(
            f'imASC fname:="{escaped_path}" '
            f'options.Separator.nSeparator:={sep_code};'
        )

        # Get info about the active worksheet after import
        active_book = op.get_lt_str("page.name$")
        num_cols = op.lt_int("wks.ncols")
        num_rows = op.lt_int("wks.nrows")

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
    """Import an Excel file into Origin.

    Args:
        file_path: Full path to the Excel file (.xlsx/.xls).
        sheet_name: Specific Excel sheet name to import (optional).

    Returns:
        dict with import result info.
    """
    with origin.lock() as op:
        escaped_path = file_path.replace("\\", "\\\\")

        cmd = f'impExcel fname:="{escaped_path}"'
        if sheet_name:
            cmd += f' options.sparkn:="{sheet_name}"'
        cmd += ";"

        op.lt_exec(cmd)

        active_book = op.get_lt_str("page.name$")
        num_cols = op.lt_int("wks.ncols")
        num_rows = op.lt_int("wks.nrows")

        return {
            "book_name": active_book,
            "file_path": file_path,
            "columns": num_cols,
            "rows": num_rows,
        }


def list_workbooks() -> dict[str, Any]:
    """List all open workbooks and their sheets.

    Returns:
        dict with list of workbooks.
    """
    with origin.lock() as op:
        books = []
        for pg in op.pages("w"):
            sheets = []
            try:
                for i in range(pg.shape[0]):
                    sh = pg[i]
                    sheets.append({
                        "index": i,
                        "name": sh.lt_prop("name$") if hasattr(sh, "lt_prop") else f"Sheet{i+1}",
                        "cols": sh.cols if hasattr(sh, "cols") else 0,
                    })
            except Exception:
                pass
            books.append({
                "short_name": pg.lt_prop("name$") if hasattr(pg, "lt_prop") else str(pg),
                "long_name": pg.lt_prop("page.longname$") if hasattr(pg, "lt_prop") else "",
                "sheets": sheets,
            })

        return {"workbooks": books, "count": len(books)}


def set_column_labels(
    book_name: str,
    sheet_index: int,
    labels: list[str],
    label_type: str = "L",
) -> dict[str, Any]:
    """Set labels for columns in a worksheet.

    Args:
        book_name: Workbook short name.
        sheet_index: Sheet index (0-based).
        labels: List of label strings, one per column.
        label_type: Label row type - 'L' (long name), 'U' (units),
                     'C' (comments), 'D' (designation).

    Returns:
        dict confirming the operation.
    """
    with origin.lock() as op:
        wb = op.find_book("w", book_name)
        if wb is None:
            raise ValueError(f"Workbook '{book_name}' not found")

        wks = wb[sheet_index]
        wks.set_labels(labels, type=label_type)

        return {
            "book_name": book_name,
            "sheet_index": sheet_index,
            "label_type": label_type,
            "labels_set": len(labels),
        }
