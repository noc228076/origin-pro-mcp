"""Data analysis tools for Origin Pro MCP - fitting, statistics, FFT, peak analysis."""

import logging
from typing import Any

from .origin_manager import origin

logger = logging.getLogger(__name__)


def linear_fit(
    book_name: str,
    sheet_index: int = 0,
    col_x: int = 0,
    col_y: int = 1,
    fix_intercept: bool = False,
    intercept_value: float = 0.0,
) -> dict[str, Any]:
    """Perform linear regression on worksheet data.

    Args:
        book_name: Workbook short name.
        sheet_index: Sheet index (0-based).
        col_x: X column index (0-based).
        col_y: Y column index (0-based).
        fix_intercept: Whether to fix the intercept.
        intercept_value: Fixed intercept value (if fix_intercept is True).

    Returns:
        dict with fit results (slope, intercept, R², etc.).
    """
    with origin.lock() as op:
        wb = op.find_book("w", book_name)
        if wb is None:
            raise ValueError(f"Workbook '{book_name}' not found")

        wks = wb[sheet_index]
        sname = wks.lt_prop("page.name$") if hasattr(wks, "lt_prop") else book_name

        # Activate the worksheet
        op.lt_exec(f"win -a {book_name};")

        # Build range strings
        x_range = f"[{book_name}]{sheet_index + 1}!Col({col_x + 1})"
        y_range = f"[{book_name}]{sheet_index + 1}!Col({col_y + 1})"

        # Execute linear fit via LabTalk
        fix_str = f"fixint:=1 fix_intcpt:={intercept_value}" if fix_intercept else ""
        op.lt_exec(f"fitLR iy:={y_range} ix:={x_range} {fix_str};")

        # Retrieve results from LabTalk system variables
        results = {
            "type": "linear_fit",
            "slope": op.lt_float("fitLR.b"),
            "intercept": op.lt_float("fitLR.a"),
            "r_squared": op.lt_float("fitLR.COD"),
            "pearson_r": op.lt_float("fitLR.r"),
            "std_error_slope": op.lt_float("fitLR.bErr"),
            "std_error_intercept": op.lt_float("fitLR.aErr"),
        }

        return results


def polynomial_fit(
    book_name: str,
    sheet_index: int = 0,
    col_x: int = 0,
    col_y: int = 1,
    order: int = 2,
) -> dict[str, Any]:
    """Perform polynomial fit on worksheet data.

    Args:
        book_name: Workbook short name.
        sheet_index: Sheet index (0-based).
        col_x: X column index.
        col_y: Y column index.
        order: Polynomial order (2=quadratic, 3=cubic, etc.).

    Returns:
        dict with fit results.
    """
    with origin.lock() as op:
        op.lt_exec(f"win -a {book_name};")

        y_range = f"[{book_name}]{sheet_index + 1}!Col({col_y + 1})"
        x_range = f"[{book_name}]{sheet_index + 1}!Col({col_x + 1})"

        op.lt_exec(f"fitPoly iy:={y_range} ix:={x_range} polyorder:={order};")

        results = {
            "type": "polynomial_fit",
            "order": order,
            "r_squared": op.lt_float("fitPoly.COD"),
            "adj_r_squared": op.lt_float("fitPoly.AdjCOD"),
        }

        # Retrieve coefficients
        coefficients = []
        for i in range(order + 1):
            try:
                coeff = op.lt_float(f"fitPoly.P{i}")
                coefficients.append(coeff)
            except Exception:
                break
        results["coefficients"] = coefficients

        return results


