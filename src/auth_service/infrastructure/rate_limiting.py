"""Shared slowapi Limiter instance.

Lives in its own module (not in main.py) so routers can import it without
creating a circular import (main.py needs to import the routers too).
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
