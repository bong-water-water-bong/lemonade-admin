# Lemonade Admin

`lemonade-admin` is the internal-only POS/admin web shell for Lemonade Store.

It owns the package-manager web wizard, local Help Center, role-aware admin UI, and localhost/LAN-only operator interface. The package-manager engine stays in `lemonade-store` so the CLI and web wizard share one resolver and manifest model.

## Status

This initial package provides a stdlib-only internal web shell and docs index foundation. It is intentionally minimal and testable; richer FastAPI/UI work can build on the same boundaries later.
