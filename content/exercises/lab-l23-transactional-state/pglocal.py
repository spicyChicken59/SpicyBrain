"""Throwaway local PostgreSQL 16 server and psql sessions for lab L23.

Standard library only. The server lives in a fresh temporary directory, listens on
127.0.0.1 only (no Unix socket), uses SCRAM password authentication, and is stopped
and deleted by LocalPostgres.stop(). SQL runs through the psql client that ships
with the server, as separate processes, so two sessions really are two database
connections with two server backends.

This is local PostgreSQL 16. It is not Lakebase and makes no claim about Lakebase
behaviour; ADAPTATION.md lists what changes on the managed service.
"""
from __future__ import annotations

import os
import pwd
import queue
import re
import secrets
import shutil
import socket
import subprocess
import tempfile
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path

ADMIN_ROLE = "lab_admin"
SAFE_VALUE = re.compile(r"^[A-Za-z0-9 _:.+\-]*$")
MESSAGE = re.compile(r"^(?:psql:[^:]*:\d+: )?(ERROR|WARNING|NOTICE|DETAIL|HINT|LOCATION|CONTEXT):\s+(.*)$")


class LabError(RuntimeError):
    """The local server could not be prepared; the run must stop, never skip."""


def find_bin_dir(explicit: str | None = None) -> tuple[Path, str]:
    """Return the PostgreSQL 16 bin directory and the server's version line."""
    candidates: list[str] = [c for c in (explicit, os.environ.get("PG_BIN")) if c]
    try:
        found = subprocess.run(["pg_config", "--bindir"], capture_output=True, text=True, check=True)
        candidates.append(found.stdout.strip())
    except (OSError, subprocess.CalledProcessError):
        pass
    candidates.append("/usr/lib/postgresql/16/bin")  # Debian and Ubuntu packages
    for candidate in candidates:
        path = Path(candidate)
        if all((path / tool).exists() for tool in ("postgres", "initdb", "pg_ctl", "psql")):
            version = subprocess.run([str(path / "postgres"), "--version"],
                                     capture_output=True, text=True).stdout.strip()
            if re.search(r"\(PostgreSQL\) 16\.", version):
                return path, version
    raise LabError("PostgreSQL 16 server binaries (postgres, initdb, pg_ctl, psql) were not found; "
                   "pass --pg-bin <dir> or set PG_BIN. SQLite or another engine is not a substitute.")


def free_loopback_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


@dataclass
class Result:
    """Everything one batch printed, split into rows and server messages."""
    lines: list[str]
    sqlstate: str
    rows: list[list[str]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    details: list[str] = field(default_factory=list)

    @classmethod
    def parse(cls, lines: list[str], sqlstate: str) -> "Result":
        result = cls(lines=lines, sqlstate=sqlstate)
        for line in lines:
            match = MESSAGE.match(line)
            if match:
                kind, text = match.groups()
                if kind == "ERROR":
                    result.errors.append(text)
                elif kind == "DETAIL":
                    result.details.append(text)
            elif line.startswith("psql:"):
                result.errors.append(line)
            elif line != "":
                result.rows.append(line.split("|"))
        return result

    def column(self, index: int = 0) -> list[str]:
        return [row[index] for row in self.rows]


class LocalPostgres:
    """initdb, start, stop and delete one throwaway PostgreSQL 16 cluster."""

    def __init__(self, bin_dir: Path):
        self.bin = bin_dir
        self.root: Path | None = None
        self.port: int | None = None
        self.admin_password = secrets.token_urlsafe(18)
        self.os_user: str | None = None
        self.started = False

    # -- server lifecycle -------------------------------------------------
    def _server_command(self, tool: str, *args: str) -> subprocess.CompletedProcess:
        command = [str(self.bin / tool), *args]
        if self.os_user:  # initdb refuses to run as root, so the cluster belongs to another OS user
            command = ["runuser", "-u", self.os_user, "--", *command]
        env = {k: v for k, v in os.environ.items() if not k.startswith("PG")}
        env.update(LC_ALL="C", LANG="C")
        return subprocess.run(command, capture_output=True, text=True, env=env, timeout=120)

    def start(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="lab-l23-pg-"))
        owner = None
        if os.geteuid() == 0:
            try:
                owner = pwd.getpwnam("postgres")
            except KeyError as missing:
                raise LabError("running as root needs an OS user named postgres to own the cluster") from missing
            self.os_user = owner.pw_name
            os.chown(self.root, owner.pw_uid, owner.pw_gid)
        os.chmod(self.root, 0o700)
        password_file = self.root / "admin.pw"
        password_file.write_text(self.admin_password + "\n", encoding="utf-8")
        if owner:
            os.chown(password_file, owner.pw_uid, owner.pw_gid)
        os.chmod(password_file, 0o600)
        init = self._server_command(
            "initdb", "-D", str(self.root / "data"), "-U", ADMIN_ROLE, "-A", "scram-sha-256",
            f"--pwfile={password_file}", "-E", "UTF8", "--locale=C", "--no-instructions", "--no-sync")
        password_file.unlink()
        if init.returncode != 0:
            raise LabError(f"initdb failed: {init.stderr.strip()}")
        self.port = free_loopback_port()
        options = f"-p {self.port} -c listen_addresses=127.0.0.1 -c unix_socket_directories="
        started = self._server_command("pg_ctl", "-D", str(self.root / "data"), "-l",
                                       str(self.root / "server.log"), "-w", "-t", "60", "-o", options, "start")
        if started.returncode != 0:
            log = (self.root / "server.log").read_text(errors="replace") if (self.root / "server.log").exists() else ""
            raise LabError(f"pg_ctl start failed: {started.stderr.strip()} {log[-800:]}")
        self.started = True

    def stop(self) -> bool:
        """Stop the server and delete its directory. Returns True when nothing is left."""
        if self.root is None:
            return True
        if self.started:
            self._server_command("pg_ctl", "-D", str(self.root / "data"), "-m", "fast", "-w", "-t", "60", "stop")
            self.started = False
        shutil.rmtree(self.root, ignore_errors=True)
        return not self.root.exists()

    # -- clients ----------------------------------------------------------
    def client_env(self, password: str, app: str) -> dict[str, str]:
        env = {k: v for k, v in os.environ.items() if not k.startswith("PG")}
        env.update(PGPASSWORD=password, PGAPPNAME=app, PGTZ="UTC", PGCLIENTENCODING="UTF8",
                   PGSSLMODE="disable", PGCONNECT_TIMEOUT="10", LC_ALL="C", LANG="C")
        return env

    def psql_command(self, user: str, db: str, on_error_stop: bool, extra: tuple[str, ...] = ()) -> list[str]:
        return [str(self.bin / "psql"), "-X", "-q", "-A", "-t", "-v", f"ON_ERROR_STOP={int(on_error_stop)}",
                "-h", "127.0.0.1", "-p", str(self.port), "-U", user, "-d", db, *extra]

    def run(self, sql: str, *, db: str = "postgres", user: str = ADMIN_ROLE, password: str | None = None,
            app: str = "lab-l23-admin", on_error_stop: bool = True) -> subprocess.CompletedProcess:
        """One-shot psql: run a script, return exit code, stdout and stderr."""
        command = self.psql_command(user, db, on_error_stop, ("-f", "-"))
        env = self.client_env(self.admin_password if password is None else password, app)
        return subprocess.run(command, input=sql, capture_output=True, text=True, env=env, timeout=60)

    def run_file(self, path: Path, *, db: str) -> subprocess.CompletedProcess:
        command = self.psql_command(ADMIN_ROLE, db, True, ("-f", str(path)))
        return subprocess.run(command, capture_output=True, text=True,
                              env=self.client_env(self.admin_password, "lab-l23-admin"), timeout=60)

    def scalar(self, sql: str, *, db: str) -> str:
        done = self.run(sql, db=db)
        if done.returncode != 0:
            raise LabError(f"admin query failed: {done.stderr.strip()}")
        return done.stdout.strip()

    def session(self, *, db: str, user: str, password: str, app: str) -> "Session":
        return Session(self, db=db, user=user, password=password, app=app)

    def wait_for_activity(self, *, db: str, app: str, column: str, value: str, timeout: float = 15.0) -> str:
        """Poll pg_stat_activity (from a separate admin connection) until app's column equals value."""
        deadline = time.monotonic() + timeout
        seen = ""
        while time.monotonic() < deadline:
            seen = self.scalar(f"SELECT coalesce({column}, '') FROM pg_stat_activity "
                               f"WHERE datname = '{db}' AND application_name = '{app}';", db=db)
            if seen == value:
                return seen
            time.sleep(0.05)
        return seen

    def wait_until_gone(self, *, db: str, app: str, timeout: float = 15.0) -> bool:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            count = self.scalar(f"SELECT count(*) FROM pg_stat_activity WHERE application_name = '{app}';", db=db)
            if count == "0":
                return True
            time.sleep(0.05)
        return False


