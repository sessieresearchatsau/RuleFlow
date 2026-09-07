# Publishing to PIP

```bash
uv build
uv publish
```

The current directory layout being src/<package-name> is so that best practices are followed.

NOTE: don't forget to bump up the package version when releasing (both in the pyproject.toml AND the studio/config)
NOTE: `uv cache clean ruleflow` it may be important to clear the cache so that new versions are recognized when installing.
