import subprocess

def tester():

	miner_process_count = 0
	process = subprocess.Popen("tasklist /V", stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell=True)
	output, error = process.communicate()

	for line in output.splitlines():

		line = line.decode(errors='ignore')

		if "miner" and "Zec" in line:
			miner_process_count += 1
			print("EWBF Equihash Miner")

		if "zm.exe" in line:
			miner_process_count += 1
			print("DSTM Equihash Miner")

		if "ccminer" in line:
			print("CC Miner")

		if "excavator" in line:
			miner_process_count += 1
			print("Nicehash Excavator Miner")

		if "Claymore" in line:
			miner_process_count += 1
			print("Claymore Dual Miner")


	if miner_process_count == 0:
		print("No Miner is Running")

def main():
	tester()

main()
