def add(a, b):
    """Simple addition function"""
    return a + b

def multiply(a, b):
    """Simple multiplication function"""
    return a * b

def greet(name):
    """Simple greeting function"""
    return f"Hello, {name}!"

if __name__ == "__main__":
    print(greet("World"))
    print(f"2 + 3 = {add(2, 3)}")
    print(f"4 * 5 = {multiply(4, 5)}")
