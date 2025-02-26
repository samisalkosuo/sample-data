import time
import random
from datetime import datetime, timedelta

def random_unix_timestamp_in_last_days(days=730):
    """
    Return a random Unix epoch timestamp (in seconds) within the last two years.
    """
    # Current timestamp
    now_ts = int(time.time())
        
    two_years_ago_dt = datetime.now() - timedelta(days=days)
    two_years_ago_ts = int(two_years_ago_dt.timestamp())
    
    # Generate a random timestamp between two_years_ago_ts and now_ts
    return random.randint(two_years_ago_ts, now_ts)


def random_choice_distribution(
    items,
    distribution="uniform",
    **dist_params
):
    """
    Return one item from 'items' based on the specified distribution.

    :param items: list of strings (or any items).
    :param distribution: str, one of ["uniform", "gaussian", "lognormal", "pareto"].
    :param dist_params: additional parameters for the chosen distribution.
        - For "gaussian", provide mean (float) and stdev (float).
          e.g., mean=5, stdev=2
        - For "lognormal", provide mu (float) and sigma (float).
          e.g., mu=0, sigma=1
        - For "pareto", provide alpha (float).
          e.g., alpha=1
    :return: A single randomly chosen item from the list.
    """
    n = len(items)
    if n == 0:
        raise ValueError("Items list cannot be empty.")

    # Uniform distribution: each item is equally likely
    if distribution == "uniform":
        return random.choice(items)

    # Otherwise, generate an index using the requested distribution
    idx = None
    
    # GAUSSIAN (normal) distribution
    if distribution == "gaussian":
        mean = dist_params.get("mean", n / 2.0)  # default center in the middle
        stdev = dist_params.get("stdev", n / 6.0)  # default spread
        # Generate until we get an in-range index
        while True:
            candidate = int(random.gauss(mean, stdev))
            if 0 <= candidate < n:
                idx = candidate
                break

    # LOGNORMAL distribution
    elif distribution == "lognormal":
        mu = dist_params.get("mu", 0.0)      # location
        sigma = dist_params.get("sigma", 1.0)  # scale
        while True:
            candidate = int(random.lognormvariate(mu, sigma))
            if 0 <= candidate < n:
                idx = candidate
                break

    # PARETO distribution
    elif distribution == "pareto":
        alpha = dist_params.get("alpha", 1.0)
        while True:
            candidate = int(random.paretovariate(alpha))
            if 0 <= candidate < n:
                idx = candidate
                break

    if idx is not None:
        return items[idx]
    else:
        # Fallback (should not happen in normal scenarios)
        raise ValueError("Failed to produce an index within the valid range.")
