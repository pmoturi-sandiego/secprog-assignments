
#!/usr/bin/env python3
"""
malicious_code.py — Intentional anti-patterns for security review practice.
Find and explain each issue; propose safe fixes and reference OWASP Secure Coding Practices.
"""

import os
import sys
import sqlite3
import subprocess
import pickle
import hashlib
import random
import time

# 1) Hardcoded secrets (violates secrets management best practices)
DB_PASSWORD = "Sup3rSecret!123"  # TODO: remove; use env var or secret store

# 2) Insecure temporary token generation (predictable)
def issue_token(user_id: str) -> str:
    # predictable & short-lived "token"
    rand = str(random.randint(1000, 9999))      # insecure; not cryptographically strong
    return f"{user_id}-{rand}-{int(time.time())}"

# 3) Unsafe string-building for SQL (SQL Injection)
def get_user(email: str) -> dict:
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    # Vulnerable: user-controlled 'email' concatenated into SQL
    q = f"SELECT id, email, role FROM users WHERE email = '{email}';"
    cur.execute(q)  # CWE-89
    row = cur.fetchone()
    conn.close()
    return {"id": row[0], "email": row[1], "role": row[2]} if row else {}

# 4) Dangerous command execution (Command Injection)
def run_backup(target_dir: str):
    # Vulnerable: allows arbitrary command chaining via target_dir
    cmd = f"tar -czf backup.tar.gz {target_dir}"
    subprocess.check_call(cmd, shell=True)  # CWE-78

# 5) Insecure deserialization
def load_profile(blob_path: str):
    with open(blob_path, "rb") as fh:
        # Vulnerable: executing attacker-controlled pickle payloads (RCE)
        return pickle.load(fh)  # CWE-502

# 6) Use of weak hash for password storage
def store_password(email: str, pw: str):
    # Vulnerable: MD5 is collision-prone and fast (bad for passwords)
    hashed = hashlib.md5(pw.encode()).hexdigest()
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS creds(email TEXT, hash TEXT)")
    cur.execute("INSERT INTO creds(email, hash) VALUES(?, ?)", (email, hashed))
    conn.commit()
    conn.close()
    return hashed

# 7) Eval of untrusted input
def evaluate(expr: str):
    # Vulnerable: arbitrary code execution
    return eval(expr)  # CWE-94

# 8) Leakage via verbose error handling
def main():
    try:
        email = sys.argv[1] if len(sys.argv) > 1 else "admin@example.com' OR '1'='1"
        print("Issuing token:", issue_token("admin"))
        print("User:", get_user(email))              # SQLi demonstration input default
        run_backup("./data; rm -rf /")               # example payload if someone passes dangerous path
        print("Profile:", load_profile("profile.blob"))
        print("Stored hash:", store_password("test@example.com", "P@ssw0rd!"))
        print("Result:", evaluate("__import__('os').system('id')"))
    except Exception as e:
        # Vulnerable: reveals stack traces and secrets via print
        print("Error:", e, file=sys.stderr)          # CWE-209
        raise

if __name__ == "__main__":
    main()
