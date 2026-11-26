from downloads.utils import (
    get_duration_bucket,
    get_file_size_bucket,
    get_row_count_bucket,
)
from test_utils.base import BaseSimpleTestCase


class GetDurationBucketTests(BaseSimpleTestCase):
    def test_duration_buckets(self):
        test_cases = [
            (0, "0-5s"),
            (4.99, "0-5s"),
            (5, "5-10s"),
            (9.99, "5-10s"),
            (10, "10-30s"),
            (29.99, "10-30s"),
            (30, "30-60s"),
            (59.99, "30-60s"),
            (60, "60s+"),
            (120, "60s+"),
        ]

        for seconds, expected in test_cases:
            with self.subTest(seconds=seconds):
                self.assertEqual(get_duration_bucket(seconds), expected)


class GetRowCountBucketTests(BaseSimpleTestCase):
    def test_row_count_buckets(self):
        test_cases = [
            (0, "0-100"),
            (99, "0-100"),
            (100, "100-1k"),
            (999, "100-1k"),
            (1_000, "1k-10k"),
            (9_999, "1k-10k"),
            (10_000, "10k-100k"),
            (99_999, "10k-100k"),
            (100_000, "100k+"),
            (1_000_000, "100k+"),
        ]

        for count, expected in test_cases:
            with self.subTest(count=count):
                self.assertEqual(get_row_count_bucket(count), expected)


class GetFileSizeBucketTests(BaseSimpleTestCase):
    def test_file_size_buckets(self):
        mb = 1024 * 1024

        test_cases = [
            (0, "0-1MB"),
            (mb - 1, "0-1MB"),
            (mb, "1-10MB"),
            (10 * mb - 1, "1-10MB"),
            (10 * mb, "10-50MB"),
            (50 * mb - 1, "10-50MB"),
            (50 * mb, "50-100MB"),
            (100 * mb - 1, "50-100MB"),
            (100 * mb, "100-250MB"),
            (250 * mb - 1, "100-250MB"),
            (250 * mb, "250-500MB"),
            (500 * mb - 1, "250-500MB"),
            (500 * mb, "500MB+"),
            (1_000 * mb, "500MB+"),
        ]

        for size, expected in test_cases:
            with self.subTest(size=size):
                self.assertEqual(get_file_size_bucket(size), expected)
