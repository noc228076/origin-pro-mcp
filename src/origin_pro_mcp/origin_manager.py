"""Origin Pro COM connection manager - thread-safe singleton for Origin automation."""

import logging
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
        """Connect to Origin Pro via the originpro package."""
        with self._lock:
            if self._op is not None:
                return
            try:
                import originpro as op
                self._op = op
                # Make Origin visible so user can see what's happening
                op.set_show(True)
                # Wait for Origin C compilation to finish
                op.lt_exec("sec -poc 3.5")
                logger.info("Successfully connected to Origin Pro")
            except Exception as e:
                self._op = None
                raise ConnectionError(
                    f"Failed to connect to Origin Pro. "
                    f"Ensure Origin Pro 2024 is installed and licensed. Error: {e}"
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
