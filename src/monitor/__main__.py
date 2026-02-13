"""Entry point for running the monitor as a module: python -m monitor"""

import sys
from monitor.server import main

if __name__ == "__main__":
    sys.exit(main())
