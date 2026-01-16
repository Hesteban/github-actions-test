import pytest
from main import add, multiply, greet

def test_add():
    """Test the add function"""
    assert add(2, 3) == 5
    assert add(-1, 1) == 0
    assert add(0, 0) == 0

def test_multiply():
    """Test the multiply function"""
    assert multiply(2, 3) == 6
    assert multiply(-2, 3) == -6
    assert multiply(0, 5) == 0

def test_greet():
    """Test the greet function"""
    assert greet("Alice") == "Hello, Alice!"
    assert greet("Bob") == "Hello, Bob!"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
