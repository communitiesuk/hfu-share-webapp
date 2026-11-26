def get_duration_bucket(seconds: float) -> str:
    if seconds < 5:
        return "0-5s"
    if seconds < 10:
        return "5-10s"
    if seconds < 30:
        return "10-30s"
    if seconds < 60:
        return "30-60s"
    return "60s+"


def get_row_count_bucket(count: int) -> str:
    if count < 100:
        return "0-100"
    if count < 1_000:
        return "100-1k"
    if count < 10_000:
        return "1k-10k"
    if count < 100_000:
        return "10k-100k"
    return "100k+"


def get_file_size_bucket(size: int) -> str:
    mb = 1024 * 1024

    if size < mb:
        return "0-1MB"
    if size < 10 * mb:
        return "1-10MB"
    if size < 50 * mb:
        return "10-50MB"
    if size < 100 * mb:
        return "50-100MB"
    if size < 250 * mb:
        return "100-250MB"
    if size < 500 * mb:
        return "250-500MB"
    return "500MB+"
