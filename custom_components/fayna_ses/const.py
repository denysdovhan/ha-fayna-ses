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
    "dee052e69e8fa101de2f002f53a964e2",
    "8fd92183d607f5990c7e1dac509ec68a",
    "4f655c36051a572e646a09bd6dc67d66",
    "7cfb64881a9fa84997bf7e1bdb8e5071",
)