def nonlinear_fit(
    book_name: str,
    sheet_index: int = 0,
    col_x: int = 0,
    col_y: int = 1,
    function: str = "Gauss",
    max_iter: int = 200,
) -> dict[str, Any]:
    """Perform nonlinear curve fitting.

    Args:
        book_name: Workbook short name.
        sheet_index: Sheet index (0-based).
        col_x: X column index.
        col_y: Y column index.
        function: Fit function name. Common options:
                   Gauss, Lorentz, Voigt, ExpDec1, ExpDec2, ExpGrow1,
                   Boltzmann, Logistic, Sine, Power, Log, Polynomial.
        max_iter: Maximum number of iterations.

    Returns:
        dict with fit results.
    """
    with origin.lock() as op:
        op.lt_exec(f"win -a {book_name};")

        y_range = f"[{book_name}]{sheet_index + 1}!Col({col_y + 1})"
        x_range = f"[{book_name}]{sheet_index + 1}!Col({col_x + 1})"

        # Use nlbegin/nlfit/nlend workflow
        op.lt_exec(f'nlbegin iy:={y_range} ix:={x_range} func:={function} iter:={max_iter};')
        op.lt_exec("nlfit;")

        results = {
            "type": "nonlinear_fit",
            "function": function,
            "chi_squared_reduced": op.lt_float("nlf.ChiSqr"),
            "r_squared": op.lt_float("nlf.COD"),
            "iterations": op.lt_int("nlf.NumIter"),
        }

        # Try to get parameters (function-dependent)
        params = {}
        common_params = ["y0", "xc", "w", "A", "a", "b", "c", "t1", "t2"]
        for p in common_params:
            try:
                val = op.lt_float(f"nlf.{p}")
                params[p] = val
            except Exception:
                continue
        results["parameters"] = params

        op.lt_exec("nlend;")

        return results


def descriptive_statistics(
    book_name: str,
    sheet_index: int = 0,
    col_index: int = 0,
) -> dict[str, Any]:
    """Calculate descriptive statistics for a column.

    Args:
        book_name: Workbook short name.
        sheet_index: Sheet index (0-based).
        col_index: Column index (0-based).

    Returns:
        dict with statistical measures.
    """
    with origin.lock() as op:
        op.lt_exec(f"win -a {book_name};")

        data_range = f"[{book_name}]{sheet_index + 1}!Col({col_index + 1})"
        op.lt_exec(f"stats ix:={data_range};")

        results = {
            "type": "descriptive_statistics",
            "n": op.lt_int("stats.N"),
            "mean": op.lt_float("stats.Mean"),
            "std_dev": op.lt_float("stats.SD"),
            "min": op.lt_float("stats.Min"),
            "max": op.lt_float("stats.Max"),
            "median": op.lt_float("stats.Median"),
            "sum": op.lt_float("stats.Sum"),
            "variance": op.lt_float("stats.Var"),
            "skewness": op.lt_float("stats.Skew"),
            "kurtosis": op.lt_float("stats.Kurt"),
        }

        return results


def fft(
    book_name: str,
    sheet_index: int = 0,
    col_index: int = 0,
    output_type: str = "magnitude",
) -> dict[str, Any]:
    """Perform Fast Fourier Transform on a data column.

    Args:
        book_name: Workbook short name.
        sheet_index: Sheet index (0-based).
        col_index: Column index (0-based).
        output_type: Output type - "magnitude", "phase", "complex", "power".

    Returns:
        dict with FFT result location.
    """
    with origin.lock() as op:
        op.lt_exec(f"win -a {book_name};")

        data_range = f"[{book_name}]{sheet_index + 1}!Col({col_index + 1})"

        # Map output type
        spectrum_map = {
            "magnitude": 0,
            "phase": 1,
            "complex": 2,
            "power": 3,
        }
        spec_type = spectrum_map.get(output_type.lower(), 0)

        op.lt_exec(
            f"fft1 ix:={data_range} spectrum:={spec_type};"
        )

        result_book = op.get_lt_str("page.name$")

        return {
            "type": "fft",
            "source_book": book_name,
            "result_book": result_book,
            "output_type": output_type,
        }


