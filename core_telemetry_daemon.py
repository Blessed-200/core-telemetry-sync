#!/usr/bin/env python3
"""
========================================================================================
CORE TELEMETRY DAEMON — SPORTS ORACLE LIVE PRODUCTION SERVER (F11.1)
========================================================================================
- Logs en tiempo real (unbuffered) de cada barrido y cada mesa en vivo.
- Identificación exacta de Torneo, Fase (Group/Final), Match ID y Hora Inicio (Cuba/UTC).
- Notificación automática a Telegram al disparar el pick Y al liquidar el resultado final.
- Cierre limpio a los 195 minutos para evitar cancelaciones por timeout en GitHub Actions.
========================================================================================
"""

import csv
import gzip
import itertools
import json
import math
import os
import random
import smtplib
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, List, Tuple, Optional, Any
import numpy as np

# Forzar salida inmediata en consola para GitHub Actions
sys.stdout.reconfigure(line_buffering=True)

DEFAULT_TOKENS = [
    "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyXzMyMDMiLCJpc3MiOiJsaWdhX3Byb19jel9iYWNrZW5kIiwiZXhwIjoxNzkzNzkzNzUxLCJpYXQiOjE3OTEyMDE3NTEsImp0aSI6ImE4OTFiOGIwYzExMzQzOTM5NjEzYTI5MjJmYWIzZjYyIiwiYXVkIjpbImxpZ2FfcHJvX2N6Il0sInVzZXJfaWQiOjMyMDMsInJvbGVzIjpbMl19.PCOxG8COAR4WrAVMPCn2ue0jh5NZziQiTwB39FwMSXARIgAfRxLtD2OE_ET-bfhnGA4PzWc6ufHgBJ9SXSMbSe7s5S4a3kdyN_Me_F--WLDQ0Efr9-DFRW4CibzDNIjhcUPhssvdK7JXYvcf71oEwWZavZcXcPLGU2EmSDreMkYpge56_7BiwH3qESBOt39sVHmAI_pf02Q4_md0SnyVOIB0iU7zG00tJh-ma53LIwXPsb22G-AvjaGh1J7KCBOKdjUfSvV9jHqT08tXvRCJRjA4hAvDDx4rkcYWcvDAldQ9ndvD9wql84F_B2uaRaetNVNGasZ0P2Vgt0xxT1xcngdgiKXa_Yv7SbJg5Bq6kDSjVfFlbXTIhpGjHzvahu4nQBCK9e89zpPZ2FcdEUzh__k3CcEsAvUyriQjSRtCiW5h9jUAmETwueZDa4FfMHzUoNAYx9bYZNzdeQXwhmv20AlQQvZGVIcBnsgwMnCz6YIqg6h3RtB4-9eIpvGdv02XGl4vGX4g342oZphWGJQOhV4XL4aF571j_RmonecSbFNqPcAKXIpmbXzYZJI7c26RDZtwS7ztDVpysEt2whc7dK8TWchj9liEkA4iy5hl3gYv3XE4kNvDU-2FgL5E71aeW4AzE_FTYPHjOh0QHM4AZJ_FZG64EY5mcEAiayD2XUk",
    "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyXzMyMDQiLCJpc3MiOiJsaWdhX3Byb19jel9iYWNrZW5kIiwiZXhwIjoxNzkzNzk0MDU1LCJpYXQiOjE3OTEyMDIwNTUsImp0aSI6Ijg0NjAzNmEzNTdjODRkMTA4ZTdkZWQ5NWNkZTRiNGZmIiwiYXVkIjpbImxpZ2FfcHJvX2N6Il0sInVzZXJfaWQiOjMyMDQsInJvbGVzIjpbMl19.anwTv8jH1821iIfgcUuxCWx0aWIWAn7zc0j1qJPoZl-NrVdfY27Au1Jpgb9YSiRGhCUtoMm3dULJckbgWSmD3EWyIN2IavInAudienr7Sr6zcN6HzpLr1XFKwciYPW77ZYMSYkgfTrWoSt9vPymmzcjVtR-CaxlEFtkSuY4MTu71UtiI8yY4AowlgoBzqFkRYz1eB5z4dilGpgYXqMw1ZPX7ErrYw_yUxQEOWyoK_L2mygQIgcuwdDuZWqNlJyWAJXjsA8XnNamXIJNM_ru0Ky3glSkoLnl_mkAp7jyxN_eXrZdY6iLvWcNGxOlrDKh5MtayEl6vbT50wNtc4-4ywGgNGW4cKAYM5xQ7jAOpwhY_TKHg6JJcDFPhal-vZ4--oY7mBzB49vl-ghblYeg36hOAMgHAyk6m72YoosbUW0aUKmas6dXE4APLG92W-kcJu_wk09i-yFZZ4mPGABnA4h1b6s5NAavDC6qbXB5QKsy28l9AqmP3W-RQZdbCnAhmXnUVd8ZyCOVPo73jE7G_npxioRgza5RYS6h15ju9m9gpiFAh3qVmi4nnsp7GKc8viD4hr2Yvg2gB5LoT_X8SD5Ktq2iTCfjll3HOiIU_BdNvcjUaQMdT3uhIGJKCmXZPPXfkGWWpglOWr-nscG4stQS5kdMuifjwJ-eF4s2kVsw",
    "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyXzMyMDUiLCJpc3MiOiJsaWdhX3Byb19jel9iYWNrZW5kIiwiZXhwIjoxNzkzNzk0MzY5LCJpYXQiOjE3OTEyMDIzNjksImp0aSI6IjEwODVkZGEwZmFmYzRmMTM5ZWRlZjg3YTkxZTE5ZTlhIiwiYXVkIjpbImxpZ2FfcHJvX2N6Il0sInVzZXJfaWQiOjMyMDUsInJvbGVzIjpbMl19.KAQJj0WRDfSve-xT4vgqD88gVL6a62FrbQV3I6A-OUF5nVQ7rwuXz0e2t56guIr9OSSoVk_fD_kp1eCg9JJsc9Wqva1fKg6XOm849jzxONEpwqvtnrnPCpUjQe1i6GFkkN6U6b0z5RdrnjjS9X9oyVuHwjzw7itttmjb5-WPjoanyvgZfaMoH-7vWcN54dDPp9n3l2u8dY9uq2rSsx4_CXnZyjTDCH_zOx-l59Zo-iJGakciS4JF5toU5y270hDpfI7HUCGv5rHHutChnVdlL8B-ifRrKDiWhmlro2fZe2aqsyhcUkx-cYANfi1cv0KxFL6ovtwbrBCOoYC-de4Ft23H0fcm-_7e00LQcRM1YNIVuKZpaQngm0XBw99M6XM4zJ9oEvU27qc7HdhPb9RNasC7IfZWusUPgoB4JGtHAo2aVfXfyVb7B4-1aqgp9yDbmGeadPLpHgsR1V7ozy5X8NYIO5VB1AUb9Xl7HniC-aEWdXpSThimDK_5QJ7Gwl0D1d2lK1hrOQxv2yOWy1dq11UpBgpCUD_9KdSHY-DTwnBxhULQ4rfol1zBYHnOfTYsJ0Sgwj1Csu9VSemfR5MOrN4DVhUK82JvQ_NF75m5WQrNRMLLNU0MgMNVEL6z3ux3lBSww_q8f-pJrMjqvkGjhBhbOYFY9X5kjS35dBMc0YA",
]

