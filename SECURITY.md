# Security Policy

## Supported versions

Only the latest released version of `reflex-react-globe-gl` receives security fixes.

| Version | Supported |
| ------- | --------- |
| 0.1.x   | ✅        |

## Reporting a vulnerability

Please **do not open a public issue** for security problems.

Report privately through
[GitHub Security Advisories](https://github.com/ecrespo/reflex-react-globe-gl/security/advisories/new),
or by email to <ecrespo@gmail.com>.

Include, as far as you can: affected version, a description of the impact, and the smallest
reproduction you have. Expect an acknowledgement within 72 hours and a fix or a mitigation
plan within 30 days for confirmed issues.

## Scope and threat model

This package renders **caller-supplied data** on a WebGL globe. Two areas deserve attention
when you use it:

- **`html_markup` and `tooltip` templates render HTML.** `tooltip()` HTML-escapes the values
  it interpolates, but the template itself is emitted verbatim, and `html_markup` is not
  escaped at all. Never build either from untrusted input.
- **`js()` and `run_js()` emit JavaScript verbatim** into the compiled page, by design —
  that is how accessor functions reach the browser. Treat any string you pass to them as
  code, and never interpolate untrusted input into it.

Everything a handler receives from the browser is sanitized by `globe_wrapper.js` into plain
JSON (functions, ThreeJS objects, DOM events, cycles and keys listed in `event_data_exclude`
are stripped, and arrays are capped) before it reaches your Python state.

## Automated checks

Every push and pull request runs, in `.github/workflows/security.yml`:

- **bandit** — static analysis of the package source
- **pip-audit** — known vulnerabilities in the resolved dependency tree
- **gitleaks** — secret scanning across the full git history
- **CodeQL** — `security-extended` queries for Python and JavaScript
- **dependency review** — blocks pull requests introducing high-severity advisories

The suite also runs weekly so newly disclosed advisories surface without a push.

## Releases

Releases are published to PyPI from a tagged commit using
[Trusted Publishing](https://docs.pypi.org/trusted-publishers/) (OIDC) with
[attestations](https://docs.pypi.org/attestations/). No long-lived PyPI API token exists
for this project.
