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
- package status route backed by local install state
- simple stdlib HTTP server for internal deployment

## Run locally

Preview a route from the CLI:

```sh
lemonade-admin --route /packages/plan?profile=store-operations --role admin
```

Run the internal HTTP server on localhost:

```sh
lemonade-admin --serve --host 127.0.0.1 --port 8788
```

For LAN use, bind to a private LAN address only. Do not expose this service to a
public hostname or public interface.

## Roles

- `owner` / `admin`: can use package wizard and status routes.
- `attendant`: can use POS/help-center style routes, but package management is
  blocked.

The first implementation accepts the role from CLI flags or the
`X-Lemonade-Role` HTTP header so the boundary is testable. A production UI can
replace that with a local login/session layer without changing app semantics.
