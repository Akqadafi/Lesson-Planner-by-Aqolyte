# Versioning, backups, and recovery

LPAPP uses Git, GitHub, semantic versions, and annotated release tags so a failed change can
be traced and safely reversed.

## Version policy

Versions use `MAJOR.MINOR.PATCH`:

- **MAJOR**: incompatible changes to saved data, public routes, or supported workflows
- **MINOR**: backward-compatible features such as a new lesson or handout capability
- **PATCH**: backward-compatible fixes, validation improvements, or documentation corrections

`VERSION` is the application version returned by `/version`. Every release updates `VERSION`
and `CHANGELOG.md` in the same commit. The matching annotated tag uses the form `v0.2.0`.

## What is backed up

- Every committed source revision is preserved in Git history.
- `main`, active feature branches, and release tags are pushed to the GitHub `origin` remote.
- Release tags provide named, immutable recovery points.
- GitHub Actions records whether the offline test suite passed for pushed release code.

Git does not back up ignored local state. `.env`, API keys, Flask sessions, generated files,
and the SQLite generation-limit database are intentionally excluded. If LPAPP is deployed,
store secrets in the host's secret manager and back up durable databases separately using
encrypted, access-controlled storage.

## Release checklist

1. Work on a focused branch and commit reviewable increments.
2. Run `python -m unittest discover -s tests -v` without live provider calls.
3. Update `VERSION` and move completed items from `Unreleased` into a dated changelog entry.
4. Merge or fast-forward the reviewed branch into `main`.
5. Push `main`, confirm GitHub Actions succeeds, then create and push an annotated tag.
6. Create a GitHub release from the matching changelog entry.

Do not rewrite published release tags or force-push shared `main`.

## Safe recovery

Inspect a release without changing a branch:

```powershell
git show v0.2.0
git switch --detach v0.2.0
```

Create a recovery branch from a known release:

```powershell
git switch -c recovery/v0.2.0 v0.2.0
```

For a bad commit already pushed to `main`, preserve history and reverse it:

```powershell
git switch main
git pull --ff-only
git revert <bad-commit-sha>
git push origin main
```

Use a release branch or a revert commit for recovery. Avoid `git reset --hard` on shared
history because it can discard work and make the remote history disagree with local copies.

After restoring code, restore compatible secrets and durable data separately, run the offline
test suite, and check `/health` and `/version` before allowing generation traffic.
