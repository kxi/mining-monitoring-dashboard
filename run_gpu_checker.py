import subprocess
import sys
import time

def main():
    miner_id = sys.argv[1]
    interval_sec = int(sys.argv[2])
    timeout_sec = 60
    sleep_sec = interval_sec - timeout_sec

    try:
        process = subprocess.call("python gpu_check.py {} {}".format(miner_id, interval_sec), stderr=subprocess.STDOUT, timeout = timeout_sec)
        # process = subprocess.Popen("python gpu_check.py {} {}".format(miner_id, interval_sec), stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell=True, timeout = timeout_sec)
        # output, error = process.communicate()

    except Exception as e:
        print(e)

    print("Start Sleep")
    time.sleep(sleep_sec)

main()
