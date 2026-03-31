select
  ride_id,
  distance,
  cab_type,
  time_stamp,
  ride_timestamp,
  ride_hour,
  destination,
  source,
  price,
  surge_multiplier,
  name as ride_name
from {{ source('raw', 'rides') }}