token_cycle = itertools.cycle(DEFAULT_TOKENS)


def get_headers() -> Dict[str, str]:
    token = next(token_cycle)
    return {
        "User-Agent": (
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4_1 like Mac OS X) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Mobile/15E148 Safari/604.1"
        ),
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9,es;q=0.8",
        "Origin": "https://tt.league-pro.com",
        "Referer": "https://tt.league-pro.com/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "Accept-Encoding": "gzip",
        "Authorization": f"Bearer {token.strip()}",
    }


def api_get_json(url: str, min_delay: float = 0.40, max_delay: float = 0.75) -> Optional[Dict[str, Any]]:
    time.sleep(random.uniform(min_delay, max_delay))
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers=get_headers())
            with urllib.request.urlopen(req, timeout=20) as r:
                raw = r.read()
                if r.headers.get("Content-Encoding") == "gzip":
                    raw = gzip.decompress(raw)
                return json.loads(raw)
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(12 + 8 * attempt)
                continue
            if e.code in (401, 403):
                time.sleep(3)
                continue
            if e.code == 404:
                return None
        except Exception:
            time.sleep(2)
    return None


def format_match_times(iso_str: str) -> str:
    if not iso_str:
        return "N/A"
    try:
        dt_utc = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        dt_cuba = dt_utc - timedelta(hours=4)
        return f"{dt_cuba.strftime('%I:%M %p')} Cuba ({dt_utc.strftime('%H:%M')} UTC)"
    except Exception:
        return iso_str


CONFIG = {
    "m2a": {
        "min_x1_deuce": 22,
        "max_abs_delta_rating": 25.0,
        "line_offset": 50.5,
        "odds_target": 1.62,
        "odds_floor": 1.60,
        "p_base_logit": 0.85,
        "w_asym_penalty": 1.40,
        "w_exp_bonus": 0.22,
        "w_res_bonus": 0.30,
        "w_rating_dist": 0.010,
        "h2h_asym_cutoff": 0.64,
        "h2h_matches_min": 5,
        "mu_m_loser_floor": 7.20,
        "n_min_fragile": 120,
        "dr_fragile_gap": 18.0,
        "kelly_multiplier": 0.05,
        "stake_min": 0.018,
        "stake_max": 0.030,
    },
    "m1b": {
        "x12_min": 38,
        "x12_max": 44,
        "max_trailer_h2h_wr": 0.35,
        "line_offset": 31.5,
        "odds_target": 1.86,
        "odds_floor": 1.82,
        "p_base_logit": 0.42,
        "w_trailer_penalty": 0.90,
        "w_res_mitigation": 0.20,
        "kelly_multiplier": 0.04,
        "stake_min": 0.018,
        "stake_max": 0.025,
    },
    "execution": {
        "initial_bankroll_usd": float(os.environ.get("INITIAL_BANKROLL", "100.0")),
        "table_liquidity_cap_usd": 180.0,
        "min_bet_usd": 1.0,
    },
}

STATE_FILE = "oracle_live_state.json"
LEDGER_CSV = "institutional_ledger.csv"
KPIS_JSON = "institutional_kpis.json"