def peak_find(
    book_name: str,
    sheet_index: int = 0,
    col_x: int = 0,
    col_y: int = 1,
    method: str = "local_max",
    n_peaks: int = 0,
) -> dict[str, Any]:
    """Find peaks in data.

    Args:
        book_name: Workbook short name.
        sheet_index: Sheet index (0-based).
        col_x: X column index.
        col_y: Y column index.
        method: Peak finding method - "local_max", "window", "first_derivative".
        n_peaks: Maximum number of peaks to find (0 = all).

    Returns:
        dict with peak positions and info.
    """
    with origin.lock() as op:
        op.lt_exec(f"win -a {book_name};")

        y_range = f"[{book_name}]{sheet_index + 1}!Col({col_y + 1})"

        method_map = {
            "local_max": 0,
            "window": 1,
            "first_derivative": 2,
        }
        method_code = method_map.get(method.lower(), 0)

        cmd = f"pkFind iy:={y_range} method:={method_code}"
        if n_peaks > 0:
            cmd += f" npeaks:={n_peaks}"
        cmd += ";"

        op.lt_exec(cmd)

        # Retrieve number of peaks found
        n_found = op.lt_int("pkFind.nPeaks")

        return {
            "type": "peak_find",
            "method": method,
            "peaks_found": n_found,
            "source_book": book_name,
        }


def smooth_data(
    book_name: str,
    sheet_index: int = 0,
    col_y: int = 1,
    method: str = "savitzky_golay",
    points: int = 5,
    polynomial_order: int = 2,
) -> dict[str, Any]:
    """Smooth data in a column.

    Args:
        book_name: Workbook short name.
        sheet_index: Sheet index (0-based).
        col_y: Y column index.
        method: Smoothing method - "adjacent_averaging", "savitzky_golay",
                "percentile_filter", "fft_filter".
        points: Number of smoothing points.
        polynomial_order: Polynomial order (for Savitzky-Golay only).

    Returns:
        dict with smoothing result info.
    """
    with origin.lock() as op:
        op.lt_exec(f"win -a {book_name};")

        y_range = f"[{book_name}]{sheet_index + 1}!Col({col_y + 1})"

        method_map = {
            "adjacent_averaging": 1,
            "savitzky_golay": 2,
            "percentile_filter": 3,
            "fft_filter": 4,
        }
        method_code = method_map.get(method.lower(), 2)

        cmd = f"smooth iy:={y_range} method:={method_code} npts:={points}"
        if method_code == 2:
            cmd += f" polyorder:={polynomial_order}"
        cmd += ";"

        op.lt_exec(cmd)

        return {
            "type": "smooth",
            "method": method,
            "points": points,
            "source_book": book_name,
        }


def baseline_correction(
    book_name: str,
    sheet_index: int = 0,
    col_y: int = 1,
) -> dict[str, Any]:
    """Perform baseline correction on data.

    Args:
        book_name: Workbook short name.
        sheet_index: Sheet index (0-based).
        col_y: Y column index.

    Returns:
        dict with result info.
    """
    with origin.lock() as op:
        op.lt_exec(f"win -a {book_name};")

        y_range = f"[{book_name}]{sheet_index + 1}!Col({col_y + 1})"
        op.lt_exec(f"blauto iy:={y_range};")

        return {
            "type": "baseline_correction",
            "source_book": book_name,
            "col_y": col_y,
        }


def interpolate(
    book_name: str,
    sheet_index: int = 0,
    col_x: int = 0,
    col_y: int = 1,
    method: str = "linear",
    n_points: int = 100,
) -> dict[str, Any]:
    """Interpolate/extrapolate data.

    Args:
        book_name: Workbook short name.
        sheet_index: Sheet index (0-based).
        col_x: X column index.
        col_y: Y column index.
        method: Interpolation method - "linear", "cubic_spline", "bspline", "akima".
        n_points: Number of output points.

    Returns:
        dict with interpolation result info.
    """
    with origin.lock() as op:
        op.lt_exec(f"win -a {book_name};")

        y_range = f"[{book_name}]{sheet_index + 1}!Col({col_y + 1})"
        x_range = f"[{book_name}]{sheet_index + 1}!Col({col_x + 1})"

        method_map = {
            "linear": 0,
            "cubic_spline": 1,
            "bspline": 2,
            "akima": 3,
        }
        method_code = method_map.get(method.lower(), 0)

        op.lt_exec(
            f"interp1 iy:={y_range} ix:={x_range} method:={method_code} npts:={n_points};"
        )

        result_book = op.get_lt_str("page.name$")

        return {
            "type": "interpolation",
            "method": method,
            "n_points": n_points,
            "result_book": result_book,
        }
