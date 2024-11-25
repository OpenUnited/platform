from typing import Dict

# List to track executed listeners
executed_listeners = []

def listener_1(payload: Dict) -> bool:
    """Test listener 1"""
    print("Listener 1 executed")
    executed_listeners.append('listener1')
    return True

def listener_2(payload: Dict) -> bool:
    """Test listener 2"""
    print("Listener 2 executed")
    executed_listeners.append('listener2')
    return True

def clear_executed() -> None:
    """Clear the executed listeners list"""
    executed_listeners.clear()