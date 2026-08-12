# Outputs

Dated landscape reports, written by `/purchasing:mkt-report`. Never overwritten — a survey's value is partly in being able to see how the market moved between runs.

```
landscape-YYYY-MM-DD.md     # the report
landscape-YYYY-MM-DD.typ    # Typst source
landscape-YYYY-MM-DD.pdf    # compiled artifact
```

`/purchasing:mkt-refresh` writes a new dated set with a "Changes since <previous date>" section at the top, and leaves the previous one in place.