class CausalPITTracker:
    def __init__(self, eb_prior_m: float = 7.48, eb_weight: float = 50.0):
        self.eb_prior_m = eb_prior_m
        self.eb_weight = eb_weight
        self.player_ratings: Dict[int, float] = {}
        self.player_match_counts: Dict[int, int] = {}
        self.player_loss_points: Dict[int, List[float]] = {}
        self.h2h_records: Dict[Tuple[int, int], Dict[int, int]] = {}
        self.player_names: Dict[int, str] = {}
        self.processed_match_ids: set = set()
        self.evaluated_set1_ids: set = set()
        self.evaluated_set2_ids: set = set()
        self.last_synced_utc: str = "2026-10-06T00:00:00Z"

    def load_seed_vault_if_needed(
        self,
        players_path: str = "PIT_PLAYER_RATINGS_AND_RESISTANCE.json",
        h2h_path: str = "PIT_H2H_MATRIX.json",
    ):
        if os.path.exists(players_path):
            with open(players_path, "r", encoding="utf-8") as f:
                p_data = json.load(f)
            for pid_str, info in p_data.items():
                pid = int(pid_str)
                self.player_names[pid] = info.get("name", f"P_{pid}")
                self.player_ratings[pid] = float(info.get("latest_rating", 600.0))
                cnt = int(info.get("total_matches_2026", 0))
                self.player_match_counts[pid] = cnt
                mean_m = float(info.get("mean_resistance_m_s", self.eb_prior_m))
                n_sets = min(max(cnt * 3, 1), 50)
                self.player_loss_points[pid] = [round(mean_m, 3)] * n_sets

        if os.path.exists(h2h_path):
            with open(h2h_path, "r", encoding="utf-8") as f:
                h_data = json.load(f)
            for pair_key, rec in h_data.items():
                parts = pair_key.replace("_vs_", "_").split("_")
                p1, p2 = int(parts[0]), int(parts[1])
                pair = (min(p1, p2), max(p1, p2))
                self.h2h_records[pair] = {
                    p1: int(rec.get(str(p1), 0)),
                    p2: int(rec.get(str(p2), 0)),
                }

    def get_player_experience(self, player_id: int) -> int:
        return self.player_match_counts.get(player_id, 0)

    def get_player_rating(self, player_id: int, fallback: float = 600.0) -> float:
        return self.player_ratings.get(player_id, fallback)

    def get_h2h_stats(self, p1_id: int, p2_id: int) -> Tuple[int, int, int, float]:
        pair = (min(p1_id, p2_id), max(p1_id, p2_id))
        record = self.h2h_records.get(pair, {p1_id: 0, p2_id: 0})
        p1_w = record.get(p1_id, 0)
        p2_w = record.get(p2_id, 0)
        total = p1_w + p2_w
        wr_p1 = (p1_w / total) if total > 0 else 0.50
        return total, p1_w, p2_w, wr_p1

    def get_resistance_profile(self, player_id: int) -> Tuple[float, float, float]:
        history = self.player_loss_points.get(player_id, [])
        if not history:
            return self.eb_prior_m, 1.80, self.eb_prior_m
        recent = history[-50:]
        mu = float(np.mean(recent))
        std = float(np.std(recent)) if len(recent) > 1 else 1.80
        mu_eb = (sum(recent) + self.eb_weight * self.eb_prior_m) / (len(recent) + self.eb_weight)
        return mu, std, mu_eb

    def update_match_outcome(
        self,
        m_id: int,
        p1_id: int,
        p2_id: int,
        r1: float,
        r2: float,
        score_str: str,
        set_scores: List[Tuple[int, int]],
        p1_name: str = "",
        p2_name: str = "",
        match_date_utc: str = "",
    ):
        if m_id in self.processed_match_ids:
            return
        self.processed_match_ids.add(m_id)
        if r1 > 0:
            self.player_ratings[p1_id] = r1
        if r2 > 0:
            self.player_ratings[p2_id] = r2
        self.player_match_counts[p1_id] = self.player_match_counts.get(p1_id, 0) + 1
        self.player_match_counts[p2_id] = self.player_match_counts.get(p2_id, 0) + 1
        if p1_name:
            self.player_names[p1_id] = p1_name
        if p2_name:
            self.player_names[p2_id] = p2_name

        pair = (min(p1_id, p2_id), max(p1_id, p2_id))
        if pair not in self.h2h_records:
            self.h2h_records[pair] = {p1_id: 0, p2_id: 0}
        winner_id = p1_id if score_str.startswith("3-") else p2_id
        self.h2h_records[pair][winner_id] = self.h2h_records[pair].get(winner_id, 0) + 1

        if p1_id not in self.player_loss_points:
            self.player_loss_points[p1_id] = []
        if p2_id not in self.player_loss_points:
            self.player_loss_points[p2_id] = []
        for pt1, pt2 in set_scores:
            if pt1 + pt2 > 0:
                ms = float(min(pt1, pt2))
                self.player_loss_points[p1_id].append(ms)
                self.player_loss_points[p2_id].append(ms)
        self.player_loss_points[p1_id] = self.player_loss_points[p1_id][-50:]
        self.player_loss_points[p2_id] = self.player_loss_points[p2_id][-50:]

        if match_date_utc and match_date_utc > self.last_synced_utc:
            self.last_synced_utc = match_date_utc


