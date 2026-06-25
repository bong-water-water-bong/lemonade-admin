# Lemonade Admin

`lemonade-admin` is the internal-only POS/admin web shell for Lemonade Store.

It owns the package-manager web wizard, local Help Center, role-aware admin UI,
and localhost/LAN-only operator interface. The package-manager engine stays in
`lemonade-store` so the CLI and web wizard share one resolver and manifest model.

## Current capabilities

This package is still stdlib-only and intentionally small, but it is now a
usable internal admin foundation:

- internal-only access policy for localhost/private LAN hosts
- owner/admin vs attendant role gates
- Help Center routes backed by local Markdown docs
- package wizard catalog page
- package install-plan preview route backed by `lemonade-store`
- owner/admin install route backed by `lemonade-store` package manager
- package status route backed by local install state
- simple stdlib HTTP server for internal deployment
- local backup archive creation/listing/verification primitives
- verified backup restore CLI with digest and path-traversal checks

## Run locally

Preview a route from the CLI:

```sh
lemonade-admin --route /packages/plan?profile=store-operations --role admin
```

Preview a package plan:

```sh
lemonade-admin --route '/packages/plan?profile=store-operations' --role admin
```

Install from a verified local bundle through the internal app route (owner/admin only):

```text
POST /packages/install?manifest=/media/usb/lemonade-bundle.toml&profile=store-operations&key=/path/to/bundle.key&confirm=install
```

The install route requires `confirm=install` so an owner/admin has to review the
plan first. It still uses the same offline `lemonade-store` package manager as
the CLI. Include `key=/path/to/bundle.key` for signed bundle verification before
installation.

Run the internal HTTP server on localhost:

```sh
lemonade-admin --serve --host 127.0.0.1 --port 8788
```

Create, list, and restore a local backup:

```sh
lemonade-admin --backup-create --backup-path ~/.lemonade --backup-out /media/usb/backups --backup-label pre-install
lemonade-admin --backup-list --backup-out /media/usb/backups
lemonade-admin --backup-restore /media/usb/backups/<backup>.tar.gz \
  --backup-digest sha256:<digest> \
  --backup-restore-dest ./restore-check
```

Restore verifies the archive digest before extraction and rejects unsafe archive
members that try to write outside the destination directory.

For LAN use, bind to a private LAN address only. Do not expose this service to a
public hostname or public interface.

The package depends on `lemonade-store>=0.1.0` as a normal package dependency,
not a GitHub URL. Offline installs should bundle `lemonade-store` and
`lemonade-admin` wheels together.

## Roles

- `owner` / `admin`: can use package wizard and status routes.
- `attendant`: can use POS/help-center style routes, but package management is
  blocked.

The first implementation accepts the role from CLI flags or the
`X-Lemonade-Role` HTTP header so the boundary is testable. A production UI can
replace that with a local login/session layer without changing app semantics.
