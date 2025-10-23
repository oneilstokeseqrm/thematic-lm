"""Tests for quote ID encoding and decoding."""

import pytest

from thematic_lm.utils.quote_id import encode_quote_id, decode_quote_id, QUOTE_ID_PATTERN


class TestEncodeQuoteId:
    """Tests for encode_quote_id function."""
    
    def test_encode_without_msg_index(self):
        """Test encoding quote ID without message index."""
        quote_id = encode_quote_id(
            interaction_id="550e8400-e29b-41d4-a716-446655440000",
            chunk_index=0,
            start_pos=10,
            end_pos=50
        )
        
        assert quote_id == "550e8400-e29b-41d4-a716-446655440000:ch_0:10-50"
    
    def test_encode_with_msg_index(self):
        """Test encoding quote ID with message index."""
        quote_id = encode_quote_id(
            interaction_id="550e8400-e29b-41d4-a716-446655440000",
            chunk_index=2,
            start_pos=100,
            end_pos=200,
            msg_index=5
        )
        
        assert quote_id == "550e8400-e29b-41d4-a716-446655440000:msg_5:ch_2:100-200"
    
    def test_encode_with_large_offsets(self):
        """Test encoding with large offset values."""
        quote_id = encode_quote_id(
            interaction_id="a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            chunk_index=10,
            start_pos=5000,
            end_pos=5500
        )
        
        assert quote_id == "a1b2c3d4-e5f6-7890-abcd-ef1234567890:ch_10:5000-5500"


class TestDecodeQuoteId:
    """Tests for decode_quote_id function."""
    
    def test_decode_without_msg_index(self):
        """Test decoding quote ID without message index."""
        quote_id = "550e8400-e29b-41d4-a716-446655440000:ch_0:10-50"
        result = decode_quote_id(quote_id)
        
        assert result == {
            "interaction_id": "550e8400-e29b-41d4-a716-446655440000",
            "msg_index": None,
            "chunk_index": 0,
            "start_pos": 10,
            "end_pos": 50
        }
    
    def test_decode_with_msg_index(self):
        """Test decoding quote ID with message index."""
        quote_id = "550e8400-e29b-41d4-a716-446655440000:msg_5:ch_2:100-200"
        result = decode_quote_id(quote_id)
        
        assert result == {
            "interaction_id": "550e8400-e29b-41d4-a716-446655440000",
            "msg_index": 5,
            "chunk_index": 2,
            "start_pos": 100,
            "end_pos": 200
        }
    
    def test_decode_invalid_format(self):
        """Test decoding invalid quote ID raises ValueError."""
        invalid_ids = [
            "not-a-valid-quote-id",
            "550e8400:10-50",  # Missing chunk_index
            "550e8400:ch_0",  # Missing offsets
            "550e8400:ch_0:10",  # Missing end_pos
            "550e8400:ch_a:10-50",  # Non-numeric chunk_index
            "550e8400:ch_0:abc-50",  # Non-numeric start_pos
        ]
        
        for invalid_id in invalid_ids:
            with pytest.raises(ValueError, match="Invalid quote_id format"):
                decode_quote_id(invalid_id)
    
    def test_round_trip_without_msg_index(self):
        """Test encoding and decoding round-trip without message index."""
        original = {
            "interaction_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            "chunk_index": 3,
            "start_pos": 250,
            "end_pos": 350
        }
        
        encoded = encode_quote_id(
            interaction_id=original["interaction_id"],
            chunk_index=original["chunk_index"],
            start_pos=original["start_pos"],
            end_pos=original["end_pos"]
        )
        
        decoded = decode_quote_id(encoded)
        
        assert decoded["interaction_id"] == original["interaction_id"]
        assert decoded["chunk_index"] == original["chunk_index"]
        assert decoded["start_pos"] == original["start_pos"]
        assert decoded["end_pos"] == original["end_pos"]
        assert decoded["msg_index"] is None
    
    def test_round_trip_with_msg_index(self):
        """Test encoding and decoding round-trip with message index."""
        original = {
            "interaction_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
            "chunk_index": 1,
            "start_pos": 0,
            "end_pos": 100,
            "msg_index": 3
        }
        
        encoded = encode_quote_id(
            interaction_id=original["interaction_id"],
            chunk_index=original["chunk_index"],
            start_pos=original["start_pos"],
            end_pos=original["end_pos"],
            msg_index=original["msg_index"]
        )
        
        decoded = decode_quote_id(encoded)
        
        assert decoded["interaction_id"] == original["interaction_id"]
        assert decoded["chunk_index"] == original["chunk_index"]
        assert decoded["start_pos"] == original["start_pos"]
        assert decoded["end_pos"] == original["end_pos"]
        assert decoded["msg_index"] == original["msg_index"]


class TestQuoteIdPattern:
    """Tests for QUOTE_ID_PATTERN regex."""
    
    def test_pattern_matches_valid_ids(self):
        """Test regex pattern matches valid quote IDs."""
        valid_ids = [
            "550e8400-e29b-41d4-a716-446655440000:ch_0:10-50",
            "a1b2c3d4-e5f6-7890-abcd-ef1234567890:msg_5:ch_2:100-200",
            "12345678-1234-1234-1234-123456789012:ch_99:0-9999",
            "abcdef01-2345-6789-abcd-ef0123456789:msg_0:ch_0:0-1",
        ]
        
        for quote_id in valid_ids:
            match = QUOTE_ID_PATTERN.match(quote_id)
            assert match is not None, f"Pattern should match: {quote_id}"
    
    def test_pattern_rejects_invalid_ids(self):
        """Test regex pattern rejects invalid quote IDs."""
        invalid_ids = [
            "not-a-uuid:ch_0:10-50",  # Invalid UUID format (uppercase not allowed)
            "550e8400:10-50",  # Missing chunk_index
            "550e8400:ch_0",  # Missing offsets
            "550e8400:ch_0:10",  # Missing end_pos
            "550e8400:ch_a:10-50",  # Non-numeric chunk_index
            "550e8400:ch_0:abc-50",  # Non-numeric start_pos
            "550e8400:ch_0:10-xyz",  # Non-numeric end_pos
            "550e8400:msg_a:ch_0:10-50",  # Non-numeric msg_index
        ]
        
        for quote_id in invalid_ids:
            match = QUOTE_ID_PATTERN.match(quote_id)
            assert match is None, f"Pattern should not match: {quote_id}"
    
    def test_unicode_interaction_id(self):
        """Test with UUID format interaction IDs (lowercase hex with hyphens)."""
        # UUIDs are lowercase hex with hyphens
        uuid_ids = [
            "550e8400-e29b-41d4-a716-446655440000:ch_0:10-50",
            "a1b2c3d4-e5f6-7890-abcd-ef1234567890:ch_1:20-60",
            "00000000-0000-0000-0000-000000000000:ch_0:0-1",
            "ffffffff-ffff-ffff-ffff-ffffffffffff:ch_0:0-1",
        ]
        
        for quote_id in uuid_ids:
            result = decode_quote_id(quote_id)
            assert result["interaction_id"] in quote_id
            # Verify the interaction_id is extracted correctly
            encoded = encode_quote_id(
                interaction_id=result["interaction_id"],
                chunk_index=result["chunk_index"],
                start_pos=result["start_pos"],
                end_pos=result["end_pos"],
                msg_index=result["msg_index"]
            )
            assert encoded == quote_id
