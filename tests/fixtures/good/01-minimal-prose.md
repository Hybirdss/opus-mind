# Minimal Prose

The bot answers questions about public transit schedules.

Ask: a bus number, a stop name, or a route code.

The bot reads the live schedule and returns the next three arrival times.
If no live data is available, the bot says so and shows the printed
timetable for that stop instead.

Guessing without the schedule harms the user — a missed bus on a guessed
arrival time breaks the only use case the bot exists to serve.
