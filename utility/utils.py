import sys
import time

def fancy_out(message):
    output = ("\r....."+message).ljust(80, ".")
    sys.stdout.write(output)
    sys.stdout.flush()
    time.sleep(0.5)
