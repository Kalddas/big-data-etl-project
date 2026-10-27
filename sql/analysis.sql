-- 1. Total number of loaded trips
SELECT COUNT(*) AS total_trips
FROM public.yellow_taxi_trips;

-- 2. Trips by pickup hour
SELECT pickup_hour, COUNT(*) AS number_of_trips
FROM public.yellow_taxi_trips
GROUP BY pickup_hour
ORDER BY number_of_trips DESC;

-- 3. Average fare and total recorded amount
SELECT
    ROUND(AVG(fare_amount)::numeric, 2) AS average_fare,
    ROUND(SUM(total_amount)::numeric, 2) AS total_recorded_amount,
    ROUND(AVG(total_amount)::numeric, 2) AS average_total_amount
FROM public.yellow_taxi_trips;

-- 4. Average distance and duration
SELECT
    ROUND(AVG(trip_distance)::numeric, 2) AS average_distance_miles,
    ROUND(AVG(trip_duration_minutes)::numeric, 2) AS average_duration_minutes
FROM public.yellow_taxi_trips
WHERE trip_duration_minutes >= 0;

-- 5. Trips by payment type
SELECT payment_type, COUNT(*) AS number_of_trips
FROM public.yellow_taxi_trips
GROUP BY payment_type
ORDER BY number_of_trips DESC;
