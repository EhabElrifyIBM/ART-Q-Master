"""
ART Q Master — application version.

Single source of truth.  Import this wherever you need the version string:

    from version import __version__, version_label

"""

# ── Semantic version ──────────────────────────────────────────────────────────
VERSION_MAJOR: int = 2
VERSION_MINOR: int = 0
VERSION_PATCH: int = 1

__version__: str = f"{VERSION_MAJOR}.{VERSION_MINOR}.{VERSION_PATCH}"

# ── Human-readable labels ─────────────────────────────────────────────────────
APP_NAME: str = "ART Q Master"

#: Short label shown in UI headers / titles  →  "ART Q Master v2.0.0"
version_label: str = f"{APP_NAME} v{__version__}"

#: One-line string suitable for a footer  →  "ART Q Master v2.0.0 • IBM Carbon Design"
footer_label: str = f"{version_label} • IBM Carbon Design"

#: Window title suffix  →  "v2.0.0"
version_tag: str = f"v{__version__}"
