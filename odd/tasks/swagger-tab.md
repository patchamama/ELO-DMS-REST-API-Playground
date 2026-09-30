# swagger-tab
Objective: new "Swagger" tab: Swagger UI over ELO's openapi.json with working "Try it out".
Scope: frontend (index.html, app.js, style.css, i18n x3, vendor/swagger-ui), backend main.py + openapi_ref.py (raw spec endpoint), scripts/build_static.py, tests, README.
Route: delegated direct (one writer). TDD: not configured; runner: python -m pytest backend-python, node --test.
Tasks:
- [x] T1 backend GET /api/spec/raw (+ static api/spec/raw.json, api/swagger-mock.json) + test
- [x] T2 vendor swagger-ui-dist (bundle js/css) under frontend/vendor/swagger-ui
- [x] T3 tab UI: routing, spec load, requestInterceptor -> proxy/mock/direct, i18n
- [x] T4 README/TODO, run tests, build_static
Commit: work-unit conventional commits, no AI attribution.
