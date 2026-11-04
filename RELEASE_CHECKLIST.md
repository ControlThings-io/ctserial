# Release checklist

Prepare the release locally, then run submission steps only when authorized.
See [docs/STATUS.md](docs/STATUS.md) for actual results and remaining gaps.

## Prepare and verify

- [x] Declare GPL-3.0-or-later, matching LICENSE and source headers, as selected
      by the user for 0.6.0.
- [ ] Confirm version `0.6.0` in `pyproject.toml` and `uv.lock`.
- [ ] Replace `unreleased` in `CHANGELOG.md` with the actual publication date.
- [ ] Review the diff against the previous release and preserve unrelated work.
- [ ] Run source checks:

```bash
uv sync --locked --python 3.11
uv run python -m unittest discover -s tests -v
uv run black --check src tests
uv run isort --check-only src tests
uv lock --check
git diff --check
```

- [ ] Require passing remote CI for Python 3.11–3.14 on Linux, macOS, and Windows.
- [ ] Exercise a physical serial adapter before release; the Linux PTY test does
      not establish physical-adapter compatibility.
- [ ] Move aside old `dist/` output, build, and test both installed artifacts:

```bash
uv build
uv run --isolated --no-project --with dist/ctserial-0.6.0-py3-none-any.whl tests/smoke_test.py
uv run --isolated --no-project --with dist/ctserial-0.6.0.tar.gz tests/smoke_test.py
```

- [ ] Inspect wheel/sdist metadata for name, version, Python requirement,
      dependencies, README, and license; inspect archive contents.

## Submit and publish

- [ ] Obtain explicit authorization before committing or pushing.
- [ ] Commit the release changes with a Conventional Commit message and confirm
      a clean working tree. Push the authorized branch and obtain passing CI.
- [ ] Confirm the repository's `pypi` GitHub environment and PyPI trusted publisher
      reference `.github/workflows/publish.yml`.
- [ ] When explicitly authorized to publish, create and push the matching tag:

```bash
git tag -a v0.6.0 -m "ctserial 0.6.0"
git push origin v0.6.0
```

The tag triggers tests, distribution builds and smoke tests, attestations, PyPI
publication, and GitHub release creation. Do not reuse a published version.

## Verify publication

- [ ] Confirm the workflow succeeded and PyPI offers both archives and attestations.
- [ ] Confirm the GitHub release points to `v0.6.0`.
- [ ] Verify PyPI metadata and README, then install the published package in a
      fresh environment and exercise `ctserial --help` and a real device exchange.
- [ ] Update [docs/STATUS.md](docs/STATUS.md) with observed release evidence.
