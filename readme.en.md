[![SWUbanner](https://raw.githubusercontent.com/vshymanskyy/StandWithUkraine/main/banner-direct-single.svg)](https://stand-with-ukraine.pp.ua/)

<p align="center">
  <img src="./custom_components/fayna_ses/brand/icon.png#gh-light-mode-only" alt="Fayna SES" />
  <img src="./custom_components/fayna_ses/brand/dark_icon.png#gh-dark-mode-only" alt="Fayna SES" />
</p>

# ☀️ Fayna SES for Home Assistant

[![GitHub Release][gh-release-image]][gh-release-url]
[![GitHub Downloads][gh-downloads-image]][gh-downloads-url]
[![hacs][hacs-image]][hacs-url]
[![GitHub Sponsors][gh-sponsors-image]][gh-sponsors-url]
[![Buy Me A Coffee][buymeacoffee-image]][buymeacoffee-url]
[![Twitter][twitter-image]][twitter-url]

[Українською](./readme.md) | [**English**](./readme.en.md)

Monitor [Fayna SES][fayna-ses] power stations in [Home Assistant][home-assistant]: battery, power flows, daily energy, and connectivity. Connect using a public station dashboard link. No account required.

## About the project

**Fayna SES** is an energy independence and backup power project implemented by residents and KAN Development at the [Fayna Town](https://faynatown.com.ua/) residential complex in Kyiv. Watch the project video:

[![Watch the Fayna SES video on YouTube](https://img.youtube.com/vi/989Uze7SJAc/hqdefault.jpg)](https://youtu.be/989Uze7SJAc)

## Sponsorship

Your generosity will help me maintain and develop more projects like this one.

- 💖 [Sponsor on GitHub][gh-sponsors-url]
- ☕️ [Buy Me A Coffee][buymeacoffee-url]
- Bitcoin: `bc1q7lfx6de8jrqt8mcds974l6nrsguhd6u30c6sg8`
- Ethereum: `0x6aF39C917359897ae6969Ad682C14110afe1a0a1`

## Installation

Requires Home Assistant **2026.2.3+**. Integration icons require **2026.3**.

Add the custom repository to HACS, install the integration, and restart Home Assistant.

[![Add to HACS][hacs-install-image]][hacs-install-url]

<details>
<summary>Add the repository to HACS manually</summary>

1. Open **HACS → ⋮ → Custom repositories**.
2. Enter `https://github.com/denysdovhan/ha-fayna-ses` and select **Integration**.
3. Download **Fayna SES** and restart Home Assistant.

</details>

<details>
<summary>Install without HACS</summary>

1. Copy `custom_components/fayna_ses` from this repository into your Home Assistant `config/custom_components` directory.
2. Restart Home Assistant.

</details>

## Usage

Click the button and paste your public station link: `https://fayna-ses.funs.net.ua/s/…`.

[![Add Fayna SES][install-image]][install-url]

<details>
<summary>Add the integration manually</summary>

1. Open **Settings → Devices & services → Add integration**.
2. Search for **Fayna SES** and paste the station link.

</details>

Each station gets a separate device. Repeat setup to add another station.

### Sensors

| Sensors                          | Diagnostics                              |
| -------------------------------- | ---------------------------------------- |
| ![Sensors](./assets/sensors.png) | ![Diagnostics](./assets/diagnostics.png) |

| Data                                   | Values                                 |
| -------------------------------------- | -------------------------------------- |
| Battery level and state                | %; charging, discharging, or idle      |
| Grid power                             | W; positive import, negative export    |
| Battery power                          | W; positive discharge, negative charge |
| Solar power and building consumption   | W                                      |
| Solar, grid, and building energy today | kWh                                    |
| Power source                           | Solar, grid, battery, or idle          |

**Diagnostics** contains station connectivity, detailed connection status, and the last update time. Equipment power ratings, battery capacity, and station description are attributes of connection status.

### Data updates

- Polls every minute. Measurements older than 30 minutes become unavailable; missing readings remain unknown.
- Station connectivity does not indicate mains availability. Power source is estimated from power readings, not an outage detector.
- Daily totals reset at midnight in Kyiv. Grid energy import/export accounting is undocumented.
- Monitoring only. Equipment control and historical backfill are not supported.

### Removal

Open **Settings → Devices & services → Fayna SES** and delete the station entry through its menu. After removing all stations, uninstall the integration in HACS or delete `config/custom_components/fayna_ses`.

## Development

See [contributing.md](./contributing.md) for setup and checks.

## Other integrations

- 💥 [Aerial Danger](https://github.com/denysdovhan/ha-aerial-danger) — aerial-threat notifications.
- ☁️ [Check Weather](https://github.com/denysdovhan/ha-check-weather) — forecast condition checks.
- 💨 [LUN Misto Air](https://github.com/denysdovhan/ha-lun-misto-air) — air quality.
- 🌦️ [Ukrainian Hydrometeorological Center](https://github.com/denysdovhan/ha-ukr-hmc) — weather, radiation, and hydrology.
- ⚡️ [Yasno](https://github.com/denysdovhan/ha-yasno-outages) — electricity outage schedules.

## License

MIT © [Denys Dovhan][denysdovhan]

<!-- Badges -->

[gh-release-url]: https://github.com/denysdovhan/ha-fayna-ses/releases/latest
[gh-release-image]: https://img.shields.io/github/v/release/denysdovhan/ha-fayna-ses?style=flat-square
[gh-downloads-url]: https://github.com/denysdovhan/ha-fayna-ses/releases
[gh-downloads-image]: https://img.shields.io/github/downloads/denysdovhan/ha-fayna-ses/total?style=flat-square
[hacs-url]: https://github.com/hacs/integration
[hacs-image]: https://img.shields.io/badge/hacs-custom-orange.svg?style=flat-square
[gh-sponsors-url]: https://github.com/sponsors/denysdovhan
[gh-sponsors-image]: https://img.shields.io/github/sponsors/denysdovhan?style=flat-square
[buymeacoffee-url]: https://buymeacoffee.com/denysdovhan
[buymeacoffee-image]: https://img.shields.io/badge/support-buymeacoffee-222222.svg?style=flat-square
[twitter-url]: https://x.com/denysdovhan
[twitter-image]: https://img.shields.io/badge/follow-%40denysdovhan-000000.svg?style=flat-square

<!-- References -->

[home-assistant]: https://www.home-assistant.io/
[denysdovhan]: https://github.com/denysdovhan
[hacs-install-url]: https://my.home-assistant.io/redirect/hacs_repository/?owner=denysdovhan&repository=ha-fayna-ses&category=integration
[hacs-install-image]: https://my.home-assistant.io/badges/hacs_repository.svg
[install-image]: https://my.home-assistant.io/badges/config_flow_start.svg
[install-url]: https://my.home-assistant.io/redirect/config_flow_start/?domain=fayna_ses
[fayna-ses]: https://fayna-ses.funs.net.ua/
