# Developer

Developer details are separated from operator/admin help. Maintainers should keep the package-manager engine in `lemonade-store` and use `lemonade-admin` as a UI shell.

## Boundaries

- Keep core package resolution, manifests, and install state in `lemonade-store`.
- Keep internal web routes, Help Center, and role-gated admin UX in `lemonade-admin`.
- Keep runtime stdlib-only unless a later UI layer explicitly chooses a framework.

## Server adapter

`lemonade_admin.server.serve()` wraps `AdminApp` with `ThreadingHTTPServer`.
The handler passes the Host header through the internal-access policy and uses
`X-Lemonade-Role` for the first testable role boundary. Replace that header with
a local auth/session implementation before multi-user production deployment.
