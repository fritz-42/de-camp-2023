{{ config(materialized='view') }}

select 

    cast(int64_field_0 as integer) as int64_field_0,
    cast(dispatching_base_num as string) as dispatching_base_num,

    cast(pickup_datetime as timestamp) as pickup_datetime,
    cast(dropOff_datetime as timestamp) as dropoff_datetime,

    cast(PUlocationID as integer) as  pickup_locationid,
    cast(DOlocationID as integer) as  dropoff_locationid,
    
    cast(SR_Flag as string) as sr_flag,
    cast(Affiliated_base_number as string) as affiliated_base_number 
    
from {{ source('staging','fhv_tripdata') }}

 -- dbt build --m <model.sql> --var 'is_test_run: false'
{% if var('is_test_run', default=true) %}

  limit 100

{% endif %}
