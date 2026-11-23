# Deployment dependency validation

The earlier hosted screenshot showed a requirements installation failure, but
its complete log and Python version were not provided. The underlying hosted
failure is therefore not conclusively diagnosed.

The original NumPy 2.5.4 pin has an unnecessarily high Python minimum for this
project: it cannot install on Python 3.11. The pin is now NumPy 2.2.6; none of the
project's numerical methods require the newer version.

## Checks performed

- Created a fresh Python 3.12 environment and installed `requirements.txt` with
  normal package integrity and TLS verification enabled.
- All 22 automated tests passed in that fresh environment.
- `pip check` reported no broken requirements.
- A Python 3.11 binary-only dependency-resolution dry run succeeded. This is a
  resolver check, not a claim that the full application was run on Python 3.11.
- Regenerated Q3 outputs using NumPy 2.2.6 and compared the numeric tables with
  the previous environment; values matched within 1e-12.
- Ran the app from a clean copy with only the committed compact snapshot, no raw
  cache and no local processed-data folder. It displayed the 2,990 eligible rows,
  correct departmental statistics, missing-culture handling, and filtered Q3 results.

## What still needs confirmation

The owner must rebuild/reboot the actual Streamlit app and verify the generated
website starts. Use Python 3.12 for the tested runtime. If it still fails, obtain
the first failing dependency/error and runtime version from its build log rather
than the final generic installer status. Local success and a GitHub push are not
proof of online service availability.
