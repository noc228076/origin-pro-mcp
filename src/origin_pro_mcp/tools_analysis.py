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
    """Perform linear regression on worksheet data."""
    origin.lt_exec(f"win -a {book_name};")
    origin.lt_exec(f"page.active = {sheet_index + 1};")

    y_range = f"col({col_y + 1})"
    x_range = f"col({col_x + 1})"

    fix_str = f"fixint:=1 fix_intcpt:={intercept_value}" if fix_intercept else ""
    origin.lt_exec(f"fitLR iy:={y_range} ix:={x_range} {fix_str};")

    return {
        "type": "linear_fit",
        "slope": origin.lt_float("fitLR.b"),
        "intercept": origin.lt_float("fitLR.a"),
        "r_squared": origin.lt_float("fitLR.COD"),
        "pearson_r": origin.lt_float("fitLR.r"),
        "std_error_slope": origin.lt_float("fitLR.bErr"),
        "std_error_intercept": origin.lt_float("fitLR.aErr"),
    }


def polynomial_fit(
    book_name: str,
    sheet_index: int = 0,
    col_x: int = 0,
    col_y: int = 1,
    order: int = 2,
) -> dict[str, Any]:
    """Perform polynomial fit on worksheet data."""
    origin.lt_exec(f"win -a {book_name};")
    origin.lt_exec(f"page.active = {sheet_index + 1};")

    y_range = f"col({col_y + 1})"
    x_range = f"col({col_x + 1})"

    origin.lt_exec(f"fitPoly iy:={y_range} ix:={x_range} polyorder:={order};")

    results = {
        "type": "polynomial_fit",
        "order": order,
        "r_squared": origin.lt_float("fitPoly.COD"),
    }

    coefficients = []
    for i in range(order + 1):
        try:
            coeff = origin.lt_float(f"fitPoly.P{i}")
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
    """Perform nonlinear curve fitting."""
    origin.lt_exec(f"win -a {book_name};")
    origin.lt_exec(f"page.active = {sheet_index + 1};")

    y_range = f"col({col_y + 1})"
    x_range = f"col({col_x + 1})"

    origin.lt_exec(f"nlbegin iy:={y_range} ix:={x_range} func:={function} iter:={max_iter};")
    origin.lt_exec("nlfit;")

    results = {
        "type": "nonlinear_fit",
        "function": function,
        "chi_squared_reduced": origin.lt_float("nlf.ChiSqr"),
        "r_squared": origin.lt_float("nlf.COD"),
        "iterations": origin.lt_int("nlf.NumIter"),
    }

    params = {}
    common_params = ["y0", "xc", "w", "A", "a", "b", "c", "t1", "t2"]
    for p in common_params:
        try:
            val = origin.lt_float(f"nlf.{p}")
            params[p] = val
        except Exception:
            continue
    results["parameters"] = params

    origin.lt_exec("nlend;")

    return results


def descriptive_statistics(
    book_name: str,
    sheet_index: int = 0,
    col_index: int = 0,
) -> dict[str, Any]:
    """Calculate descriptive statistics for a column."""
    origin.lt_exec(f"win -a {book_name};")
    origin.lt_exec(f"page.active = {sheet_index + 1};")

    data_range = f"col({col_index + 1})"
    origin.lt_exec(f"stats ix:={data_range};")

    return {
        "type": "descriptive_statistics",
        "n": origin.lt_int("stats.N"),
        "mean": origin.lt_float("stats.Mean"),
        "std_dev": origin.lt_float("stats.SD"),
        "min": origin.lt_float("stats.Min"),
        "max": origin.lt_float("stats.Max"),
        "median": origin.lt_float("stats.Median"),
        "sum": origin.lt_float("stats.Sum"),
        "variance": origin.lt_float("stats.Var"),
        "skewness": origin.lt_float("stats.Skew"),
        "kurtosis": origin.lt_float("stats.Kurt"),
    }


def fft(
    book_name: str,
    sheet_index: int = 0,
    col_index: int = 0,
    output_type: str = "magnitude",
) -> dict[str, Any]:
    """Perform Fast Fourier Transform on a data column."""
    origin.lt_exec(f"win -a {book_name};")
    origin.lt_exec(f"page.active = {sheet_index + 1};")

    data_range = f"col({col_index + 1})"
    spectrum_map = {"magnitude": 0, "phase": 1, "complex": 2, "power": 3}
    spec_type = spectrum_map.get(output_type.lower(), 0)

    origin.lt_exec(f"fft1 ix:={data_range} spectrum:={spec_type};")

    result_book = origin.get_lt_str("page.name$")

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
    """Find peaks in data."""
    origin.lt_exec(f"win -a {book_name};")
    origin.lt_exec(f"page.active = {sheet_index + 1};")

    y_range = f"col({col_y + 1})"
    method_map = {"local_max": 0, "window": 1, "first_derivative": 2}
    method_code = method_map.get(method.lower(), 0)

    cmd = f"pkFind iy:={y_range} method:={method_code}"
    if n_peaks > 0:
        cmd += f" npeaks:={n_peaks}"
    cmd += ";"

    origin.lt_exec(cmd)

    n_found = origin.lt_int("pkFind.nPeaks")

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
    """Smooth data in a column."""
    origin.lt_exec(f"win -a {book_name};")
    origin.lt_exec(f"page.active = {sheet_index + 1};")

    y_range = f"col({col_y + 1})"
    method_map = {
        "adjacent_averaging": 1, "savitzky_golay": 2,
        "percentile_filter": 3, "fft_filter": 4,
    }
    method_code = method_map.get(method.lower(), 2)

    cmd = f"smooth iy:={y_range} method:={method_code} npts:={points}"
    if method_code == 2:
        cmd += f" polyorder:={polynomial_order}"
    cmd += ";"

    origin.lt_exec(cmd)

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
    """Perform baseline correction on data."""
    origin.lt_exec(f"win -a {book_name};")
    origin.lt_exec(f"page.active = {sheet_index + 1};")

    y_range = f"col({col_y + 1})"
    origin.lt_exec(f"blauto iy:={y_range};")

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
    """Interpolate data."""
    origin.lt_exec(f"win -a {book_name};")
    origin.lt_exec(f"page.active = {sheet_index + 1};")

    y_range = f"col({col_y + 1})"
    x_range = f"col({col_x + 1})"
    method_map = {"linear": 0, "cubic_spline": 1, "bspline": 2, "akima": 3}
    method_code = method_map.get(method.lower(), 0)

    origin.lt_exec(
        f"interp1 iy:={y_range} ix:={x_range} method:={method_code} npts:={n_points};"
    )

    result_book = origin.get_lt_str("page.name$")

    return {
        "type": "interpolation",
        "method": method,
        "n_points": n_points,
        "result_book": result_book,
    }
