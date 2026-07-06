"""Rate limiting utilities for Gemini API calls"""

import time
import asyncio
from collections import deque
from datetime import datetime

class RateLimiter:
    """Token bucket rate limiter for Gemini API"""
    
    def __init__(self, rpm_limit: int = 10, rpd_limit: int = 20, tpm_limit: int = 250000):
        """
        Args:
            rpm_limit: Requests per minute (10 for free tier)
            rpd_limit: Requests per day (20 for free tier)
            tpm_limit: Tokens per minute (250k for free tier)
        """
        self.rpm_limit = rpm_limit
        self.rpd_limit = rpd_limit
        self.tpm_limit = tpm_limit
        
        # Track timestamps for RPM and RPD
        self.rpm_calls = deque()
        self.rpd_calls = deque()
        
        # Track tokens used (estimate)
        self.tokens_used_in_minute = 0
        self.token_window_start = time.time()
        
        self.lock = asyncio.Lock()
    
    async def acquire(self, estimated_tokens: int = 1000):
        """
        Wait if any rate limit would be exceeded
        
        Args:
            estimated_tokens: Estimated tokens for this request (default 1000)
        """
        async with self.lock:
            now = time.time()
            
            # Clean old RPM calls (> 60 seconds)
            while self.rpm_calls and now - self.rpm_calls[0] > 60:
                self.rpm_calls.popleft()
            
            # Clean old RPD calls (> 86400 seconds = 24 hours)
            while self.rpd_calls and now - self.rpd_calls[0] > 86400:
                self.rpd_calls.popleft()
            
            # Check RPD limit (20 per day)
            if len(self.rpd_calls) >= self.rpd_limit:
                oldest = min(self.rpd_calls)
                wait_time = 86400 - (now - oldest) + 1
                print(f"⏳ RPD limit (20/day) reached. Waiting {wait_time/3600:.1f} hours...")
                await asyncio.sleep(wait_time)
                # Recheck after waiting
                now = time.time()
                while self.rpd_calls and now - self.rpd_calls[0] > 86400:
                    self.rpd_calls.popleft()
            
            # Check RPM limit (10 per minute)
            if len(self.rpm_calls) >= self.rpm_limit:
                oldest = min(self.rpm_calls)
                wait_time = 60 - (now - oldest) + 0.5
                print(f"⏳ RPM limit (10/min) reached. Waiting {wait_time:.1f}s...")
                await asyncio.sleep(wait_time)
                # Recheck after waiting
                now = time.time()
                while self.rpm_calls and now - self.rpm_calls[0] > 60:
                    self.rpm_calls.popleft()
            
            # Check TPM limit (250k tokens per minute)
            # Reset token counter if window expired
            if now - self.token_window_start > 60:
                self.token_window_start = now
                self.tokens_used_in_minute = 0
            
            if self.tokens_used_in_minute + estimated_tokens > self.tpm_limit:
                wait_time = 60 - (now - self.token_window_start) + 1
                print(f"⏳ TPM limit (250k tokens) reached. Waiting {wait_time:.1f}s...")
                await asyncio.sleep(wait_time)
                # Reset after waiting
                self.token_window_start = time.time()
                self.tokens_used_in_minute = 0
            
            # Record the call
            self.rpm_calls.append(now)
            self.rpd_calls.append(now)
            self.tokens_used_in_minute += estimated_tokens

# Create global rate limiter
gemini_limiter = RateLimiter(
    rpm_limit=10,      # 10 requests per minute
    rpd_limit=20,      # 20 requests per day
    tpm_limit=250000   # 250k tokens per minute
)