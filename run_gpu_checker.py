import subprocess
import sys
import time
from datetime import datetime

def main():
    miner_id = sys.argv[1]
    interval_sec = int(sys.argv[2])
    timeout_sec = 180
    sleep_sec = interval_sec - timeout_sec

    while 1:
        print("###############################################################")
        print("Start GPU Check @ {}".format((str(datetime.now()))))
        now = time.time()

        try:
            process = subprocess.call("python gpu_check.py {} {}".format(miner_id, interval_sec), stderr=subprocess.STDOUT, timeout = timeout_sec)

        except Exception as e:
            print(e)

        print("Finish GPU Check @ {}".format((str(datetime.now()))))
        print("****** It Takes {0:.1f} Second to Complete GPU Check! ******".format(time.time() - now))

        print("Start Sleep")
        print("###############################################################")
        print("")

        time.sleep(sleep_sec)

main()
