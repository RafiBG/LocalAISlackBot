from collections import deque
from threading import Lock

class ChatMemoryService:
    def __init__(self, max_history_size: int = 10):
        self.max_history_size = max_history_size
        # Dictionary to store user histories: {user_id: deque([messages])}
        self._user_histories = {}
        # Thread safety lock for concurrent access
        self._lock = Lock()

    def add_message(self, user_id: str, role: str, content: str):
        with self._lock:
            if user_id not in self._user_histories:
                self._user_histories[user_id] = deque(maxlen=self.max_history_size)
            
            self._user_histories[user_id].append({"role": role, "content": content})

    def get_history(self, user_id: str, system_message: str) -> list:
        with self._lock:
            history = list(self._user_histories.get(user_id, []))
            
            # Always prepend the system message for the LLM call
            full_history = [{"role": "system", "content": system_message}]
            full_history.extend(history)
            return full_history

    def clear_user_history(self, user_id: str):
        with self._lock:
            if user_id in self._user_histories:
                del self._user_histories[user_id]

    def reset_all(self):
        with self._lock:
            self._user_histories.clear()