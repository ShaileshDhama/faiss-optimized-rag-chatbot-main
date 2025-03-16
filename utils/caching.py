import functools

cache = {}

def cache_result(func):
    """Decorator to cache FAISS retrieval results."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        cache_key = str(args) + str(kwargs)
        if cache_key in cache:
            return cache[cache_key]
        result = func(*args, **kwargs)
        cache[cache_key] = result
        return result
    return wrapper

if __name__ == "__main__":
    @cache_result
    def slow_function(x):
        return x ** 2

    print(slow_function(5))  # First call (computes)
    print(slow_function(5))  # Second call (cached)

# Store in cache
def cache_response(query, response):
    cache = load_cache()
    cache[query] = response
    save_cache(cache)