class UniversalPhysicsEngine:
    def __init__(self, config: Dict[str, Any] = CONFIG):
        self.cfg = config
        self.m2a_cfg = config["m2a"]
        self.m1b_cfg = config["m1b"]
        self.exec_cfg = config["execution"]

    def compute_p_structural_2a(
        self, abs_dr: float, h2h_wr_s1_win: float, n_min: int, res_mean_min: float
    ) -> float:
        c = self.m2a_cfg
        asym_penalty = c["w_asym_penalty"] * max(h2h_wr_s1_win - 0.50, 0.0)
        exp_factor = c["w_exp_bonus"] * min(n_min / 50.0, 1.0)
        res_factor = c["w_res_bonus"] * (res_mean_min - 7.20)
        rating_dist = c["w_rating_dist"] * abs_dr
        logit = c["p_base_logit"] - asym_penalty + exp_factor + res_factor - rating_dist
        return float(1.0 / (1.0 + math.exp(-logit)))

    def is_joint_collapse_risk_m2a(
        self, h2h_wr_s1_win: float, h2h_n: int, mu_m_loser: float, n_min: int, abs_dr: float
    ) -> Tuple[bool, str]:
        c = self.m2a_cfg
        cond1 = (
            (h2h_wr_s1_win > c["h2h_asym_cutoff"])
            and (h2h_n >= c["h2h_matches_min"])
            and (mu_m_loser < c["mu_m_loser_floor"])
        )
        if cond1:
            return True, "JOINT_COLLAPSE_ASYMMETRY"
        cond2 = (n_min < c["n_min_fragile"]) and (abs_dr > c["dr_fragile_gap"])
        if cond2:
            return True, "RUIDO_EPISTEMICO_BAJA_MUESTRA"
        return False, "APROBADO_ESTRUCTURALMENTE"

    def calculate_kelly_stake(
        self, p_struct: float, odds: float, n_min: int, bankroll: float, is_motor_2a: bool = True
    ) -> Tuple[float, float, float]:
        cfg_m = self.m2a_cfg if is_motor_2a else self.m1b_cfg
        b_net = odds - 1.0
        ev = p_struct * odds - 1.0
        if ev <= 0:
            return 0.0, 0.0, ev
        full_kelly = ev / b_net
        conf_weight = min(n_min / 40.0, 1.0)
        raw_pct = cfg_m["stake_min"] + cfg_m["kelly_multiplier"] * full_kelly * conf_weight
        stake_pct = float(np.clip(raw_pct, cfg_m["stake_min"], cfg_m["stake_max"]))
        nominal_stake = round(bankroll * stake_pct, 2)
        capped_stake = min(nominal_stake, self.exec_cfg["table_liquidity_cap_usd"])
        final_stake = max(capped_stake, self.exec_cfg["min_bet_usd"])
        return final_stake, stake_pct, ev

    def evaluate_live_set1(
        self,
        p1_id: int,
        p2_id: int,
        r1: float,
        r2: float,
        p1_s1: int,
        p2_s1: int,
        tracker: CausalPITTracker,
        bankroll: float,
        current_screen_odds: float = 1.62,
    ) -> Dict[str, Any]:
        x1 = p1_s1 + p2_s1
        abs_dr = abs(r1 - r2)
        c = self.m2a_cfg
        if x1 < c["min_x1_deuce"]:
            return {"action": "NO_BET", "reason": f"No Deuce ({p1_s1}-{p2_s1}, {x1} pts)"}
        if abs_dr > c["max_abs_delta_rating"]:
            return {"action": "NO_BET", "reason": f"|Delta Rating|={abs_dr:.0f} > 25"}

        s1_winner = p1_id if p1_s1 > p2_s1 else p2_id
        s1_loser = p2_id if p1_s1 > p2_s1 else p1_id
        h2h_n, _, _, wr_p1 = tracker.get_h2h_stats(p1_id, p2_id)
        h2h_wr_s1_win = wr_p1 if s1_winner == p1_id else (1.0 - wr_p1)
        mu_loser, _, _ = tracker.get_resistance_profile(s1_loser)
        mu_w, _, _ = tracker.get_resistance_profile(s1_winner)
        res_mean_min = min(mu_loser, mu_w)
        n_min = min(tracker.get_player_experience(p1_id), tracker.get_player_experience(p2_id))

        is_risk, risk_reason = self.is_joint_collapse_risk_m2a(
            h2h_wr_s1_win, h2h_n, mu_loser, n_min, abs_dr
        )
        if is_risk:
            return {"action": "NO_BET", "reason": risk_reason}

        p_struct = self.compute_p_structural_2a(abs_dr, h2h_wr_s1_win, n_min, res_mean_min)
        effective_odds = max(current_screen_odds, c["odds_floor"])
        stake_usd, stake_pct, ev = self.calculate_kelly_stake(
            p_struct, effective_odds, n_min, bankroll, is_motor_2a=True
        )
        target_line = x1 + c["line_offset"]
        return {
            "action": "BET",
            "motor": "Motor 2A F11.1 (OVER ÉLITE)",
            "selection": f"Más de {target_line:.1f} Puntos",
            "target_line": target_line,
            "screen_odds": effective_odds,
            "p_structural": round(p_struct, 4),
            "expected_value": round(ev, 4),
            "recommended_stake_pct": round(stake_pct, 4),
            "stake_usd": stake_usd,
            "state_desc": f"Set 1 Deuce: {p1_s1}-{p2_s1} ({x1} pts)",
        }

    def evaluate_live_set2(
        self,
        p1_id: int,
        p2_id: int,
        r1: float,
        r2: float,
        p1_s1: int,
        p2_s1: int,
        p1_s2: int,
        p2_s2: int,
        tracker: CausalPITTracker,
        bankroll: float,
        current_screen_odds: float = 1.86,
    ) -> Dict[str, Any]:
        s1_w = p1_s1 > p2_s1
        s2_w = p1_s2 > p2_s2
        is_2_0 = (s1_w and s2_w) or ((not s1_w) and (not s2_w))
        if not is_2_0:
            return {"action": "NO_BET", "reason": "Empate 1-1 en sets"}

        x12 = p1_s1 + p2_s1 + p1_s2 + p2_s2
        c = self.m1b_cfg
        if not (c["x12_min"] <= x12 <= c["x12_max"]):
            return {"action": "NO_BET", "reason": f"X12={x12} fuera de [38, 44]"}

        leader_is_p1 = s1_w and s2_w
        leader_r = r1 if leader_is_p1 else r2
        trailer_r = r2 if leader_is_p1 else r1
        trailer_id = p2_id if leader_is_p1 else p1_id

        if trailer_r > leader_r:
            return {"action": "NO_BET", "reason": f"Perseguidor favorito ({trailer_r:.0f} > {leader_r:.0f})"}

        h2h_n, _, _, wr_p1 = tracker.get_h2h_stats(p1_id, p2_id)
        wr_trailer = (1.0 - wr_p1) if leader_is_p1 else wr_p1
        if h2h_n >= 3 and wr_trailer > c["max_trailer_h2h_wr"]:
            return {"action": "NO_BET", "reason": f"H2H perseguidor alto ({wr_trailer*100:.1f}% > 35%)"}

        mu_trailer, _, _ = tracker.get_resistance_profile(trailer_id)
        logit_1b = (
            c["p_base_logit"]
            + c["w_trailer_penalty"] * max(c["max_trailer_h2h_wr"] - wr_trailer, 0.0)
            - c["w_res_mitigation"] * max(mu_trailer - 7.50, 0.0)
        )
        p_struct = float(1.0 / (1.0 + math.exp(-logit_1b)))
        n_min = min(tracker.get_player_experience(p1_id), tracker.get_player_experience(p2_id))
        effective_odds = max(current_screen_odds, c["odds_floor"])
        stake_usd, stake_pct, ev = self.calculate_kelly_stake(
            p_struct, effective_odds, n_min, bankroll, is_motor_2a=False
        )
        target_line = x12 + c["line_offset"]
        return {
            "action": "BET",
            "motor": "Motor 1B F11.1 (UNDER 2-0 CERRADO)",
            "selection": f"Menos de {target_line:.1f} Puntos",
            "target_line": target_line,
            "screen_odds": effective_odds,
            "p_structural": round(p_struct, 4),
            "expected_value": round(ev, 4),
            "recommended_stake_pct": round(stake_pct, 4),
            "stake_usd": stake_usd,
            "state_desc": f"Marcador 2-0 Cerrado: {p1_s1}-{p2_s1}, {p1_s2}-{p2_s2} ({x12} pts)",
        }


