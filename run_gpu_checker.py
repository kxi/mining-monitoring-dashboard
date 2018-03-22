import subprocess
import sys
import time

def main():
    miner_id = sys.argv[1]
    interval_sec = int(sys.argv[2])
    timeout_sec = 60
    sleep_sec = interval_sec - timeout_sec

    try:
        process = subprocess.check_output("python gpu_check.py {} {}".format(miner_id, interval_sec), stderr = subprocess.PIPE, timeout = timeout_sec)
    except Exception as e:
        print(e)

    time.sleep(sleep_sec)

main()
