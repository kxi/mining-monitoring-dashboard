SHELL=/bin/sh
PATH=/home/coin/bin:/home/coin/.local/bin:/home/coin/miniconda3/bin:/home/coin/miniconda3/bin:/home/coin/bin:/home/coin/.local/bin:/usr/local/bin:/usr/bin:/bin:/usr/local/games:/usr/games:/snap/bin
*/5 * * * * cd ~/mining-monitoring-dashboard/;/usr/bin/timeout 280 python gpu_check.py kai_test_miner > /tmp/gpu_dashboard_checker.log 2>&1
