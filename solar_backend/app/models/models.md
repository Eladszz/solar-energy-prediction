# API models

`BasePVRequest` validates location, forecast year, tilt, panel area/efficiency, cleanliness, shading, AC capacity, temperature coefficient, NOCT, tariff, currency, and CAPEX. Unknown fields and non-finite values are rejected.

`ScenarioComparisonRequest` contains shared location/year/tariff context and 2-20 independently configured scenarios. Scenario names must be unique after trimming and case folding.

Responses expose the production model, weather source/reference year, energy values, financial assumptions, and archive-year reuse reason. Monthly response arrays contain exactly twelve values.