def send_live_alert(subject: str, body_text: str):
    print("\n" + "=" * 65, flush=True)
    print(body_text, flush=True)
    print("=" * 65 + "\n", flush=True)

    tg_token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    tg_chat = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    if tg_token and tg_chat:
        try:
            tg_url = f"https://api.telegram.org/bot{tg_token}/sendMessage"
            payload = json.dumps({"chat_id": tg_chat, "text": body_text}).encode("utf-8")
            req = urllib.request.Request(
                tg_url, data=payload, headers={"Content-Type": "application/json"}
            )
            urllib.request.urlopen(req, timeout=10)
        except Exception as e:
            print(f"[WARN] Error enviando Telegram: {e}", flush=True)

    smtp_user = os.environ.get("SMTP_EMAIL", "").strip()
    smtp_pass = os.environ.get("SMTP_PASSWORD", "").strip()
    to_email = os.environ.get("ALERT_TO_EMAIL", smtp_user).strip()
    if smtp_user and smtp_pass and to_email:
        try:
            msg = MIMEMultipart()
            msg["From"] = smtp_user
            msg["To"] = to_email
            msg["Subject"] = subject
            msg.attach(MIMEText(body_text, "plain", "utf-8"))
            with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=15) as server:
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)
        except Exception as e:
            print(f"[WARN] Error enviando Email SMTP: {e}", flush=True)


class InstitutionalPortfolio:
    def __init__(self, initial_bankroll: float = 100.0):
        self.balance = initial_bankroll
        self.peak_balance = initial_bankroll
        self.max_drawdown = 0.0
        self.active_bets: List[Dict[str, Any]] = []
        self.settled_bets: List[Dict[str, Any]] = []

    def save_full_state(self, tracker: CausalPITTracker):
        state = {
            "last_synced_utc": tracker.last_synced_utc,
            "balance": round(self.balance, 2),
            "peak_balance": round(self.peak_balance, 2),
            "max_drawdown": round(self.max_drawdown, 4),
            "active_bets": self.active_bets,
            "settled_bets": self.settled_bets,
            "processed_match_ids": list(tracker.processed_match_ids)[-10000:],
            "evaluated_set1_ids": list(tracker.evaluated_set1_ids)[-3000:],
            "evaluated_set2_ids": list(tracker.evaluated_set2_ids)[-3000:],
            "player_ratings": {str(k): v for k, v in tracker.player_ratings.items()},
            "player_match_counts": {str(k): v for k, v in tracker.player_match_counts.items()},
            "player_names": {str(k): v for k, v in tracker.player_names.items()},
            "player_loss_points": {str(k): v for k, v in tracker.player_loss_points.items()},
            "h2h_records": {f"{k[0]}_vs_{k[1]}": v for k, v in tracker.h2h_records.items()},
        }
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False)

    def load_full_state(self, tracker: CausalPITTracker) -> bool:
        if not os.path.exists(STATE_FILE) or os.path.getsize(STATE_FILE) < 50:
            return False
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            state = json.load(f)
        tracker.last_synced_utc = state.get("last_synced_utc", "2026-10-06T00:00:00Z")
        self.balance = float(state.get("balance", self.balance))
        self.peak_balance = float(state.get("peak_balance", self.peak_balance))
        self.max_drawdown = float(state.get("max_drawdown", 0.0))
        self.active_bets = state.get("active_bets", [])
        self.settled_bets = state.get("settled_bets", [])
        tracker.processed_match_ids = set(state.get("processed_match_ids", []))
        tracker.evaluated_set1_ids = set(state.get("evaluated_set1_ids", []))
        tracker.evaluated_set2_ids = set(state.get("evaluated_set2_ids", []))
        tracker.player_ratings = {int(k): float(v) for k, v in state.get("player_ratings", {}).items()}
        tracker.player_match_counts = {int(k): int(v) for k, v in state.get("player_match_counts", {}).items()}
        tracker.player_names = {int(k): v for k, v in state.get("player_names", {}).items()}
        tracker.player_loss_points = {
            int(k): [float(x) for x in v] for k, v in state.get("player_loss_points", {}).items()
        }
        tracker.h2h_records = {}
        for pair_str, rec in state.get("h2h_records", {}).items():
            parts = pair_str.replace("_vs_", "_").split("_")
            pair = (int(parts[0]), int(parts[1]))
            tracker.h2h_records[pair] = {int(pk): int(pv) for pk, pv in rec.items()}
        return True

    def update_institutional_files(self):
        # Siempre escribir el archivo CSV (incluso si hay 0 apuestas) para que git add nunca falle
        keys = [
            "match_id", "match_start_utc", "tournament_stage", "timestamp_utc",
            "players", "motor", "state_desc", "selection", "odds", "stake_usd",
            "final_sets_score", "actual_points", "result", "pnl_usd", "balance_after"
        ]
        with open(LEDGER_CSV, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
            w.writeheader()
            if self.settled_bets:
                w.writerows(self.settled_bets)

        total = len(self.settled_bets)
        wins = sum(1 for b in self.settled_bets if b.get("result") == "GANADA")
        losses = total - wins
        vol = sum(float(b.get("stake_usd", 0)) for b in self.settled_bets)
        net_pnl = sum(float(b.get("pnl_usd", 0)) for b in self.settled_bets)
        gross_win = sum(float(b.get("pnl_usd", 0)) for b in self.settled_bets if float(b.get("pnl_usd", 0)) > 0)
        gross_loss = abs(sum(float(b.get("pnl_usd", 0)) for b in self.settled_bets if float(b.get("pnl_usd", 0)) < 0))

        kpis = {
            "updated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "current_balance_usd": round(self.balance, 2),
            "peak_balance_usd": round(self.peak_balance, 2),
            "total_settled_picks": total,
            "active_pending_picks": len(self.active_bets),
            "wins": wins,
            "losses": losses,
            "strike_rate_pct": round((wins / total) * 100, 2) if total > 0 else 0.0,
            "total_volume_usd": round(vol, 2),
            "net_profit_usd": round(net_pnl, 2),
            "roi_yield_pct": round((net_pnl / vol) * 100, 2) if vol > 0 else 0.0,
            "profit_factor": round(gross_win / gross_loss, 2) if gross_loss > 0 else 99.9,
            "max_drawdown_pct": round(self.max_drawdown * 100, 2),
        }
        with open(KPIS_JSON, "w", encoding="utf-8") as f:
            json.dump(kpis, f, indent=2, ensure_ascii=False)


def sync_historical_gap(tracker: CausalPITTracker, portfolio: InstitutionalPortfolio):
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"[SYNC] Verificando partidos terminados desde {tracker.last_synced_utc} hasta {now_str}...", flush=True)
    base_url = (
        "https://api.league-pro.com/matches?sport_id=2&limit=100"
        f"&date_from={tracker.last_synced_utc}&date_to={now_str}"
        "&order_field=start_game&order_type=asc"
    )
    offset = 0
    new_finished_ids = []
    while True:
        d = api_get_json(f"{base_url}&offset={offset}", min_delay=0.25, max_delay=0.45)
        if not d:
            break
        items = d.get("items") or []
        total = (d.get("pagination") or {}).get("total_items", 0)
        if not items:
            break
        for m in items:
            m_id = int(m.get("id") or 0)
            if m.get("status") == 3 and m_id not in tracker.processed_match_ids:
                new_finished_ids.append(m_id)
        offset += len(items)
        if offset >= total:
            break

    print(f"[SYNC] Partidos nuevos finalizados por actualizar en PIT: {len(new_finished_ids)}", flush=True)
    for idx, m_id in enumerate(new_finished_ids, 1):
        page = api_get_json(f"https://api.league-pro.com/pages/matches/{m_id}", 0.25, 0.45)
        if not page or "match" not in page:
            continue
        m = page["match"]
        res = m.get("results") or {}
        if res.get("finish_type") != 1:
            continue
        ps = res.get("period_scores") or []
        if not ps:
            continue
        s1, s2 = m.get("side_one") or {}, m.get("side_two") or {}
        p1, p2 = s1.get("player") or {}, s2.get("player") or {}
        st1, st2 = s1.get("stats") or {}, s2.get("stats") or {}
        p1_id, p2_id = int(p1.get("id") or 0), int(p2.get("id") or 0)
        if not p1_id or not p2_id:
            continue
        r1 = float(st1.get("rating_before") or tracker.get_player_rating(p1_id))
        r2 = float(st2.get("rating_before") or tracker.get_player_rating(p2_id))
        sc1, sc2 = int(res.get("score_one") or 0), int(res.get("score_two") or 0)
        score_str = f"{sc1}-{sc2}"
        set_tuples = [(int(x[0]), int(x[1])) for x in ps if len(x) >= 2]
        p1_name = f"{p1.get('first_name_en', '')} {p1.get('surname_en', '')}".strip()
        p2_name = f"{p2.get('first_name_en', '')} {p2.get('surname_en', '')}".strip()
        tracker.update_match_outcome(
            m_id, p1_id, p2_id, r1, r2, score_str, set_tuples, p1_name, p2_name, m.get("start_date", "")
        )
        if idx % 25 == 0:
            print(f"[SYNC] Progreso PIT: {idx}/{len(new_finished_ids)} partidos...", flush=True)
            portfolio.save_full_state(tracker)

    portfolio.save_full_state(tracker)
    print(f"[SYNC] Base PIT al día ({len(tracker.processed_match_ids)} partidos en memoria).", flush=True)


