import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

DB_PATH = "db.json"

_EMPTY_DB = {
    "inputs": [],
    "posts": [],
    "event_config": {},
    "oauth": None,
    "oauth_state": None,
}


def load_db() -> Dict[str, Any]:
    if not os.path.exists(DB_PATH):
        return dict(_EMPTY_DB)
    with open(DB_PATH, "r", encoding="utf-8") as f:
        db = json.load(f)
    # backfill keys for dbs created before oauth support existed
    for key, default in _EMPTY_DB.items():
        db.setdefault(key, default)
    return db


def save_db(data: Dict[str, Any]) -> None:
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ---------- Inputs ----------

def add_input(input_data: Dict[str, Any]) -> Dict[str, Any]:
    db = load_db()
    input_data["id"] = f"inp_{len(db['inputs']) + 1}"
    input_data["created_at"] = datetime.utcnow().isoformat()
    input_data["status"] = "pending"
    db["inputs"].append(input_data)
    save_db(db)
    return input_data


def get_input(input_id: str) -> Optional[Dict[str, Any]]:
    db = load_db()
    for inp in db["inputs"]:
        if inp["id"] == input_id:
            return inp
    return None


def update_input(input_id: str, updates: Dict[str, Any]) -> None:
    db = load_db()
    for inp in db["inputs"]:
        if inp["id"] == input_id:
            inp.update(updates)
            break
    save_db(db)


def get_pending_inputs() -> List[Dict[str, Any]]:
    db = load_db()
    return [inp for inp in db["inputs"] if inp.get("status") == "pending"]


# ---------- Posts ----------

def add_post(post_data: Dict[str, Any]) -> Dict[str, Any]:
    db = load_db()
    post_data["id"] = f"post_{len(db['posts']) + 1}"
    post_data["created_at"] = datetime.utcnow().isoformat()
    db["posts"].append(post_data)
    save_db(db)
    return post_data


def get_all_posts() -> List[Dict[str, Any]]:
    db = load_db()
    return db["posts"]


# ---------- Event config ----------

def set_event_config(config: Dict[str, Any]) -> None:
    db = load_db()
    db["event_config"] = config
    save_db(db)


def get_event_config() -> Dict[str, Any]:
    db = load_db()
    return db.get("event_config", {})


# ---------- OAuth ----------

def set_oauth_state(state: str) -> None:
    db = load_db()
    db["oauth_state"] = state
    save_db(db)


def get_oauth_state() -> Optional[str]:
    db = load_db()
    return db.get("oauth_state")


def store_tokens(access_token: str, person_urn: str) -> None:
    db = load_db()
    db["oauth"] = {"access_token": access_token, "person_urn": person_urn}
    save_db(db)


def get_stored_tokens() -> Optional[Dict[str, Any]]:
    db = load_db()
    return db.get("oauth")
