## Removed nested backend checkout

The stale nested repository formerly located at `backend_repo/python/` was removed on `2026-06-23`.

Recovery backup:

- Directory: `cleanup_backups/python-20260623-222633/`
- Bundle: `cleanup_backups/python-20260623-222633/nested-backend.bundle`
- Working tree patch: `cleanup_backups/python-20260623-222633/working-tree.patch`
- Status snapshot: `cleanup_backups/python-20260623-222633/status.txt`
- Nested repo HEAD before removal: `e389fca5c0929b61fcdc9461406bde5f6151e18d`

The preserved state is for recovery only. The active backend source tree remains `app/`, `alembic/`, `tests/`, and `scripts/`.
