select
  rides.ride_id,
  rides.distance,
  rides.cab_type,
  rides.time_stamp as ride_time_stamp,
  rides.ride_timestamp,
  rides.ride_hour,
  rides.destination,
  rides.source,
  rides.price,
  rides.surge_multiplier,
  rides.ride_name,
  weather.weather_id,
  weather.temp,
  weather.clouds,
  weather.pressure,
  weather.rain,
  weather.humidity,
  weather.wind,
  weather.location,
  weather.time_stamp as weather_time_stamp,
  weather.weather_timestamp,
  weather.weather_hour
from {{ ref('stg_rides') }} as rides
left join {{ ref('stg_weather') }} as weather
  on rides.source = weather.location
 and rides.ride_hour = weather.weather_hour
