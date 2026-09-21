"""Shared configuration constants for BasiCoCo."""

import os

DEFAULT_PORT = 5002

# The server listens on loopback only by default: it has no authentication,
# so exposing it to the network is an explicit opt-in (BASICOCO_HOST=0.0.0.0).
DEFAULT_HOST = os.environ.get('BASICOCO_HOST', '127.0.0.1')

# Browser origins allowed to open a Socket.IO connection. By default only the
# page the server itself serves (same origin); a comma-separated list in
# BASICOCO_CORS_ORIGINS adds others. Never "*": any web page the user visits
# could otherwise drive the interpreter.
CORS_ALLOWED_ORIGINS = [o.strip() for o in os.environ.get('BASICOCO_CORS_ORIGINS', '').split(',')
                        if o.strip()] or None

LOOPBACK_HOSTS = ('127.0.0.1', 'localhost', '::1')
