select
  weather_id,
  temp,
  clouds,
  pressure,
  rain,
  humidity,
  wind,
  location,
  time_stamp,
  weather_timestamp,
  weather_hour
from {{ source('raw', 'weather') }}
