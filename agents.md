# AI Coding Agents Guide

## Purpose

Keep changes focused and preserve unrelated work. Do not commit unless asked.

## Project Overview

Fayna SES is a read-only Home Assistant integration for public power station dashboards.
Code lives in `custom_components/fayna_ses`.

- `api/` separates the HTTP client, constants, public models, parsing, and validation without HA dependencies.
- `coordinator.py` polls every 60 seconds and checks 30-minute data freshness.
- `config_flow.py` validates a dashboard before creating one entry per station.
- `entity.py`, `sensor.py`, and `binary_sensor.py` expose cached readings.
- Runtime data is the typed coordinator stored on `ConfigEntry.runtime_data`.
- Translations are maintained in English and Ukrainian; `strings.json` matches English.

## Workflow

- Use `uv` with the public PyPI registry and keep `uv.lock` synchronized.
- Apply the `readable-py` skill to Python changes: short focused functions, clear names, and flat control flow.
- Run `scripts/lint` after Python changes and `scripts/test` before finishing.
- Read current Home Assistant developer documentation before changing HA APIs.
- Never log complete dashboard URLs or station identifiers.
- Missing values remain unknown; stale measurements must not appear current.
- Preserve API power signs: positive grid means import, positive battery means discharge.
- Daily energy uses explicit Kyiv midnight resets; do not treat corrections as new cycles.
- Keep static capacity metadata in attributes, not separate entities.

<instruction>Keep this guide synced when tooling, workflows, or runtime data structures change.</instruction>

<important>Do not commit unless directly asked. Keep changes concise.</important>
