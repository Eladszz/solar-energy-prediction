# Implementation Status

## Completed Features

- FastAPI backend with health, simulation, yearly forecast, comparison, and accuracy endpoints
- Streamlit frontend with location input, map-based roof area selection, yearly overview, daily simulation, scenario comparison, and accuracy backtest tabs
- Physics-based PV conversion pipeline
- Real ML baseline for yearly forecasting using trained weather regression
- Financial value estimation from predicted energy
- Monthly and yearly summary outputs
- Scenario comparison with yearly energy and value deltas
- Accuracy backtest with monthly MAPE and yearly MAPE
- Explicit fallback metadata when ML cannot be used
- Backend automated tests for core services and forecast logic

## Partially Completed Features

- Scenario editing in the UI
  - Scenarios can be added and cleared, but not edited inline after creation
- Explainability
  - Model metadata is exposed, but there is no dedicated feature attribution view
- Deployment hardening
  - Docker support exists, but production-grade deployment concerns are not fully addressed

## Deferred Features

- Real PV production ingestion from monitored systems
- Database storage for forecast history
- Authentication and user-specific projects
- Battery/storage and self-consumption optimization
- Dynamic tariff catalogs and time-of-use pricing
- Uncertainty bands and probabilistic forecasting
- Advanced ML models such as gradient boosting, transformers, or LSTM variants

## Known Limitations

- The ML model predicts weather first and energy second; it is not yet trained on real measured PV output
- Monetary value is based on a single user-supplied tariff assumption
- Geocoding and weather retrieval depend on external APIs
- The yearly physical baseline uses archived weather as a representative profile when future weather is unavailable
- UI state is session-based and not persisted

## Alpha Readiness Summary

The project is ready for Alpha submission because it now supports a credible end-to-end engineering demo:
- location selection
- system parameter entry
- yearly forecast in physical or ML mode
- financial interpretation of results
- scenario comparison
- backtest accuracy analysis

The current implementation is intentionally practical rather than exhaustive. The architecture leaves clear extension points for future work without blocking the Alpha version.
