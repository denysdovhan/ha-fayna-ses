"""Constants for Fayna SES."""

from datetime import timedelta

DOMAIN = "fayna_ses"
CONF_DASHBOARD_URL = "dashboard_url"
CONF_STATION_ID = "station_id"
UPDATE_INTERVAL = timedelta(seconds=60)
STALE_AFTER = timedelta(minutes=30)

# Dashboard suggestions and community submissions.
REPORT_DASHBOARD_URL = (
    "https://github.com/denysdovhan/ha-fayna-ses/issues/new?title=Add+dashboard"
)
CUSTOM_DASHBOARD = "custom"
PRECONFIGURED_DASHBOARDS = (
    "cc5a340c80f5ce04158291f4aac365a6",
    "366ae83e5947dbd6b6d30372f916a71f",
    "ac15fb3d463174465df3bedcb30be9cc",
    "91d435460f4c38741aa0ee07808a5960",
    "e64791f0a8f89a5400db11c0f8c82c57",
)
