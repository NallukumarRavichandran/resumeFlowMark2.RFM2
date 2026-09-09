import os
import json
from datetime import datetime

LOGS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
LOGS_FILE = os.path.join(LOGS_DIR, "account_history.json")

class AccountLogger:
    @staticmethod
    def _ensure_logs_file():
        os.makedirs(LOGS_DIR, exist_ok=True)
        if not os.path.exists(LOGS_FILE):
            with open(LOGS_FILE, "w", encoding="utf-8") as f:
                json.dump([], f)

    @classmethod
    def get_logs(cls):
        cls._ensure_logs_file()
        try:
            with open(LOGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    @classmethod
    def add_or_update_log(cls, entry_id, **kwargs):
        cls._ensure_logs_file()
        logs = cls.get_logs()
        found = False
        
        for item in logs:
            if item.get("id") == entry_id:
                item.update(kwargs)
                item["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                found = True
                break
                
        if not found:
            new_entry = {
                "id": entry_id,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                **kwargs
            }
            logs.insert(0, new_entry)
            
        with open(LOGS_FILE, "w", encoding="utf-8") as f:
            json.dump(logs, f, indent=2)
            
        return entry_id
