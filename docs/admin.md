# Admin

The admin view is for owners and delegated managers. It includes package status, package wizard, backups, restore, and local Help Center management.

Package installs use the `lemonade-store` package-manager engine.

## Current admin routes

- `/packages` lists profiles and departments.
- `/packages/plan?profile=store-operations` previews a package plan.
- `/packages/plan?profile=none&department=inventory&agent=onboarder` previews a custom plan.
- `/packages/status` reads local install state.

These routes require the `owner` or `admin` role. Attendants are denied.
