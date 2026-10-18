"""Small Python model of the MCU policy for HEARTBEAT + PERCEPTION_HEALTH."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import json
from perception_health import FLAG_AGE_VALID, FLAG_MAPPING_VALID, TRACKING_STATES, U32_MAX

@dataclass
class Event:
    kind: str
    received_us: int
    age_at_send_us: int = 0
    tracking_state: int = 0
    flags: int = 0
    session_id: int = 0
    map_reset_counter: int = 0
    imu_initialized: bool = True

class SupervisorModel:
    def __init__(self, config=None):
        if config is None:
            config = json.loads((Path(__file__).parents[1] / "config.json").read_text())
        self.c = config
        self.state, self.reason = "INIT", "NONE"
        self.last_hb = self.last_health = None
        self.last_age = 0
        self.latched = False
        self.session_id = None
        self.map_reset_counter = None
        self.last_now = None
        self.last_report_fresh = False
        self.healthy_since = None

    def _transition(self, state, reason):
        if self.state != state or self.reason != reason:
            self.state, self.reason = state, reason

    def update(self, now_us: int, event: Event | None = None):
        if self.last_now is not None and now_us < self.last_now:
            self.latched = True; self._transition("FAILSAFE", "CLOCK_REGRESSION"); return self.state
        self.last_now = now_us
        if self.latched:
            return self.state
        # Existing deadlines expire before a newly received frame is considered.
        if self.last_hb is not None and now_us - self.last_hb >= self.c["heartbeat_timeout_us"]:
            self.latched = True; self._transition("FAILSAFE", "HEARTBEAT_TIMEOUT"); return self.state
        if self.last_health is not None:
            silence = now_us - self.last_health
            age = min(0xFFFFFFFFFFFFFFFF, self.last_age + silence + self.c["transit_bound_us"])
            if silence >= self.c["receipt_silence_timeout_us"] or age >= self.c["pose_age_timeout_us"]:
                self.latched = True
                self._transition("FAILSAFE", "SOURCE_AGE_TIMEOUT" if age >= self.c["pose_age_timeout_us"] else "RESULT_TIMEOUT")
                return self.state
            if silence >= self.c["receipt_silence_hold_us"]:
                self._transition("HOLD", "RESULT_SILENCE"); self.healthy_since = None; return self.state
            if age >= self.c["pose_age_hold_us"]:
                self._transition("HOLD", "SOURCE_AGE_HOLD"); self.healthy_since = None; return self.state
        if event is not None:
            if event.kind == "heartbeat":
                if self.session_id is None or self.session_id != event.session_id:
                    self.session_id = event.session_id
                    self.last_hb = None; self.last_health = None
                    self.map_reset_counter = None
                    self.last_report_fresh = False
                    if self.state != "INIT": self._transition("INIT", "SESSION_CHANGE")
                self.last_hb = event.received_us
            elif event.kind == "health":
                reset_changed = self.map_reset_counter is not None and event.map_reset_counter != self.map_reset_counter
                self.map_reset_counter = event.map_reset_counter
                self.last_health = event.received_us
                self.last_age = min(U32_MAX, event.age_at_send_us)
                self.last_report_fresh = False
                if event.tracking_state == TRACKING_STATES["LOST"]:
                    self.latched = True; self._transition("FAILSAFE", "TRACKING_LOST"); return self.state
                if event.flags & (FLAG_AGE_VALID | FLAG_MAPPING_VALID) != (FLAG_AGE_VALID | FLAG_MAPPING_VALID):
                    self._transition("HOLD", "SOURCE_AGE_UNAVAILABLE"); self.healthy_since = None; return self.state
                if self.last_age >= self.c["pose_age_timeout_us"]:
                    self.latched = True; self._transition("FAILSAFE", "SOURCE_AGE_TIMEOUT"); return self.state
                if self.last_age >= self.c["pose_age_hold_us"] or event.flags & 4 or not event.imu_initialized or reset_changed or event.tracking_state not in (TRACKING_STATES["OK"], TRACKING_STATES["OK_KLT"]):
                    self._transition("HOLD", "SOURCE_AGE_HOLD" if self.last_age >= self.c["pose_age_hold_us"] else "MAP_RESET" if reset_changed else "PERCEPTION_DEGRADED")
                    self.healthy_since = None; return self.state
                self.last_report_fresh = True
        if self.last_hb is not None and self.last_health is not None:
            age = self.last_age + max(0, now_us - self.last_health) + self.c["transit_bound_us"]
            if self.last_report_fresh and age < self.c["pose_age_hold_us"] and now_us - self.last_hb < self.c["heartbeat_timeout_us"]:
                self._transition("FRESH", "READY")
        return self.state

    def rearm(self, now_us: int):
        """Explicit local action; clears the latch and returns to safe INIT."""
        if not self.latched: return False
        self.latched = False; self.last_hb = self.last_health = None
        self.last_report_fresh = False; self.map_reset_counter = None
        self.healthy_since = None; self._transition("INIT", "REARM")
        return True
