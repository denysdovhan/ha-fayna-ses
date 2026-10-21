# Contributing

If you plan to contribute back to this repo, please fork & open a PR.

## How to add translation

Edit `custom_components/fayna_ses/translations/en.json` and `uk.json` directly.
Keep translation keys aligned and `strings.json` identical to English.

## How to run locally

1. Clone this repo to wherever you want:
   ```sh
   git clone https://github.com/denysdovhan/ha-fayna-ses.git
   ```
2. Go into the repo folder:
   ```sh
   cd ha-fayna-ses
   ```
3. Open the project with [VSCode Dev Container](https://code.visualstudio.com/docs/devcontainers/containers)
4. Start a HA via `Run Home Assistant on port 8123` task or run a following command:
   ```sh
   scripts/develop
   ```

Now you have a working Home Assistant instance with this integration installed. You can test your changes by editing the files in `custom_components/fayna_ses` folder and restarting your Home Assistant instance.
