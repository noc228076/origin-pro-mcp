"""Origin Pro COM connection manager - thread-safe singleton for Origin automation."""

import logging
import sys
import threading
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class OriginManager:
    """Manages the COM connection to Origin Pro 2024.

    Uses Origin.ApplicationSI to connect to a single shared instance.
    Thread-safe via a reentrant lock on all COM operations.
    """

    _instance = None
    _lock = threading.RLock()

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

    def connect(self) -> None:
        """Connect to Origin Pro via COM.

        Uses win32com directly first to ensure COM is properly initialized,
        then imports originpro which wraps the same COM connection.
        """
        with self._lock:
            if self._op is not None:
                return
            try:
                # Step 1: Initialize COM on this thread
                import pythoncom
                pythoncom.CoInitialize()

                # Step 2: Connect to Origin via COM directly to verify it works
                import win32com.client
                app = win32com.client.Dispatch("Origin.ApplicationSI")
                app.Visible = 1  # MAINWND_SHOW = 1
                app.Execute("sec -poc 3.5")  # Wait for Origin C compilation
                self._app = app

                # Step 3: Now import originpro which will attach to the same instance
                import originpro as op
                self._op = op

                # Step 4: Verify by running a simple LabTalk command
                op.lt_exec("type -q MCP Server Connected")

                print("Origin Pro COM connection established successfully.", file=sys.stderr)

            except Exception as e:
                self._op = None
                self._app = None
                raise ConnectionError(
                    f"Failed to connect to Origin Pro. "
                    f"Ensure Origin Pro 2024 is installed, licensed, and running. "
                    f"Error: {e}"
                ) from e

    def disconnect(self) -> None:
        """Disconnect from Origin Pro."""
        with self._lock:
            if self._op is not None:
                try:
                    self._op.exit()
                except Exception:
                    pass
                self._op = None
                self._app = None
                logger.info("Disconnected from Origin Pro")

    @property
    def op(self):
        """Get the originpro module (connected)."""
        if self._op is None:
            self.connect()
        return self._op

    @contextmanager
    def lock(self):
        """Context manager for thread-safe COM operations."""
        with self._lock:
            yield self.op

    def ensure_connected(self) -> bool:
        """Check connection and reconnect if needed. Returns True if connected."""
        try:
            with self._lock:
                if self._op is None:
                    self.connect()
                # Test connection with a simple call
                self._op.lt_exec("type -q Connected")
                return True
        except Exception:
            self._op = None
            self._app = None
            try:
                self.connect()
                return True
            except Exception:
                return False

    def lt_exec(self, script: str) -> None:
        """Execute a LabTalk script."""
        with self._lock:
            self.op.lt_exec(script)

    def lt_int(self, expr: str) -> int:
        """Evaluate a LabTalk expression and return an integer."""
        with self._lock:
            return self.op.lt_int(expr)

    def lt_float(self, expr: str) -> float:
        """Evaluate a LabTalk expression and return a float."""
        with self._lock:
            return self.op.lt_float(expr)

    def get_lt_str(self, var: str) -> str:
        """Get a LabTalk string variable value."""
        with self._lock:
            return self.op.get_lt_str(var)


# Global singleton
origin = OriginManager()
