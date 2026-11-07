#!/usr/bin/env python3
"""Canary 3 (t_full_generator) : observation de la nouvelle baseline (full generator match).

Même discipline que les générations précédentes (fenêtre 24 h, 30 min, aucun agent, verrou,
journal en ajout seul, rapport local-only), mais le contrôle technique porte sur
l'empreinte réellement publiée aujourd'hui : le générateur complet aligné (commit d976ce9).

Honnêteté : rendu navigateur et usage réel restent NON PROUVÉS ; la validation
humaine reste PENDING. Aucun PASS global n'est produit.
"""

import argparse
import json
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
import fcntl
import math
import os
import sys
import time
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = Path("data/canary-t_full_generator")
READBACK = Path("data/full-generator-observation/readback.json")
VERIFIED = "FULL_GENERATOR_OBSERVATION_VERIFIED"
BOOLEAN_FIELDS = (
    "candidate_match", "legacy_unchanged", "default_unchanged",
    "resources_unchanged", "dashboard_registry_unchanged",
)
INTERVAL = 1800
MAX_GAP = 2700
TIMEOUT = 180


def utc_now():
    return datetime.now(timezone.utc)


def utc(value):
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("UTC_REQUIRED")
    return value.astimezone(timezone.utc)


def timestamp(value):
    return utc(value).isoformat().replace("+00:00", "Z")


def parse_timestamp(value):
    return utc(datetime.fromisoformat(value.replace("Z", "+00:00")))


@contextmanager
def private_file(path, flags, mode):
    fd = os.open(path, flags | os.O_NOFOLLOW, 0o600)
    try:
        os.fchmod(fd, 0o600)
        stream = os.fdopen(fd, mode, encoding="utf-8")
    except BaseException:
        os.close(fd)
        raise
    with stream:
        yield stream


def public_fields(data, verified=VERIFIED, boolean_fields=BOOLEAN_FIELDS):
    if not isinstance(data, dict):
        data = {}
    fields = {
        "status": verified if data.get("status") == verified else None,
        "url": data.get("url") if isinstance(data.get("url"), str) else None,
        "views": data.get("views") if type(data.get("views")) is int else None,
    }
    fields.update({key: data.get(key) if type(data.get(key)) is bool else None
                   for key in boolean_fields})
    return fields


def assert_readback(fields, boolean_fields=BOOLEAN_FIELDS, verified=VERIFIED):
    if any(fields.get(key) is not True for key in boolean_fields):
        raise AssertionError("READBACK_BOOLEAN_NOT_TRUE")
    if (fields.get("status") != verified or not fields.get("url")
            or type(fields.get("views")) is not int or fields["views"] <= 0):
        raise AssertionError("READBACK_INVALID")


def fingerprint(path):
    try:
        stat = path.stat()
        return stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns
    except FileNotFoundError:
        return None


