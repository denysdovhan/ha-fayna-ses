# Fayna SES for Home Assistant

Read-only monitoring of power stations shared through [Fayna SES](https://fayna-ses.funs.net.ua/). Enter a station dashboard link to see connectivity, battery state, power flows, and daily energy in Home Assistant.

## Installation

Requires Home Assistant 2026.2.3 or later. This integration is not yet published in the default HACS catalog.

1. Copy `custom_components/fayna_ses` into your Home Assistant `config/custom_components` directory.
2. Restart Home Assistant.
3. Open **Settings → Devices & services → Add integration → Fayna SES**.
4. Paste a dashboard URL in the form `https://fayna-ses.funs.net.ua/s/<station-id>`.

Each station is a separate device and config entry. Adding the same station twice is prevented. No account or password is required. The dashboard link identifies the shared station; only enter links you intend to monitor.

## Entities

| Entity                     | Unit / values                                     |
| -------------------------- | ------------------------------------------------- |
| Power station connectivity | Connected / disconnected                          |
| Connection status          | Normal, partially offline, all offline, no device |
| Battery level              | %                                                 |
| Battery state              | Charging, discharging, idle                       |
| Grid power                 | W; positive import, negative export               |
| Battery power              | W; positive discharge, negative charge            |
| Solar power                | W                                                 |
| Building power             | W; loads served by this station                   |
| Last data update           | Source timestamp                                  |
| Solar energy today         | kWh                                               |
| Grid energy today          | kWh; provider-reported total                      |
| Building energy today      | kWh                                               |
| Power source               | Solar, grid, battery, idle                        |

Connection status attributes contain inverter power (kW), installed solar capacity (kW), battery capacity (kWh), and the station description. These are metadata, not additional entities. Entity names and states are translated into English and Ukrainian.

## Updates and limitations

The integration polls two public JSON feeds on `data-ses.funs.net.ua` every 60 seconds. Actual station measurements typically update about every five minutes. It uses Home Assistant's shared async HTTP client and has no additional runtime dependencies.

- Telemetry becomes unavailable when source or sample timestamps are missing or older than 30 minutes. Connectivity uses only the source timestamp, so a current offline status remains visible even when measurements stop. Last update and reported connection status remain visible after a successful fetch. HTTP or malformed-response failures make all entities unavailable; polling retries automatically.
- `NORMAL` and `PARTIAL_OFFLINE` indicate connectivity; `ALL_OFFLINE` and `NO_DEVICE` indicate disconnection. This is telemetry connectivity, not proof of mains supply. Unknown status values produce an unknown connectivity state.
- Null measurements stay unknown, never zero. Reported power values may not balance exactly. Battery state uses a ±20 W idle band; power source follows the dashboard's 50 W heuristic and is not a reliable outage detector.
- Daily totals reset at midnight in Europe/Kyiv and allow provider corrections. Grid energy's import/export accounting is undocumented; do not assume it is an import-only meter. Historical backfill, previous-day/month totals, and separate battery charge/discharge energy are not implemented.
- The public feed is undocumented and may change. Local brand images require Home Assistant 2026.3 or later. No controls, service actions, or custom automation triggers/conditions are provided; use HA's standard state and numeric-state automations.

## Removal

Open **Settings → Devices & services → Fayna SES**, select the station entry's menu, and choose **Delete**. After deleting all entries, you can remove `config/custom_components/fayna_ses` and restart Home Assistant.

## Development

Run `scripts/bootstrap`, then `scripts/lint` and `scripts/test`. Start a local Home Assistant with `scripts/develop`. Tests mock HTTP and HA setup; a real Home Assistant installation remains the final manual check.
