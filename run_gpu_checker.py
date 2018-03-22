import subprocess
import sys
import time
from datetime import datetime

def main():
    miner_id = sys.argv[1]
    interval_sec = int(sys.argv[2])
    timeout_sec = 60
    sleep_sec = interval_sec - timeout_sec

    print(str(datetime.now()))

    try:
        process = subprocess.call("python gpu_check.py {} {}".format(miner_id, interval_sec), stderr=subprocess.STDOUT, timeout = timeout_sec)

    except Exception as e:
        print(e)

    print("Start Sleep")
    time.sleep(sleep_sec)

    print(str(datetime.now()))

main()