class Observer:
    DIRECTORY = DIRECTORY
    READBACK = READBACK
    VERIFIED = VERIFIED
    BOOLEAN_FIELDS = BOOLEAN_FIELDS
    VERIFY_COMMAND = ["tools/verify_full_generator_observation.py"]
    VALID_OUTCOME = "VERIFIED"
    TITLE = "# AI Nexus V4 — canary 3 (t_full_generator), Full Generator Match\n\n"

    def public_fields(self, data):
        return public_fields(data, self.VERIFIED, self.BOOLEAN_FIELDS)

    def assert_readback(self, fields):
        assert_readback(fields, self.BOOLEAN_FIELDS, self.VERIFIED)

    def markdown(self, report):
        return markdown(report, self.TITLE)

    def __init__(self, root=ROOT, clock=utc_now, monotonic=time.monotonic):
        self.root = Path(root)
        self.directory = self.root / self.DIRECTORY
        self.clock = clock
        self.monotonic = monotonic

    @contextmanager
    def locked(self, create=False):
        if create:
            self.directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        with private_file(self.directory / ".lock", os.O_CREAT | os.O_RDWR, "r+") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            try:
                yield
            finally:
                fcntl.flock(lock, fcntl.LOCK_UN)

    def state(self):
        with private_file(self.directory / "state.json", os.O_RDONLY, "r") as stream:
            state = json.load(stream)
        start = parse_timestamp(state["start_utc"])
        end = parse_timestamp(state["end_utc"])
        if (end - start != timedelta(hours=24)
                or state["interval_seconds"] != INTERVAL
                or state["human_validation"] != "PENDING"):
            raise ValueError("STATE_INVALID")
        return state, start, end

    def init(self):
        with self.locked(create=True):
            path = self.directory / "state.json"
            if path.exists():
                return self.state()[0]
            if (self.directory / "observations.jsonl").exists():
                raise ValueError("ORPHAN_OBSERVATIONS_PRESERVED")
            start = utc(self.clock())
            state = {"start_utc": timestamp(start),
                     "end_utc": timestamp(start + timedelta(hours=24)),
                     "interval_seconds": INTERVAL, "human_validation": "PENDING"}
            with private_file(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, "w") as stream:
                stream.write(json.dumps(state, sort_keys=True) + "\n")
                stream.flush()
                os.fsync(stream.fileno())
            return state

    def append(self, row):
        path = self.directory / "observations.jsonl"
        with private_file(path, os.O_CREAT | os.O_WRONLY | os.O_APPEND, "a") as stream:
            stream.write(json.dumps(row, sort_keys=True, allow_nan=False) + "\n")
            stream.flush()
            os.fsync(stream.fileno())

    def sample(self):
        with self.locked():
            _, start, end = self.state()
            began = utc(self.clock())
            if began >= end:
                return {"outcome": "NO_OP_FINISHED", "human_validation": "PENDING"}
            if began < start:
                raise ValueError("CLOCK_BEFORE_START")
            row = {"timestamp_utc": timestamp(began), "duration_seconds": 0,
                   "return_code": None, "outcome": "ERROR", "error": None,
                   "human_validation": "PENDING", **self.public_fields({})}
            tick = self.monotonic()
            try:
                previous = fingerprint(self.root / self.READBACK)
                env = dict(os.environ, PYTHONOPTIMIZE="", PYTHONDONTWRITEBYTECODE="1")
                result = subprocess.run(
                    [sys.executable, *self.VERIFY_COMMAND],
                    cwd=self.root, env=env, timeout=TIMEOUT, check=False,
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )
                row["return_code"] = result.returncode
                if result.returncode != 0:
                    row["error"] = "VERIFY_EXIT_NONZERO"
                else:
                    finished = utc(self.clock())
                    if fingerprint(self.root / self.READBACK) == previous:
                        raise AssertionError("READBACK_STALE")
                    with (self.root / self.READBACK).open(encoding="utf-8") as stream:
                        data = json.load(stream)
                    row.update(self.public_fields(data))
                    self.assert_readback(row)
                    checked = parse_timestamp(data["checked_at"])
                    if not began <= checked <= finished:
                        raise AssertionError("READBACK_STALE")
                    row["outcome"] = "VERIFIED"
            except subprocess.TimeoutExpired:
                row["outcome"] = "TIMEOUT"
                row["error"] = "VERIFY_TIMEOUT"
            except AssertionError as exc:
                known = {"READBACK_STALE", "READBACK_BOOLEAN_NOT_TRUE", "READBACK_INVALID"}
                row["error"] = str(exc) if str(exc) in known else "VERIFY_ERROR"
            except Exception:
                row["error"] = "VERIFY_OR_READBACK_ERROR"
            finally:
                row["duration_seconds"] = round(max(0, self.monotonic() - tick), 6)
                self.append(row)
            return row

    def report(self):
        with self.locked():
            state, start, end = self.state()
            now = utc(self.clock())
            points = []
            failures = 0
            count = 0
            last = start
            path = self.directory / "observations.jsonl"
            if path.exists():
                with private_file(path, os.O_RDONLY, "r") as stream:
                    for line in stream:
                        count += 1
                        try:
                            row = json.loads(line)
                            point = parse_timestamp(row["timestamp_utc"])
                            duration = row["duration_seconds"]
                            if (not start <= point < end or point < last or point > now
                                    or type(duration) not in (float, int)
                                    or not math.isfinite(duration) or duration < 0
                                    or row["outcome"] != self.VALID_OUTCOME
                                    or row["error"] is not None
                                    or type(row["return_code"]) is not int or row["return_code"] != 0
                                    or row["human_validation"] != "PENDING"):
                                raise ValueError("OBSERVATION_INVALID")
                            self.assert_readback(row)
                            points.append(point)
                            last = point
                        except (ValueError, KeyError, TypeError, AttributeError, AssertionError):
                            failures += 1
            boundary = max(start, min(now, end))
            edges = [start, *points, boundary]
            gap = max((b - a).total_seconds() for a, b in zip(edges, edges[1:]))
            if now < end:
                status = "IN_PROGRESS"
            elif failures:
                status = "TECHNICAL_FAIL"
            elif len(points) >= 48 and gap <= MAX_GAP:
                status = "TECHNICAL_PASS"
            else:
                status = "INCOMPLETE"
            return {**state, "status": status, "observations": count,
                    "valid_samples": len(points), "failures": failures,
                    "max_gap_seconds": gap, "browser_rendering": "NOT_PROVEN",
                    "real_usage": "NOT_PROVEN"}


def markdown(report, title="# AI Nexus V4 — canary 3 (t_full_generator)\n\n"):
    return (title
            + f"Statut technique : {report['status']}.\n\n"
            f"Fenêtre UTC : {report['start_utc']} → {report['end_utc']}. "
            "Intervalle prévu : 30 min.\n\n"
            f"Prélèvements : {report['observations']} ; valides : {report['valid_samples']} ; "
            f"échecs : {report['failures']}. Trou maximal, bornes incluses : "
            f"{report['max_gap_seconds'] / 60:g} min (jusqu'à maintenant si en cours).\n\n"
            "TECHNICAL_PASS exige 24 h révolues, au moins 48 prélèvements, aucun "
            "échec et aucun trou supérieur à 45 min.\n\n"
            "human_validation=PENDING. Aucun PASS global. Rendu navigateur et usage "
            "réel : NON PROUVÉS. Le readback technique ne remplace pas la QA humaine.\n")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("init", "sample", "report"))
    args = parser.parse_args(argv)
    observer = Observer()
    try:
        result = getattr(observer, args.command)()
    except BlockingIOError:
        print(json.dumps({"error": "OBSERVER_BUSY", "human_validation": "PENDING"}))
        return 2
    except Exception:
        print(json.dumps({"error": "LOCAL_STATE_OR_IO_ERROR", "human_validation": "PENDING"}))
        return 2
    print(observer.markdown(result) if args.command == "report"
          else json.dumps(result, sort_keys=True))
    if args.command == "sample" and result["outcome"] in ("ERROR", "TIMEOUT"):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())