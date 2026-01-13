import asyncio
import random
import time

class Scheduler:
    def __init__(self, uids, interval=300, min_delay=1.0, jitter=1.0):
        """
        Args:
            uids (list): List of UIDs to track.
            interval (int): Target loop interval in seconds (default 300s / 5m).
            min_delay (float): Minimum delay between requests in seconds to protect API.
            jitter (float): Max random deviation in seconds added/subtracted from delay.
        """
        self.uids = uids
        self.interval = interval
        self.min_delay = min_delay
        self.jitter = jitter
        self._index = 0
        self._first_run = True
        
    async def next_uid(self):
        """
        Waits for the calculated delay and returns the next UID to poll.
        """
        if not self.uids:
            await asyncio.sleep(self.interval)
            return None

        count = len(self.uids)
        if self._first_run:
            target_delay = self.min_delay
        else:
            target_delay = max(self.interval / max(count, 1), self.min_delay)
        
        noise = random.uniform(-self.jitter, self.jitter)
        sleep_time = max(0.1, target_delay + noise)
        
        await asyncio.sleep(sleep_time)
        
        uid = self.uids[self._index]
        self._index = (self._index + 1) % count
        
        if self._index == 0:
            self._first_run = False
        
        return uid

class GlobalRateLimiter:
    """
    Enforces a strict minimum delay between requests across multiple concurrent tasks.
    Supports progressive backoff on rate limit errors.
    """
    def __init__(self, min_delay=1.0):
        self.min_delay = min_delay
        self.current_min_delay = min_delay
        self.last_req_time = 0
        self._lock = asyncio.Lock()
        
        self.backoff_until = 0
        self.consecutive_errors = 0

    async def wait(self):
        """
        Blocks until enough time has passed since the last granted request.
        Respects active backoff timers.
        """
        async with self._lock:
            now = time.time()
            
            if now < self.backoff_until:
                wait_time = self.backoff_until - now
                print(f"[RateLimiter] 🛑 Backoff active. Pausing for {wait_time:.1f}s...")
                await asyncio.sleep(wait_time)
                now = time.time()

            elapsed = now - self.last_req_time
            delay_needed = self.current_min_delay
            
            if elapsed < delay_needed:
                wait_time = delay_needed - elapsed
                await asyncio.sleep(wait_time)
            
            self.last_req_time = time.time()

    def trigger_backoff(self):
        """Called when a 412/429 error is detected."""
        self.consecutive_errors += 1
        
        penalty = 60 * self.consecutive_errors
        self.backoff_until = time.time() + penalty
        
        if self.consecutive_errors > 1:
            self.current_min_delay = min(self.current_min_delay + 2.0, 30.0)
            
        print(f"[RateLimiter] ⚠️ RATE LIMIT HIT! Pausing {penalty}s. New min_delay={self.current_min_delay}s")

    def report_success(self):
        """Resets consecutive error count on success."""
        if self.consecutive_errors > 0:
            self.consecutive_errors = 0
            print("[RateLimiter] ✅ API call successful. Error count reset.")
