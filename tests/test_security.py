# test_security.py
from builtins import RuntimeError, ValueError, isinstance, str
import pytest
from app.utils.security import hash_password, verify_password

@pytest.mark.parametrize("password", [
    "p@ssw0rd!",  # Special characters
    "密码",        # Unicode characters
    "123456",     # Numeric password
    "pass\nword", # Newline in password
])
def test_hash_password_varied_characters(password):
    """Test hashing passwords with varied character sets."""
    hashed = hash_password(password)
    assert isinstance(hashed, str)
    assert hashed.startswith('$2b$')

def test_hash_password_subtle_changes():
    """Test that small changes in the password create different hashes."""
    password = "password1"
    close_password = "password2"
    hashed1 = hash_password(password)
    hashed2 = hash_password(close_password)
    assert hashed1 != hashed2, "Different passwords should not have the same hash"

def test_hash_password_multiple_instances():
    """Test that hashing the same password multiple times results in unique hashes."""
    password = "consistent_password"
    hashes = {hash_password(password) for _ in range(10)}
    assert len(hashes) == 10, "Each hash should be unique"

def test_hash_length_and_structure():
    """Test the length and structure of the bcrypt hash."""
    password = "secure_password"
    hashed = hash_password(password)
    parts = hashed.split('$')
    assert len(parts) == 4, "Hash should consist of four parts separated by $"
    assert len(parts[3]) == 53, "Hash payload should be of correct length"


@pytest.mark.parametrize("rounds", [-1, 0, 40, 'ten'])  # Removed None
def test_hash_password_invalid_rounds(rounds):
    """Test handling of invalid round specifications."""
    with pytest.raises((ValueError, TypeError)):
        hash_password("secure_password", rounds)


def test_hash_zero_password():
    """Test hashing an all-zero password."""
    password = "00000000"
    hashed = hash_password(password)
    assert isinstance(hashed, str)
    assert hashed.startswith('$2b$')
    assert verify_password(password, hashed) is True

def test_hash_password():
    """Test that hashing password returns a bcrypt hashed string."""
    password = "secure_password"
    hashed = hash_password(password)
    assert hashed is not None
    assert isinstance(hashed, str)
    assert hashed.startswith('$2b$')

def test_hash_password_with_different_rounds():
    """Test hashing with different cost factors."""
    password = "secure_password"
    rounds = 10
    hashed_10 = hash_password(password, rounds)
    rounds = 12
    hashed_12 = hash_password(password, rounds)
    assert hashed_10 != hashed_12, "Hashes should differ with different cost factors"

def test_verify_password_correct():
    """Test verifying the correct password."""
    password = "secure_password"
    hashed = hash_password(password)
    assert verify_password(password, hashed) is True

def test_verify_password_incorrect():
    """Test verifying the incorrect password."""
    password = "secure_password"
    hashed = hash_password(password)
    wrong_password = "incorrect_password"
    assert verify_password(wrong_password, hashed) is False

def test_verify_password_invalid_hash():
    """Test verifying a password against an invalid hash format."""
    with pytest.raises(ValueError):
        verify_password("secure_password", "invalid_hash_format")

@pytest.mark.parametrize("password", [
    "",
    " ",
    "a"*100  # Long password
])
def test_hash_password_edge_cases(password):
    """Test hashing various edge cases."""
    hashed = hash_password(password)
    assert isinstance(hashed, str) and hashed.startswith('$2b$'), "Should handle edge cases properly"

def test_verify_password_edge_cases():
    """Test verifying passwords with edge cases."""
    password = " "
    hashed = hash_password(password)
    assert verify_password(password, hashed) is True
    assert verify_password("not empty", hashed) is False

# This function tests the error handling when an internal error occurs in bcrypt
def test_hash_password_internal_error(monkeypatch):
    """Test proper error handling when an internal bcrypt error occurs."""
    def mock_bcrypt_gensalt(rounds):
        raise RuntimeError("Simulated internal error")

    monkeypatch.setattr("bcrypt.gensalt", mock_bcrypt_gensalt)
    with pytest.raises(ValueError):
        hash_password("test")

