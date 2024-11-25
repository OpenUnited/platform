from apps.engagement.tests.test_notification_processing import executed_listeners

def listener_1(payload):
    """Test listener 1"""
    executed_listeners.append('listener_1')
    return True

def listener_2(payload):
    """Test listener 2"""
    executed_listeners.append('listener_2')
    return True