def settle_pending_bets_and_update_pit(tracker: CausalPITTracker, portfolio: InstitutionalPortfolio):
    if not portfolio.active_bets:
        return
    print(f"[SETTLE] Verificando {len(portfolio.active_bets)} apuestas pendientes de liquidación...", flush=True)
    for bet in list(portfolio.active_bets):
        m_id = int(bet["match_id"])
        page = api_get_json(f"https://api.league-pro.com/pages/matches/{m_id}", 0.3, 0.5)
        if not page or "match" not in page:
            continue
        m = page["match"]
        if m.get("status") != 3:
            continue
        res = m.get("results") or {}
        ps = res.get("period_scores") or []
        if not ps:
            continue
        tot_pts = sum(int(x[0]) + int(x[1]) for x in ps if len(x) >= 2)
        sets_str = ", ".join(f"{int(x[0])}-{int(x[1])}" for x in ps if len(x) >= 2)
        sc1, sc2 = int(res.get("score_one") or 0), int(res.get("score_two") or 0)

        is_win = (
            (tot_pts > bet["target_line"])
            if "Más de" in bet["selection"]
            else (tot_pts < bet["target_line"])
        )
        pnl = round(bet["stake_usd"] * (bet["odds"] - 1.0), 2) if is_win else -bet["stake_usd"]
        portfolio.balance = round(portfolio.balance + pnl, 2)
        if portfolio.balance > portfolio.peak_balance:
            portfolio.peak_balance = portfolio.balance
        dd = (portfolio.peak_balance - portfolio.balance) / portfolio.peak_balance
        if dd > portfolio.max_drawdown:
            portfolio.max_drawdown = dd

        bet["final_sets_score"] = f"{sc1}-{sc2} ({sets_str})"
        bet["actual_points"] = tot_pts
        bet["result"] = "GANADA" if is_win else "PERDIDA"
        bet["pnl_usd"] = pnl
        bet["balance_after"] = portfolio.balance
        bet["status"] = "SETTLED"
        portfolio.settled_bets.append(bet)
        portfolio.active_bets.remove(bet)

        # Enviar notificación de liquidación oficial a Telegram
        icon = "✅ GANADA" if is_win else "❌ PERDIDA"
        sign_str = f"+${pnl:.2f}" if pnl >= 0 else f"-${abs(pnl):.2f}"
        settle_msg = (
            f"🏁 LIQUIDACIÓN OFICIAL — {icon}\n"
            f"🆔 Match ID: #{m_id} | ⏰ Inicio: {format_match_times(bet.get('match_start_utc', ''))}\n"
            f"🏓 PARTIDO: {bet['players']}\n"
            f"🏆 TORNEO: {bet.get('tournament_stage', 'Czech Liga Pro')}\n"
            f"🎯 PICK: {bet['selection']} (@{bet['odds']:.2f})\n"
            f"🔢 MARCADOR FINAL: {sc1}-{sc2} en sets [{sets_str}] = {tot_pts} Puntos\n"
            f"💵 P&L: {sign_str} USD | 💰 NUEVA BANCA: ${portfolio.balance:.2f} USD"
        )
        send_live_alert(f"🏁 {icon}: {bet['players']} ({tot_pts} pts)", settle_msg)

        s1, s2 = m.get("side_one") or {}, m.get("side_two") or {}
        p1, p2 = s1.get("player") or {}, s2.get("player") or {}
        st1, st2 = s1.get("stats") or {}, s2.get("stats") or {}
        p1_id, p2_id = int(p1.get("id") or 0), int(p2.get("id") or 0)
        r1 = float(st1.get("rating_before") or tracker.get_player_rating(p1_id))
        r2 = float(st2.get("rating_before") or tracker.get_player_rating(p2_id))
        set_tuples = [(int(x[0]), int(x[1])) for x in ps if len(x) >= 2]
        tracker.update_match_outcome(
            m_id, p1_id, p2_id, r1, r2, f"{sc1}-{sc2}", set_tuples, "", "", m.get("start_date", "")
        )

    portfolio.update_institutional_files()
    portfolio.save_full_state(tracker)


