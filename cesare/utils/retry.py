import time
import random
from typing import Callable, Any
from functools import wraps
import logging

logger = logging.getLogger(__name__)


class RetryConfig:
    """Configuration for retry behavior."""
    
    def __init__(
        self,
        max_retries: int = 15,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        rate_limit_delay: float = 2.0,
    ):
        """
        Initialize retry configuration.
        
        Args:
            max_retries: Maximum number of retry attempts
            base_delay: Initial delay in seconds
            max_delay: Maximum delay in seconds
            exponential_base: Base for exponential backoff
            jitter: Whether to add random jitter to delays
            rate_limit_delay: Additional delay between requests when rate limited
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.rate_limit_delay = rate_limit_delay


def is_retryable_error(error: Exception) -> bool:
    """
    Check if an error is retryable.
    
    Args:
        error: The exception to check
        
    Returns:
        bool: True if the error should be retried
    """
    error_str = str(error).lower()
    
    # Rate limit errors (429)
    if "429" in error_str or "rate limit" in error_str:
        return True
    
    # Server errors (5xx)
    if any(code in error_str for code in ["500", "502", "503", "504"]):
        return True
    
    # Connection errors
    if any(term in error_str for term in ["connection", "timeout", "network"]):
        return True
    
    # OpenAI specific errors
    if any(term in error_str for term in ["overloaded", "server_error"]):
        return True
    
    return False


def is_rate_limit_error(error: Exception) -> bool:
    """
    Check if an error is specifically a rate limit error.
    
    Args:
        error: The exception to check
        
    Returns:
        bool: True if this is a rate limit error
    """
    error_str = str(error).lower()
    return "429" in error_str or "rate limit" in error_str


def calculate_delay(attempt: int, config: RetryConfig) -> float:
    """
    Calculate delay for exponential backoff.
    
    Args:
        attempt: Current attempt number (0-based)
        config: Retry configuration
        
    Returns:
        float: Delay in seconds
    """
    delay = config.base_delay * (config.exponential_base ** attempt)
    delay = min(delay, config.max_delay)
    
    if config.jitter:
        # Add random jitter (±25%)
        jitter_range = delay * 0.25
        delay += random.uniform(-jitter_range, jitter_range)
    
    return max(0, delay)


def retry_with_backoff(config: RetryConfig = None):
    """
    Decorator for retrying functions with exponential backoff.
    
    Args:
        config: Retry configuration. If None, uses default config.
        
    Returns:
        Decorated function
    """
    if config is None:
        config = RetryConfig()
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            rate_limited = False
            
            for attempt in range(config.max_retries + 1):
                try:
                    # Add delay between requests if we were rate limited
                    if rate_limited and attempt > 0:
                        logger.info(f"Adding rate limit delay: {config.rate_limit_delay}s")
                        time.sleep(config.rate_limit_delay)
                    
                    result = func(*args, **kwargs)
                    
                    # Success - reset rate limit flag for future calls
                    if attempt > 0:
                        logger.info(f"Retry successful after {attempt} attempts")
                    
                    return result
                    
                except Exception as e:
                    last_exception = e
                    
                    if not is_retryable_error(e):
                        logger.error(f"Non-retryable error in {func.__name__}: {e}")
                        raise e
                    
                    if attempt == config.max_retries:
                        logger.error(f"Max retries ({config.max_retries}) exceeded for {func.__name__}")
                        raise e
                    
                    # Check if this is a rate limit error
                    if is_rate_limit_error(e):
                        rate_limited = True
                        logger.warning(f"Rate limit error in {func.__name__}, attempt {attempt + 1}")
                    else:
                        logger.warning(f"Retryable error in {func.__name__}, attempt {attempt + 1}: {e}")
                    
                    # Calculate and apply delay
                    delay = calculate_delay(attempt, config)
                    logger.info(f"Retrying in {delay:.2f} seconds...")
                    time.sleep(delay)
            
            # This should never be reached, but just in case
            raise last_exception
        
        return wrapper
    return decorator


class SimulationRetryManager:
    """
    Manager for handling retries during simulation runs.
    Tracks rate limiting state across multiple API calls.
    """
    
    def __init__(self, config: RetryConfig = None):
        """
        Initialize the retry manager.
        
        Args:
            config: Retry configuration
        """
        self.config = config or RetryConfig()
        self.rate_limited = False
        self.last_rate_limit_time = 0
    
    def execute_with_retry(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute a function with retry logic and simulation-wide rate limit tracking.
        
        Args:
            func: Function to execute
            *args: Arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            Result of the function call
        """
        last_exception = None
        
        for attempt in range(self.config.max_retries + 1):
            try:
                # Add delay if we're in a rate-limited state
                if self.rate_limited:
                    current_time = time.time()
                    time_since_rate_limit = current_time - self.last_rate_limit_time
                    
                    # If it's been a while since the last rate limit, reset the flag
                    if time_since_rate_limit > 60:  # Reset after 1 minute
                        self.rate_limited = False
                    else:
                        logger.info(f"Simulation rate limited - adding delay: {self.config.rate_limit_delay}s")
                        time.sleep(self.config.rate_limit_delay)
                
                result = func(*args, **kwargs)
                
                # Success - log if this was a retry
                if attempt > 0:
                    logger.info(f"Retry successful after {attempt} attempts")
                
                return result
                
            except Exception as e:
                last_exception = e
                
                if not is_retryable_error(e):
                    logger.error(f"Non-retryable error: {e}")
                    raise e
                
                if attempt == self.config.max_retries:
                    logger.error(f"Max retries ({self.config.max_retries}) exceeded")
                    raise e
                
                # Handle rate limiting
                if is_rate_limit_error(e):
                    self.rate_limited = True
                    self.last_rate_limit_time = time.time()
                    logger.warning("Rate limit detected - will add delays to future requests")
                
                logger.warning(f"Retryable error, attempt {attempt + 1}: {e}")
                
                # Calculate and apply delay
                delay = calculate_delay(attempt, self.config)
                logger.info(f"Retrying in {delay:.2f} seconds...")
                time.sleep(delay)
        
        # This should never be reached
        raise last_exception 