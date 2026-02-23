# Changelog

All notable changes to this project will be documented in this file.

## [1.1.0] - 2026-02-23

### Added
- Integrated **MLflow** for robust AI model training pipelines, metric tracking, and artifact logging.
- Integrated **Prometheus and Grafana** for advanced system and application monitoring.
- Automated testing suite integrated into **GitHub Actions** for continuous integration and delivery (CI/CD).
- Visual feedback on the Text Humanizer page when copied successfully.
- Valid Until (subscription expiration date) display on the navbar profile and pricing CTA for Premium users.

### Fixed
- Multiple UI responsiveness issues on mobile for Hero texts and grid alignments.
- 3D Carousel overflow and clipping clipping issues on 480px viewports.
- Standardized the App layout configuration (AI Video/Image/Text) to follow a consistent stacked design.
- Corrected Pricing UI text fallback logic for Free plans when users are logged in as Pro/Premium.
## [1.0.0] - 2026-02-18

### Added
- Initial release of DETECTIFY.
- Core application structure with Flask.
- Authentication blueprint (`/auth`).
- Analysis blueprint (`/`).
- Payment blueprint (`/api/payment`).
- Database migration support.
- JWT authentication support.
- CORS support.
- Email support.
- S3 client initialization.
- Docker support (`Dockerfile`, `.dockerignore`).
