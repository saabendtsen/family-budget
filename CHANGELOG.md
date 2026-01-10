# Changelog

## [1.2.0](https://github.com/saabendtsen/family-budget/compare/family-budget-v1.1.1...family-budget-v1.2.0) (2026-01-10)


### Features

* add app description and feature highlights to login page ([e3fa4c1](https://github.com/saabendtsen/family-budget/commit/e3fa4c131d755d85603a64ba2fd01429cf442015))
* add app description and feature highlights to login page ([358acb8](https://github.com/saabendtsen/family-budget/commit/358acb8d818e867fdcff8f0855bd65c9e6b98f91))


### Bug Fixes

* add user_id filter to category usage count to prevent data leakage ([a96b0f7](https://github.com/saabendtsen/family-budget/commit/a96b0f7dac83ee7241144f348d9f55577aaf6129))
* add user_id filter to category usage count to prevent data leakage ([39ab69e](https://github.com/saabendtsen/family-budget/commit/39ab69e159eb19934e78f9f5d2ee5cfbe1f37782))

## [1.1.1](https://github.com/saabendtsen/family-budget/compare/family-budget-v1.1.0...family-budget-v1.1.1) (2026-01-09)


### Bug Fixes

* add migration for expenses frequency CHECK constraint ([f7c07e9](https://github.com/saabendtsen/family-budget/commit/f7c07e90924a9ef6767ce0caa826037e54637bfa))

## [1.1.0](https://github.com/saabendtsen/family-budget/compare/family-budget-v1.0.0...family-budget-v1.1.0) (2026-01-08)


### Features

* add demo data examples for new frequencies ([4489ee0](https://github.com/saabendtsen/family-budget/commit/4489ee0fde78f3d25e59bdea2dbac1b403c17e30))
* add Docker support for production deployment ([7d39bc2](https://github.com/saabendtsen/family-budget/commit/7d39bc2c312baf4c286c242da607a8a0ea57c119))
* add frequency selection to income UI ([a739378](https://github.com/saabendtsen/family-budget/commit/a73937828fe65f9041fce8b472256810327de9e4))
* add frequency support to income ([6fb0cfe](https://github.com/saabendtsen/family-budget/commit/6fb0cfe8fcae0bc4825674dedaab8ad8bcf1d3b7))
* add GitHub Actions auto-deploy ([681ac24](https://github.com/saabendtsen/family-budget/commit/681ac24fca49421e06ba3e1c3f1a81a19fcbae0c))
* add polling-based auto-deploy ([a61267f](https://github.com/saabendtsen/family-budget/commit/a61267fb145b07ee0c1e0e716a49cf38c42a9f58))
* add public stats API endpoint ([b875dd3](https://github.com/saabendtsen/family-budget/commit/b875dd30c4179e673f17ade3535087712d20b7dd))
* add quarterly and semi-annual frequency options to expense UI ([4ee7337](https://github.com/saabendtsen/family-budget/commit/4ee7337e893d55dc93d73511d1c1f82eb2ad4cd9))
* Add quarterly and semi-annual frequency support ([899cfcd](https://github.com/saabendtsen/family-budget/commit/899cfcdf1dca11dbee2a5081d0bdd08fa84c2238))
* add quarterly and semi-annual frequency support to database ([7203938](https://github.com/saabendtsen/family-budget/commit/7203938214b7908422743a04ea0d04c06e29ddf8))
* enhance demo mode with localStorage persistence ([4de7826](https://github.com/saabendtsen/family-budget/commit/4de7826c73700932584282df7ddb4474857e8482))
* Enhanced Demo Mode with localStorage persistence ([28e612e](https://github.com/saabendtsen/family-budget/commit/28e612e564433a405341c02e3e46c80a980b4655))
* Implement user-specific data isolation ([28cc98b](https://github.com/saabendtsen/family-budget/commit/28cc98b48e08157aa066b9a9df1ff77e371e2ecd))
* **income:** add dynamic income sources ([1b016ce](https://github.com/saabendtsen/family-budget/commit/1b016cef9837a556595e74ca084623207dcf9e07))
* Initialize FastAPI application with Docker support, user authentication, session management, and security middleware. ([a021949](https://github.com/saabendtsen/family-budget/commit/a02194921ac6eb7a777aba5dabac577fc9bf1b7e))
* update API form handling for new frequencies ([6aa736d](https://github.com/saabendtsen/family-budget/commit/6aa736d9dc8e4dc850d35f4ea6200072a4c5b1db))
* update DemoStateManager for new frequencies ([36163b6](https://github.com/saabendtsen/family-budget/commit/36163b606014d5dfac115a6bad0c557ccb91118c))
* **users:** add last_login timestamp tracking ([2048fc2](https://github.com/saabendtsen/family-budget/commit/2048fc2f98afc011afb31decc4f16fa9e9da06df))
* **users:** add last_login timestamp tracking ([7a40017](https://github.com/saabendtsen/family-budget/commit/7a40017e4ab6cc2d184eafd652bc4f5dc1dee2f8))


### Bug Fixes

* add missing frequency column migration for existing databases ([21c2803](https://github.com/saabendtsen/family-budget/commit/21c280346ad09baeaf0fb1dc8de549f57faea708))
* allow any integer value for income amount input ([4a4e159](https://github.com/saabendtsen/family-budget/commit/4a4e15938711b741853cfe0b7ff890a6ce07ae0e))
* allow demo users to access login and register pages ([39f5e52](https://github.com/saabendtsen/family-budget/commit/39f5e52d2670bf2ad7241f0d6397ed7665c8b6c7))
* **family-budget:** apply code review suggestions ([151f13d](https://github.com/saabendtsen/family-budget/commit/151f13d2c8a17c7314555247937223175a450a35))
* **family-budget:** auto-fix code review issues ([4a3dd9f](https://github.com/saabendtsen/family-budget/commit/4a3dd9f3737e7a1235e5548b54e0b61ea3339913))
* **family-budget:** auto-fix code review issues ([5d5972d](https://github.com/saabendtsen/family-budget/commit/5d5972d13d02acbd2b0e4ee7b0a7e1012f490dc2))
* **family-budget:** bump python-multipart to 0.0.12 for CVE fix ([4bf4abe](https://github.com/saabendtsen/family-budget/commit/4bf4abe0f26fa0005d0dd95f5597b1e71c33a1a9))
* improve e2e test infrastructure reliability ([80b99d4](https://github.com/saabendtsen/family-budget/commit/80b99d4cd1d92a5ae5edb5636288a70397bb5a63))
* read database path from BUDGET_DB_PATH env var ([56312f6](https://github.com/saabendtsen/family-budget/commit/56312f696daad72f826a9cf574b8148cb7547136))
* restore RateLimitMiddleware class that was accidentally deleted ([ab99c99](https://github.com/saabendtsen/family-budget/commit/ab99c9927781aacbd497c79b040c6f3fca0a402f))
* show demo income data on income page ([adf3d26](https://github.com/saabendtsen/family-budget/commit/adf3d26a1deaf43366820a571a9e97f2d4d67e7f))
* update CSP to allow Tailwind and Lucide CDNs ([87f717e](https://github.com/saabendtsen/family-budget/commit/87f717ec9d6325cd91ffc3a4c396dcd44325075b))
* use correct income.monthly_amount property in dashboard ([961e69d](https://github.com/saabendtsen/family-budget/commit/961e69d98739fbd4f089522b43bb87aa4f883b90))
