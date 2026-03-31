select
  ride_id,
  ride_hour,
  extract(hour from ride_hour) as ride_hour_of_day,
  extract(dow from ride_hour) as ride_day_of_week,
  source,
  destination,
  cab_type,
  ride_name,
  distance,
  surge_multiplier,
  temp,
  clouds,
  pressure,
  rain,
  humidity,
  wind,
  price
from {{ ref('fct_rides_enriched') }}
where price is not null
  and distance is not null
  and cab_type is not null
