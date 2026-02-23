"""
Network Configuration Module
=============================
Provides sensible networking defaults for a local Kind cluster.
"""


def create_development_network() -> dict:
    """Return Kind networking settings suitable for local development.

    The returned dictionary is passed directly into the Kind cluster
    configuration under the ``networking`` key.
    """
    return {
        "podSubnet": "10.244.0.0/16",
        "serviceSubnet": "10.96.0.0/16",
        "disableDefaultCNI": False,
        "apiServerAddress": "127.0.0.1",
        "apiServerPort": 6443,
    }
