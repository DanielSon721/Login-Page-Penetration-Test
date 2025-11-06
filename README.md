# Overview

I built a custom login page from scratch for a Flask web app (Flask, PyMySQL, MySQL). Because it was a minimal, homegrown implementation, I treated it as an opportunity to practice secure development: I performed self-directed penetration testing, found multiple critical weaknesses (SQL injection, unencrypted plaintext credentials, and susceptibility to automated brute-force), then remediated each issue and validated the fixes.

# Initial implementation

The original app used a simple signup/login flow with HTML forms and server code that:

- built SQL queries by concatenating user input,

- stored passwords directly as plaintext in the users table,

- returned distinct error messages and had no rate limits or lockouts,

- served over HTTP in development and ran with debug=True.

This combination made the app trivially exploitable during testing.



# Vulnerabilities found

## 1. SQL injection

Occurred because SQL queries were assembled with string concatenation using raw username/password inputs.

Example exploit: username = "admin' OR 1=1 --" allowed bypassing authentication.

<img width="1512" height="950" alt="IMG_4317" src="https://github.com/user-attachments/assets/59027c7f-9ff0-4c59-bc07-7676d47bb87c" />

<img width="1512" height="948" alt="IMG_9866" src="https://github.com/user-attachments/assets/3ba13c9a-884b-4552-bbcb-36a1922d801e" />


To remediate this vulnerability, I replaced all string-built SQL with parameterized queries (PyMySQL %s placeholders).

Before:

<img width="747" height="103" alt="IMG_9712" src="https://github.com/user-attachments/assets/d7481c9c-234f-4796-a4bb-c9f29152cfc4" />

After:

<img width="703" height="77" alt="IMG_1059" src="https://github.com/user-attachments/assets/acc14d81-da70-4c9d-bbdd-8b0dda6571b9" />

2. Plaintext credential storage

Passwords were persisted in the DB as clear text. If the DB was leaked, attacker immediately had usable credentials.

<img width="267" height="139" alt="IMG_6150" src="https://github.com/user-attachments/assets/07e24f6b-ac1a-4742-a8a1-7ca8752b6be7" />

I deployed bcrypt salted password hashing to convert plaintext passwords into ciphertext, preventing human readability.

<img width="591" height="140" alt="IMG_7736" src="https://github.com/user-attachments/assets/97a82857-d55d-4d8f-aded-6d3a68688ec3" />

3. Automated brute-force

No rate limiting or lockouts meant tools like Hydra could try large password lists and enumerate credentials quickly.

I validated exploitation with local tests and automated tools (Hydra) against the pre-patch site to reproduce real-world attack scenarios.

<img width="1710" height="1218" alt="IMG_1253" src="https://github.com/user-attachments/assets/c87034e9-cda6-4125-a2f6-60088b7cc014" />

To prevent brute force attacks, I introduced an account lockout mechanism that automatically blocks accounts after 5 failed login attempts with a 15-minute
cooldown period.

<img width="502" height="116" alt="IMG_3153" src="https://github.com/user-attachments/assets/65392e06-2845-4b45-9038-918fe6d681db" />
