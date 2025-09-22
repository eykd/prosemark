"""Unit tests for UUIDv7 generation functionality."""

import time
from datetime import UTC, datetime

import pytest

from prosemark.adapters.id_generator_uuid7 import IdGeneratorUuid7


class TestUuid7Generation:
    """Test UUIDv7 generation functionality."""

    @pytest.fixture
    def generator(self) -> IdGeneratorUuid7:
        """Create a UUIDv7 generator instance."""
        return IdGeneratorUuid7()

    def test_generate_valid_uuid7_format(self, generator: IdGeneratorUuid7) -> None:
        """Test that generated UUIDs follow UUIDv7 format."""
        uuid_str = str(generator.new())

        # Should be 36 characters with hyphens in correct positions
        assert len(uuid_str) == 36
        assert uuid_str[8] == '-'
        assert uuid_str[13] == '-'
        assert uuid_str[18] == '-'
        assert uuid_str[23] == '-'

        # Should only contain valid hex characters and hyphens
        hex_chars = set('0123456789abcdef-')
        assert all(c in hex_chars for c in uuid_str.lower())

    def test_version_bits_are_correct(self, generator: IdGeneratorUuid7) -> None:
        """Test that generated UUIDs have correct version bits (7)."""
        uuid_str = str(generator.new())

        # Version is in the first 4 bits of the time_hi_and_version field
        # This is the first character of the third group
        version_char = uuid_str[14]  # Position after "xxxxxxxx-xxxx-"

        # Should be 7
        assert version_char == '7'

    def test_variant_bits_are_correct(self, generator: IdGeneratorUuid7) -> None:
        """Test that generated UUIDs have correct variant bits."""
        uuid_str = str(generator.new())

        # Variant bits are in the first 2 bits of clock_seq_hi_and_reserved
        # This is the first character of the fourth group
        variant_char = uuid_str[19]  # Position after "xxxxxxxx-xxxx-xxxx-"

        # Should be 8, 9, a, or b (binary 10xx)
        assert variant_char.lower() in '89ab'

    def test_timestamp_ordering(self, generator: IdGeneratorUuid7) -> None:
        """Test that UUIDs generated later have later timestamps."""
        uuid1 = str(generator.new())
        time.sleep(0.001)  # Small delay to ensure different timestamp
        uuid2 = str(generator.new())

        # Extract timestamp portions (first 12 hex chars, ignoring hyphens)
        ts1 = uuid1[:8] + uuid1[9:13]  # time_high + time_mid
        ts2 = uuid2[:8] + uuid2[9:13]

        # Later UUID should have later or equal timestamp
        # (equal is possible due to millisecond precision)
        assert ts1 <= ts2

    def test_uniqueness_in_batch(self, generator: IdGeneratorUuid7) -> None:
        """Test that multiple UUIDs generated quickly are unique."""
        batch_size = 1000
        uuids = [str(generator.new()) for _ in range(batch_size)]

        # All should be unique
        assert len(set(uuids)) == batch_size

    def test_temporal_locality(self, generator: IdGeneratorUuid7) -> None:
        """Test that UUIDs generated close in time have similar prefixes."""
        # Generate UUIDs in quick succession
        batch1 = [str(generator.new()) for _ in range(10)]

        # Small delay
        time.sleep(0.01)

        [str(generator.new()) for _ in range(10)]

        # UUIDs in the same batch should have very similar timestamp prefixes
        for i in range(1, len(batch1)):
            # First 8 characters (timestamp high) should often be identical
            prefix1 = batch1[0][:8]
            prefix_i = batch1[i][:8]
            # They should be very close (within a few values)
            assert abs(int(prefix1, 16) - int(prefix_i, 16)) < 1000

    def test_randomness_in_random_portion(self, generator: IdGeneratorUuid7) -> None:
        """Test that the random portion shows sufficient randomness."""
        uuids = [str(generator.new()) for _ in range(100)]

        # Extract random portions (last 12 characters)
        random_portions = [uuid[-12:].replace('-', '') for uuid in uuids]

        # Should have high uniqueness in random portion
        assert len(set(random_portions)) == len(random_portions)

        # Check that we're using the full range of hex characters
        all_chars = ''.join(random_portions)
        unique_chars = set(all_chars.lower())
        # Should see most hex digits (might not see all due to randomness)
        assert len(unique_chars) >= 12  # Most of 0-9, a-f

    def test_performance_characteristics(self, generator: IdGeneratorUuid7) -> None:
        """Test that generation is reasonably fast."""
        import time

        # Generate many UUIDs and measure time
        start_time = time.time()
        batch_size = 10000

        for _ in range(batch_size):
            str(generator.new())

        end_time = time.time()
        elapsed = end_time - start_time

        # Should be able to generate at least 1000 UUIDs per second
        rate = batch_size / elapsed
        assert rate > 1000, f'Generation rate too slow: {rate:.2f} UUIDs/sec'

    def test_thread_safety_simulation(self, generator: IdGeneratorUuid7) -> None:
        """Test behavior under simulated concurrent access."""
        import queue
        import threading

        result_queue: queue.Queue[list[str]] = queue.Queue()
        num_threads = 10
        uuids_per_thread = 100

        def generate_uuids() -> None:
            thread_uuids = [str(generator.new()) for _ in range(uuids_per_thread)]
            result_queue.put(thread_uuids)

        # Start threads
        threads = []
        for _ in range(num_threads):
            thread = threading.Thread(target=generate_uuids)
            threads.append(thread)
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # Collect all UUIDs
        all_uuids = []
        while not result_queue.empty():
            thread_uuids = result_queue.get()
            all_uuids.extend(thread_uuids)

        # All should be unique
        assert len(all_uuids) == num_threads * uuids_per_thread
        assert len(set(all_uuids)) == len(all_uuids)

    def test_timestamp_extraction_accuracy(self, generator: IdGeneratorUuid7) -> None:
        """Test that the timestamp portion reflects actual generation time."""
        # Record time before generation
        before = datetime.now(UTC)
        uuid_str = str(generator.new())
        after = datetime.now(UTC)

        # Extract timestamp from UUID
        # UUIDv7 timestamp is Unix timestamp in milliseconds
        timestamp_hex = uuid_str[:8] + uuid_str[9:13] + uuid_str[14:18][:3]
        # Remove version bits from time_hi_and_version
        timestamp_hex = timestamp_hex[:12] + '0' + timestamp_hex[13:]

        timestamp_ms = int(timestamp_hex[:12], 16)
        uuid_time = datetime.fromtimestamp(timestamp_ms / 1000, UTC)

        # UUID timestamp should be between before and after
        # Account for millisecond precision by truncating microseconds
        before_ms = before.replace(microsecond=(before.microsecond // 1000) * 1000)
        after_ms = after.replace(microsecond=(after.microsecond // 1000) * 1000)
        assert before_ms <= uuid_time <= after_ms

    def test_clock_sequence_randomness(self, generator: IdGeneratorUuid7) -> None:
        """Test clock sequence provides uniqueness for same-millisecond generation."""
        # Generate many UUIDs quickly to potentially hit same millisecond
        uuids = [str(generator.new()) for _ in range(100)]

        # Group by timestamp (first 15 hex chars)
        timestamp_groups: dict[str, list[str]] = {}
        for uuid_str in uuids:
            timestamp = uuid_str[:8] + uuid_str[9:13] + uuid_str[14:18]
            if timestamp not in timestamp_groups:
                timestamp_groups[timestamp] = []
            timestamp_groups[timestamp].append(uuid_str)

        # For UUIDs with same timestamp, they should still be unique
        for group_uuids in timestamp_groups.values():
            if len(group_uuids) > 1:
                # All UUIDs in the group should be different (full UUID comparison)
                assert len(set(group_uuids)) == len(group_uuids)
                # Extract clock sequence portions - they provide randomness
                # Not required to be different but helps with uniqueness
                # At minimum, overall UUIDs must be unique

    def test_format_consistency(self, generator: IdGeneratorUuid7) -> None:
        """Test that all generated UUIDs follow consistent format."""
        uuids = [str(generator.new()) for _ in range(50)]

        for uuid_str in uuids:
            # Test format
            parts = uuid_str.split('-')
            assert len(parts) == 5
            assert len(parts[0]) == 8  # time_high
            assert len(parts[1]) == 4  # time_mid
            assert len(parts[2]) == 4  # time_hi_and_version
            assert len(parts[3]) == 4  # clock_seq_hi_and_reserved + clock_seq_low
            assert len(parts[4]) == 12  # node

            # Test version
            assert parts[2][0] == '7'

            # Test variant
            assert parts[3][0].lower() in '89ab'

    def test_collision_resistance(self, generator: IdGeneratorUuid7) -> None:
        """Test collision resistance over large batch."""
        # Generate a large number of UUIDs
        batch_size = 50000
        uuids = set()

        for _ in range(batch_size):
            uuid_str = str(generator.new())
            assert uuid_str not in uuids, f'Collision detected: {uuid_str}'
            uuids.add(uuid_str)

        assert len(uuids) == batch_size

    def test_lexicographic_ordering_property(self, generator: IdGeneratorUuid7) -> None:
        """Test that UUIDs maintain lexicographic ordering over time."""
        # Generate UUIDs with time gaps
        batch1 = [str(generator.new()) for _ in range(5)]
        time.sleep(0.1)
        batch2 = [str(generator.new()) for _ in range(5)]
        time.sleep(0.1)
        batch3 = [str(generator.new()) for _ in range(5)]

        # All UUIDs in later batches should be lexicographically greater
        # than UUIDs in earlier batches
        for uuid1 in batch1:
            for uuid2 in batch2:
                assert uuid1 < uuid2
            for uuid3 in batch3:
                assert uuid1 < uuid3

        for uuid2 in batch2:
            for uuid3 in batch3:
                assert uuid2 < uuid3
