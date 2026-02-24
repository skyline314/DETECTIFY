# Changelog

All notable changes to this project will be documented in this file.

## [1.1.1] - 2026-02-24

### Added
- **Daily quota badge** on all 5 feature pages (Text, Image, Video, Audio, Humanize) — shows remaining quota for Free users and unlimited status for Premium/Pro users.
- New API endpoint `GET /auth/quota` returning `is_premium`, `usage`, `limit`, `remaining` fields.
- `quota-badge.js` reusable script handles badge rendering and disables Analyze button when quota is exhausted.

### Fixed
- `LIMIT_DAILY` standardized across the app — now always read from `.env` via `config.py` (was hardcoded to `3` in `decorators.py` and `payment/routes.py`, now defaults to `5` from env var).
- Audio progress bar no longer resets to 0% during the analysis phase (was caused by `startFakeProgress` reinitializing `width = "0%"`).
- Previous detection result is now cleared immediately when a new analysis is triggered on all feature pages — no more stale results showing during re-analysis.
- Page title style on **Text Detection** and **Text Humanizer** unified to match Image/Video/Audio pages (`font-weight: 900`, `letter-spacing: -0.8px`, `font-size: clamp(28px, 5vw, 52px)`).
- "Get Started" button in mobile navbar now always visible (compact size) to the left of the hamburger icon.

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