class Session:
    """One long-lived psql process: one connection, one server backend, statements sent in order.

    Each batch ends with a client-side sentinel that prints psql's SQLSTATE variable, so the
    caller knows the batch finished and how the last statement ended (00000 means success).
    """

    def __init__(self, server: LocalPostgres, *, db: str, user: str, password: str, app: str):
        self.app = app
        self.counter = 0
        self.proc = subprocess.Popen(server.psql_command(user, db, False), stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                     bufsize=1, env=server.client_env(password, app))
        self.lines: queue.Queue = queue.Queue()
        threading.Thread(target=self._read, daemon=True).start()
        hello = self.run("SELECT 'connected';")
        if hello.column() != ["connected"]:
            self.close()
            raise LabError(f"session {app} could not connect: {hello.lines}")

    def _read(self) -> None:
        assert self.proc.stdout is not None
        for line in self.proc.stdout:
            self.lines.put(line.rstrip("\n"))
        self.lines.put(None)

    def send(self, sql: str, variables: dict[str, object] | None = None) -> str:
        """Write a batch without waiting for it (it may block on a lock); returns its token."""
        self.counter += 1
        token = f"__LAB_END_{self.counter}__"
        prefix = ""
        for name, value in (variables or {}).items():
            text = str(value)
            if not SAFE_VALUE.match(text):
                raise ValueError(f"unsafe psql variable value for {name}: {text!r}")
            prefix += f"\\set {name} '{text}'\n"
        assert self.proc.stdin is not None
        self.proc.stdin.write(f"{prefix}{sql}\n\\echo {token} :SQLSTATE\n")
        self.proc.stdin.flush()
        return token

    def collect(self, token: str, timeout: float = 20.0) -> Result:
        lines: list[str] = []
        deadline = time.monotonic() + timeout
        while True:
            try:
                line = self.lines.get(timeout=max(0.01, deadline - time.monotonic()))
            except queue.Empty:
                return Result.parse(lines, "TIMEOUT")
            if line is None:
                return Result.parse(lines, "EOF")
            if line.startswith(token):
                return Result.parse(lines, line.split()[-1])
            lines.append(line)

    def run(self, sql: str, variables: dict[str, object] | None = None, timeout: float = 20.0) -> Result:
        return self.collect(self.send(sql, variables), timeout)

    def close(self) -> None:
        if self.proc.poll() is None:
            try:
                assert self.proc.stdin is not None
                self.proc.stdin.close()
            except OSError:
                pass
            try:
                self.proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait()
