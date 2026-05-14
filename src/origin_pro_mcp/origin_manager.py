"""Origin Pro COM connection manager - all COM ops run on a dedicated thread."""

import logging
import queue
import sys
import threading
from contextlib import contextmanager
from typing import Any, Callable

logger = logging.getLogger(__name__)


class OriginManager:
    """Manages the COM connection to Origin Pro 2024.

    All COM operations are dispatched to a single dedicated thread
    to avoid COM apartment threading issues when called from asyncio
    thread pool workers.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._app = None
        self._op = None
        self._connected = False
        self._com_thread = None
        self._task_queue: queue.Queue = queue.Queue()
        self._start_com_thread()

    def _start_com_thread(self):
        """Start the dedicated COM worker thread."""
        self._com_thread = threading.Thread(
            target=self._com_worker, daemon=True, name="OriginCOM"
        )
        self._com_thread.start()

    def _com_worker(self):
        """Worker loop running on the dedicated COM thread."""
        import pythoncom
        pythoncom.CoInitialize()
        try:
            while True:
                func, args, kwargs, result_queue = self._task_queue.get()
                if func is None:  # shutdown signal
                    break
                try:
                    result = func(*args, **kwargs)
                    result_queue.put(("ok", result))
                except Exception as e:
                    result_queue.put(("error", e))
        finally:
            pythoncom.CoUninitialize()

    def _run_on_com_thread(self, func: Callable, *args, **kwargs) -> Any:
        """Execute a function on the COM thread and wait for the result."""
        result_queue: queue.Queue = queue.Queue()
        self._task_queue.put((func, args, kwargs, result_queue))
        status, value = result_queue.get(timeout=60)
        if status == "error":
            raise value
        return value

    def connect(self) -> None:
        """Connect to Origin Pro via COM on the dedicated thread."""
        if self._connected:
            return

        def _do_connect():
            import win32com.client
            app = win32com.client.Dispatch("Origin.ApplicationSI")
            app.Visible = 1
            app.Execute("sec -poc 3.5")
            self._app = app
            self._connected = True
            print("Origin Pro COM connection established.", file=sys.stderr)

        self._run_on_com_thread(_do_connect)

    def disconnect(self) -> None:
        """Disconnect from Origin Pro."""
        if not self._connected:
            return

        def _do_disconnect():
            if self._app is not None:
                try:
                    self._app.Execute("exit")
                except Exception:
                    pass
                self._app = None
            self._connected = False

        try:
            self._run_on_com_thread(_do_disconnect)
        except Exception:
            pass

    def _ensure_app(self):
        """Ensure we have a COM connection (called within COM thread)."""
        if self._app is None or not self._connected:
            raise ConnectionError(
                "Not connected to Origin Pro. Call origin_connect first."
            )
        return self._app

    def lt_exec(self, script: str) -> None:
        """Execute a LabTalk script."""
        def _do(s=script):
            self._ensure_app().Execute(s)
        self._run_on_com_thread(_do)

    def lt_int(self, expr: str) -> int:
        """Evaluate a LabTalk integer expression via COM."""
        def _do(e=expr):
            app = self._ensure_app()
            # Set value via LabTalk, then retrieve
            app.Execute(f"__mcp_int = {e};")
            return app.LTGetVar("__mcp_int")
        result = self._run_on_com_thread(_do)
        return int(result) if result is not None else 0

    def lt_float(self, expr: str) -> float:
        """Evaluate a LabTalk float expression via COM."""
        def _do(e=expr):
            app = self._ensure_app()
            app.Execute(f"__mcp_float = {e};")
            return app.LTGetVar("__mcp_float")
        result = self._run_on_com_thread(_do)
        return float(result) if result is not None else 0.0

    def get_lt_str(self, var: str) -> str:
        """Get a LabTalk string variable value via COM."""
        def _do(v=var):
            app = self._ensure_app()
            return app.LTGetStrVar(v)
        result = self._run_on_com_thread(_do)
        return str(result) if result is not None else ""

    def execute(self, script: str):
        """Execute LabTalk and return the COM app for chaining (on COM thread)."""
        self.lt_exec(script)

    def new_book(self, book_type: str = "w", lname: str = "", template: str = "Origin") -> str:
        """Create a new workbook, return its short name."""
        def _do():
            app = self._ensure_app()
            page_name = app.CreatePage(2, "", template)  # 2 = worksheet page
            if lname:
                app.Execute(f'page.longname$ = "{lname}";')
            return page_name
        return self._run_on_com_thread(_do)

    def new_graph(self, template: str = "Line", lname: str = "") -> str:
        """Create a new graph page, return its short name."""
        def _do():
            app = self._ensure_app()
            page_name = app.CreatePage(3, "", template)  # 3 = graph page
            if lname:
                app.Execute(f'page.longname$ = "{lname}";')
            return page_name
        return self._run_on_com_thread(_do)

    def put_data(self, book_name: str, sheet_index: int, col_index: int,
                 data: list, col_name: str = "") -> None:
        """Write data to a worksheet column."""
        def _do():
            app = self._ensure_app()
            app.Execute(f"win -a {book_name};")
            app.Execute(f"page.active = {sheet_index + 1};")
            # Ensure enough columns
            app.Execute(f"wks.ncols = max(wks.ncols, {col_index + 1});")
            if col_name:
                escaped = col_name.replace('"', '\\"')
                app.Execute(f'col({col_index + 1})[L]$ = "{escaped}";')
            # Write data row by row
            for i, val in enumerate(data):
                if isinstance(val, str):
                    escaped = val.replace('"', '\\"')
                    app.Execute(f'col({col_index + 1})[{i + 1}]$ = "{escaped}";')
                else:
                    app.Execute(f"col({col_index + 1})[{i + 1}] = {val};")
        self._run_on_com_thread(_do)

    def get_data(self, book_name: str, sheet_index: int, col_index: int) -> list:
        """Read data from a worksheet column."""
        def _do():
            app = self._ensure_app()
            app.Execute(f"win -a {book_name};")
            app.Execute(f"page.active = {sheet_index + 1};")
            nrows = int(app.LTGetVar("wks.maxRows") or 0)
            result = []
            for i in range(1, nrows + 1):
                app.Execute(f"__mcp_float = col({col_index + 1})[{i}];")
                val = app.LTGetVar("__mcp_float")
                result.append(float(val) if val is not None else None)
            return result
        return self._run_on_com_thread(_do)


# Global singleton
origin = OriginManager()
