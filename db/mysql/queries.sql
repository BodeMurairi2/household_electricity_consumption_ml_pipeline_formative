USE household_power;

-- Q1: Daily energy consumption (kWh) for the first week of January 2007
SELECT DATE(measured_at) AS day,
       ROUND(SUM(global_active_power) / 60, 2) AS energy_kwh,
       ROUND(AVG(voltage), 2) AS avg_voltage
FROM power_readings
WHERE measured_at >= '2007-01-01' AND measured_at < '2007-01-08'
GROUP BY day
ORDER BY day;

-- Q2: Average load by hour of day (from hourly_power)
SELECT HOUR(hour_start) AS hour_of_day,
       ROUND(AVG(global_active_power), 3) AS avg_active_power_kw
FROM hourly_power
GROUP BY hour_of_day
ORDER BY hour_of_day;

-- Q3: Sub-meter energy share per year
SELECT YEAR(p.measured_at) AS year,
       s.name AS sub_meter,
       ROUND(SUM(r.energy_wh) / 1000, 1) AS energy_kwh,
       ROUND(100 * SUM(r.energy_wh) / SUM(SUM(r.energy_wh)) OVER (PARTITION BY YEAR(p.measured_at)), 1) AS pct_of_year
FROM sub_meter_readings r
JOIN power_readings p ON p.reading_id = r.reading_id
JOIN sub_meters s ON s.sub_meter_id = r.sub_meter_id
GROUP BY year, s.sub_meter_id, s.name
ORDER BY year, s.sub_meter_id;

-- Q4: Days with the most missing readings
SELECT DATE(measured_at) AS day,
       SUM(global_active_power IS NULL) AS missing_minutes
FROM power_readings
GROUP BY day
HAVING missing_minutes > 0
ORDER BY missing_minutes DESC, day
LIMIT 10;
