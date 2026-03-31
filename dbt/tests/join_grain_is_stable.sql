with ride_counts as (
    select count(*) as rides_count
    from {{ ref('stg_rides') }}
),
fact_counts as (
    select count(*) as fact_count
    from {{ ref('fct_rides_enriched') }}
)
select *
from ride_counts
cross join fact_counts
where rides_count <> fact_count
