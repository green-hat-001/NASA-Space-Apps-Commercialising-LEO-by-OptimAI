# NASA-Space-Apps-Commercialising-LEO-by-OptimAI
>>>>Overview

This project simulates an AI-optimized launch vehicle based on Falcon 9 telemetry data.
The AI rocket is designed to be:

4–5% more fuel efficient than Falcon 9.

Reaches a 600 km orbit in 95% of the time compared to Falcon 9.

The dataset AI_model_rocket_with_more_intervals.csv contains simulated telemetry for 578 seconds of flight with ~30 columns of flight parameters, derived and estimated from Falcon 9 data.

>>>>Files

Telemetry_data_falcon_9.csv
Real Falcon 9 telemetry reference dataset.

AI model rocket.csv
Initial AI rocket dataset (shorter, fewer columns).

AI_model_rocket_fledged.csv
Expanded AI rocket dataset with full telemetry timeline and derived physics columns.

AI_model_rocket_fledged.zip
Zipped version for easy download.

Columns in AI_model_rocket_fledged.csv

Some of the key columns include:

>>>>Core Telemetry

time — mission elapsed time (s)

velocity, velocity_x, velocity_y — rocket velocity (m/s)

altitude — altitude (m)

acceleration — acceleration (m/s²)

downrange_distance — horizontal distance traveled (m)

angle — flight path angle (deg)

>>>>Propulsion

thrust — thrust output (N)

propellant — fuel remaining (kg)

mass_flow_rate — rate of propellant consumption (kg/s)

propellant_est, mass_flow_rate_est — adjusted values (AI rocket, 4.5% more efficient)

>>>>Flight Environment

rho_est — estimated atmospheric density (kg/m³)

q / dynamic_pressure_est — dynamic pressure (Pa)

mach_est — Mach number

>>>>Energy & Orbit

kinetic_energy_est — kinetic energy (J)

potential_energy_est — potential energy (J)

delta_v, cum_delta_v — incremental and cumulative Δv (m/s)

apoapsis_est, periapsis_est — estimated orbital elements (km, rough)

>>>>Assumptions

Units: Treated as SI (m, s, N, kg), though original Falcon telemetry may differ.

Efficiency: AI rocket consumes 4.5% less fuel for equivalent thrust.

Orbit Target: AI rocket reaches 600 km ~502.6 s (95% of Falcon’s 529 s).

Physics Models: Approximations used for density, drag, Mach, orbital estimates. Results are indicative, not precise.
