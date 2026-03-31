select
  cast(ride_hour as date) as ride_date,
  ride_hour,
  source,
  destination,
  cab_type,
  count(*) as total_rides,
  avg(price) as avg_price,
  min(price) as min_price,
  max(price) as max_price,
  avg(distance) as avg_distance,
  avg(surge_multiplier) as avg_surge_multiplier,
  avg(temp) as avg_temp,
  avg(clouds) as avg_clouds,
  avg(humidity) as avg_humidity
from {{ ref('fct_rides_enriched') }}
group by 1, 2, 3, 4, 5
