"""Groq client with automatic API key rotation.

When one key hits rate limits (429), automatically switches to the next key.
Add keys in .env as GROQ_API_KEY, GROQ_API_KEY_2, GROQ_API_KEY_3, etc.
"""

import os
import time
from groq import Groq
from dotenv import load_dotenv

load_dotenv(override=True)

MODEL = "qwen/qwen3.8-27b"


class GroqRotatingClient:
    def __init__(self):
        self.keys = self._load_keys()
        self.current_idx = 0
        self.clients = [Groq(api_key=k) for k in self.keys]
        self.exhausted = set()  # Track which keys are daily-exhausted
        print(f"    Loaded {len(self.keys)} Groq API key(s)")

    def _load_keys(self):
        keys = []
        primary = os.getenv("GROQ_API_KEY", "").strip()
        if primary:
            keys.append(primary)
        for i in range(2, 20):
            key = os.getenv(f"GROQ_API_KEY_{i}", "").strip()
            if key:
                keys.append(key)
        if not keys:
            raise ValueError("No GROQ_API_KEY found in .env")
        return keys

    @property
    def client(self):
        return self.clients[self.current_idx]

    def _rotate(self):
        old = self.current_idx + 1
        self.exhausted.add(self.current_idx)

        # Find next non-exhausted key
        for _ in range(len(self.keys)):
            self.current_idx = (self.current_idx + 1) % len(self.keys)
            if self.current_idx not in self.exhausted:
                print(f"\n    Key {old} rate-limited → switching to key {self.current_idx + 1}/{len(self.keys)}")
                return True

        # All keys exhausted
        return False

    def chat(self, messages, max_tokens=1024, stream=False):
        """Make a chat completion with automatic key rotation on 429 errors."""
        max_retries = 3

        for retry in range(max_retries):
            try:
                return self.client.chat.completions.create(
                    model=MODEL,
                    messages=messages,
                    max_tokens=max_tokens,
                    stream=stream,
                )
            except Exception as e:
                error_str = str(e)
                if "429" not in error_str and "rate_limit" not in error_str.lower():
                    raise  # Non-rate-limit error, don't retry

                # Try rotating to another key
                if self._rotate():
                    time.sleep(1)
                    continue

                # All keys exhausted — wait for reset
                wait = 120 * (retry + 1)
                print(f"\n    All {len(self.keys)} keys rate-limited. Waiting {wait}s for reset...")
                time.sleep(wait)
                self.exhausted.clear()  # Reset exhausted set after waiting
                self.current_idx = 0

        # Final attempt after all waits
        return self.client.chat.completions.create(
            model=MODEL,
            messages=messages,
            max_tokens=max_tokens,
            stream=stream,
        )


# Singleton instance
_client = None


def get_client():
    global _client
    if _client is None:
        _client = GroqRotatingClient()
    return _client
