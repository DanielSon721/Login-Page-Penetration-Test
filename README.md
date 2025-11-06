# Login-Page-Penetration-Test

Overview

I built a custom login page from scratch for a Flask web app (Flask, PyMySQL, MySQL). Because it was a minimal, homegrown implementation, I treated it as an opportunity to practice secure development: I performed self-directed penetration testing, found multiple critical weaknesses (SQL injection, unencrypted plaintext credentials, and susceptibility to automated brute-force), then remediated each issue and validated the fixes.

Initial implementation

The original app used a simple signup/login flow with HTML forms and server code that:

- built SQL queries by concatenating user input,

- stored passwords directly as plaintext in the users table,

- returned distinct error messages and had no rate limits or lockouts,

- served over HTTP in development and ran with debug=True.

This combination made the app trivially exploitable during testing.



Vulnerabilities found (what I discovered during pentest)

1. SQL injection

Occurred because SQL queries were assembled with string concatenation using raw username/password inputs.

Example exploit: username = "admin' OR 1=1 --" allowed bypassing authentication.

2. Plaintext credential storage

Passwords were persisted in the DB as clear text. If the DB was leaked, attacker immediately had usable credentials.

3. Automated brute-force

No rate limiting or lockouts meant tools like Hydra could try large password lists and enumerate credentials quickly.

I validated exploitation with local tests and automated tools (Hydra) against the pre-patch site to reproduce real-world attack scenarios.
