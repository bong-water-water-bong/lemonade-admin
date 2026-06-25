# Admin

The admin view is for owners and delegated managers. It includes package status, package wizard, backups, restore, and local Help Center management.

Package installs use the `lemonade-store` package-manager engine.

## Current admin routes

- `/packages` lists profiles and departments.
- `/packages/plan?profile=store-operations` previews a package plan.
- `/packages/plan?profile=none&department=inventory&agent=onboarder` previews a custom plan.
- `POST /packages/install?manifest=/media/usb/lemonade-bundle.toml&profile=store-operations&key=/path/to/bundle.key&confirm=install` installs after explicit confirmation and signed-manifest verification.
- `/packages/status` reads local install state.
- `/backups` lists local backup records from `LEMONADE_BACKUP_DIR` or `~/.lemonade/backups`.

These routes require the `owner` or `admin` role. Attendants are denied. The
install route requires `confirm=install`; owners/admins should preview the plan,
create a backup, and provide the bundle key before posting to that route.

## Backup CLI

Create a local backup before package changes:

```sh
lemonade-admin --backup-create --backup-path ~/.lemonade --backup-out /media/usb/backups --backup-label pre-install
```

List backup records:

```sh
lemonade-admin --backup-list --backup-out /media/usb/backups
```

Verify and restore an archive into a destination directory:

```sh
lemonade-admin --backup-restore /media/usb/backups/<backup>.tar.gz \
  --backup-digest sha256:<digest> \
  --backup-restore-dest ./restore-check
```

Restore refuses digest mismatches and unsafe archive paths.
