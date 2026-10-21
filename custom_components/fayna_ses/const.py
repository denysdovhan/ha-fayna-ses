"""Constants for Fayna SES."""

from datetime import timedelta

DOMAIN = "fayna_ses"
CONF_DASHBOARD_URL = "dashboard_url"
CONF_STATION_ID = "station_id"
UPDATE_INTERVAL = timedelta(seconds=60)
STALE_AFTER = timedelta(minutes=30)
