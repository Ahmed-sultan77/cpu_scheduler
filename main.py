from __future__ import annotations

import sys
import os

# ── Make sure the project root is always on the import path,
#    regardless of how or from where the script is launched.
_ROOT = os.path.dirname(os.path.abspath(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from gui.main_window import MainWindow


def main() -> None:
    """Create the application window and start the Tk event loop."""
    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()