def is_set_completed(p1_pts: int, p2_pts: int) -> bool:
    return max(p1_pts, p2_pts) >= 11 and abs(p1_pts - p2_pts) >= 2


def run_live_sniper_shift(max_minutes: int = 195):
    # Reloj global iniciado ANTES de sincronizar para garantizar cierre limpio antes de los 230 min de GitHub
    t_shift_start = time.time()

    tracker = CausalPITTracker()
    portfolio = InstitutionalPortfolio(initial_bankroll=CONFIG["execution"]["initial_bankroll_usd"])
    engine = UniversalPhysicsEngine()

    if not portfolio.load_full_state(tracker):
        print("[INIT] Cargando bóveda semilla PIT_PLAYER_RATINGS_AND_RESISTANCE y PIT_H2H_MATRIX...", flush=True)
        tracker.load_seed_vault_if_needed()
    else:
        print(f"[INIT] Estado previo cargado con éxito. Banca actual: ${portfolio.balance:.2f} USD", flush=True)

    sync_historical_gap(tracker, portfolio)
    settle_pending_bets_and_update_pit(tracker, portfolio)
    portfolio.update_institutional_files()

    last_settlement_check = time.time()
    scan_cycle = 0

    print(f"[SNIPER] Vigilancia en vivo activa | Banca: ${portfolio.balance:.2f} USD", flush=True)

    while (time.time() - t_shift_start) < (max_minutes * 60):
        scan_cycle += 1
        now_utc = datetime.now(timezone.utc)
        w_from = (now_utc - timedelta(minutes=45)).strftime("%Y-%m-%dT%H:%M:%SZ")
        w_to = (now_utc + timedelta(minutes=10)).strftime("%Y-%m-%dT%H:%M:%SZ")
        url_active = (
            "https://api.league-pro.com/matches?sport_id=2&limit=100"
            f"&date_from={w_from}&date_to={w_to}&order_field=start_game&order_type=asc"
        )
        listing = api_get_json(url_active, min_delay=0.35, max_delay=0.65)
        items = (listing or {}).get("items") or []
        live_matches = [m for m in items if m.get("status") == 2]

        if scan_cycle % 4 == 1:
            elapsed_m = (time.time() - t_shift_start) / 60.0
            print(
                f"[SCAN #{scan_cycle} | {now_utc.strftime('%H:%M:%S')} UTC | {elapsed_m:.1f}/{max_minutes}m] "
                f"Mesas en vivo (status=2): {len(live_matches)} | Apuestas activas: {len(portfolio.active_bets)}",
                flush=True,
            )

        for m_summary in live_matches:
            m_id = int(m_summary.get("id") or 0)
            if not m_id:
                continue
            if m_id in tracker.evaluated_set1_ids and m_id in tracker.evaluated_set2_ids:
                continue

            page = api_get_json(f"https://api.league-pro.com/pages/matches/{m_id}", 0.35, 0.65)
            if not page or "match" not in page:
                continue
            m = page["match"]
            res = m.get("results") or {}
            ps = res.get("period_scores") or []
            if not ps:
                continue

            s1, s2 = m.get("side_one") or {}, m.get("side_two") or {}
            p1, p2 = s1.get("player") or {}, s2.get("player") or {}
            st1, st2 = s1.get("stats") or {}, s2.get("stats") or {}
            tour = m.get("tournament") or {}
            stage = m.get("stage") or {}
            tour_stage_str = f"{tour.get('name_en', '')} ({stage.get('name_en', 'Match')})".strip()
            match_start_utc = m.get("start_date") or ""

            p1_id, p2_id = int(p1.get("id") or 0), int(p2.get("id") or 0)
            p1_name = f"{p1.get('first_name_en', '')} {p1.get('surname_en', '')}".strip()
            p2_name = f"{p2.get('first_name_en', '')} {p2.get('surname_en', '')}".strip()
            r1 = float(st1.get("rating_before") or tracker.get_player_rating(p1_id))
            r2 = float(st2.get("rating_before") or tracker.get_player_rating(p2_id))

            # --- EVALUACIÓN FIN DEL SET 1 (MOTOR 2A F11.1) ---
            if m_id not in tracker.evaluated_set1_ids and len(ps) >= 1:
                p1_s1, p2_s1 = int(ps[0][0]), int(ps[0][1])
                s2_pts = (int(ps[1][0]) + int(ps[1][1])) if len(ps) >= 2 else 0
                if is_set_completed(p1_s1, p2_s1) and s2_pts <= 4:
                    tracker.evaluated_set1_ids.add(m_id)
                    sig = engine.evaluate_live_set1(
                        p1_id, p2_id, r1, r2, p1_s1, p2_s1, tracker, portfolio.balance
                    )
                    print(
                        f"  -> [EVAL SET 1] #{m_id} {p1_name} vs {p2_name} ({p1_s1}-{p2_s1}): "
                        f"{sig.get('action')} ({sig.get('reason', 'OK')})",
                        flush=True,
                    )
                    if sig.get("action") == "BET":
                        bet_rec = {
                            "match_id": m_id,
                            "match_start_utc": match_start_utc,
                            "tournament_stage": tour_stage_str,
                            "timestamp_utc": now_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
                            "players": f"{p1_name} vs {p2_name}",
                            "motor": sig["motor"],
                            "state_desc": sig["state_desc"],
                            "selection": sig["selection"],
                            "target_line": sig["target_line"],
                            "odds": sig["screen_odds"],
                            "stake_usd": sig["stake_usd"],
                            "status": "PENDING",
                        }
                        portfolio.active_bets.append(bet_rec)
                        portfolio.save_full_state(tracker)
                        alert_txt = (
                            f"🚨 ALERTA ORACLE LIVE — {sig['motor']}\n"
                            f"🆔 Match ID: #{m_id} | ⏰ Inicio: {format_match_times(match_start_utc)}\n"
                            f"🏆 TORNEO: {tour_stage_str}\n"
                            f"🏓 PARTIDO: {p1_name} (Local) vs {p2_name} (Visita)\n"
                            f"📊 ESTADO: {sig['state_desc']} | Ratings: {r1:.0f} vs {r2:.0f}\n"
                            f"🎯 SELECCIÓN EXACTA: {sig['selection']} (Cuota @{sig['screen_odds']:.2f})\n"
                            f"💰 STAKE KELLY: ${sig['stake_usd']:.2f} USD ({sig['recommended_stake_pct']*100:.2f}% de ${portfolio.balance:.2f})\n"
                            f"🔬 P_STRUCTURAL: {sig['p_structural']:.4f} | EV: +{sig['expected_value']*100:.2f}%"
                        )
                        send_live_alert(
                            f"🎯 PICK LIVE #{m_id}: {p1_name} vs {p2_name} ({sig['selection']})",
                            alert_txt,
                        )

            # --- EVALUACIÓN FIN DEL SET 2 (MOTOR 1B F11.1) ---
            if m_id not in tracker.evaluated_set2_ids and len(ps) >= 2:
                p1_s1, p2_s1 = int(ps[0][0]), int(ps[0][1])
                p1_s2, p2_s2 = int(ps[1][0]), int(ps[1][1])
                s3_pts = (int(ps[2][0]) + int(ps[2][1])) if len(ps) >= 3 else 0
                if is_set_completed(p1_s1, p2_s1) and is_set_completed(p1_s2, p2_s2) and s3_pts <= 4:
                    tracker.evaluated_set2_ids.add(m_id)
                    sig = engine.evaluate_live_set2(
                        p1_id, p2_id, r1, r2, p1_s1, p2_s1, p1_s2, p2_s2, tracker, portfolio.balance
                    )
                    print(
                        f"  -> [EVAL SET 2] #{m_id} {p1_name} vs {p2_name} ({p1_s1}-{p2_s1}, {p1_s2}-{p2_s2}): "
                        f"{sig.get('action')} ({sig.get('reason', 'OK')})",
                        flush=True,
                    )
                    if sig.get("action") == "BET":
                        bet_rec = {
                            "match_id": m_id,
                            "match_start_utc": match_start_utc,
                            "tournament_stage": tour_stage_str,
                            "timestamp_utc": now_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
                            "players": f"{p1_name} vs {p2_name}",
                            "motor": sig["motor"],
                            "state_desc": sig["state_desc"],
                            "selection": sig["selection"],
                            "target_line": sig["target_line"],
                            "odds": sig["screen_odds"],
                            "stake_usd": sig["stake_usd"],
                            "status": "PENDING",
                        }
                        portfolio.active_bets.append(bet_rec)
                        portfolio.save_full_state(tracker)
                        alert_txt = (
                            f"🚨 ALERTA ORACLE LIVE — {sig['motor']}\n"
                            f"🆔 Match ID: #{m_id} | ⏰ Inicio: {format_match_times(match_start_utc)}\n"
                            f"🏆 TORNEO: {tour_stage_str}\n"
                            f"🏓 PARTIDO: {p1_name} (Local) vs {p2_name} (Visita)\n"
                            f"📊 ESTADO: {sig['state_desc']} | Ratings: {r1:.0f} vs {r2:.0f}\n"
                            f"🎯 SELECCIÓN EXACTA: {sig['selection']} (Cuota @{sig['screen_odds']:.2f})\n"
                            f"💰 STAKE KELLY: ${sig['stake_usd']:.2f} USD ({sig['recommended_stake_pct']*100:.2f}% de ${portfolio.balance:.2f})\n"
                            f"🔬 P_STRUCTURAL: {sig['p_structural']:.4f} | EV: +{sig['expected_value']*100:.2f}%"
                        )
                        send_live_alert(
                            f"🎯 PICK LIVE #{m_id}: {p1_name} vs {p2_name} ({sig['selection']})",
                            alert_txt,
                        )

        if (time.time() - last_settlement_check) >= 600:
            settle_pending_bets_and_update_pit(tracker, portfolio)
            sync_historical_gap(tracker, portfolio)
            last_settlement_check = time.time()

        time.sleep(15)

    settle_pending_bets_and_update_pit(tracker, portfolio)
    sync_historical_gap(tracker, portfolio)
    portfolio.update_institutional_files()
    print(f"[SHIFT END] Turno cerrado limpiamente. Balance actual: ${portfolio.balance:.2f} USD", flush=True)


if __name__ == "__main__":
    run_live_sniper_shift(max_minutes=195)
