db = db.getSiblingDB("household_power");

print("Q1: Summary of a single day (2007-01-01), readings trimmed to the first 3 minutes");
printjson(db.daily_readings.findOne(
  { household_id: 1, date: ISODate("2007-01-01") },
  { _id: 0, date: 1, summary: 1, readings: { $slice: 3 } }
));

print("\nQ2: Top 5 highest-consumption days");
printjson(db.daily_readings.find(
  {},
  { _id: 0, date: 1, "summary.total_kwh": 1, "summary.peak_power_kw": 1, "summary.peak_time": 1 }
).sort({ "summary.total_kwh": -1 }).limit(5).toArray());

print("\nQ3: Monthly average daily consumption in 2008");
printjson(db.daily_readings.aggregate([
  { $match: { date: { $gte: ISODate("2008-01-01"), $lt: ISODate("2009-01-01") } } },
  { $group: {
      _id: { $month: "$date" },
      avg_daily_kwh: { $avg: "$summary.total_kwh" },
      avg_water_heater_ac_kwh: { $avg: "$summary.sub_metering_kwh.water_heater_ac" }
  } },
  { $project: { _id: 0, month: "$_id", avg_daily_kwh: { $round: ["$avg_daily_kwh", 2] },
                avg_water_heater_ac_kwh: { $round: ["$avg_water_heater_ac_kwh", 2] } } },
  { $sort: { month: 1 } }
]).toArray());

print("\nQ4: Minutes above 9 kW, counted per year");
printjson(db.daily_readings.aggregate([
  { $unwind: "$readings" },
  { $match: { "readings.global_active_power": { $gt: 9 } } },
  { $group: { _id: { $year: "$readings.time" }, minutes: { $sum: 1 },
              max_kw: { $max: "$readings.global_active_power" } } },
  { $project: { _id: 0, year: "$_id", minutes: 1, max_kw: 1 } },
  { $sort: { year: 1 } }
]).toArray());
