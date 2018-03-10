import subprocess
import sys
import gspread
from datetime import datetime
import time
from oauth2client.service_account import ServiceAccountCredentials

class GPU():
	def __init__(self):
		self.gid = None
		self.model = None
		self.utilization = None
		self.temp_curr = None
		self.core_clock = None
		self.power_draw = None
		self.power_limit = None
		self.default_power_limit = None
		self.fan_speed = None


def nvidia_smi_call():

	# DEBUG = True
	DEBUG = False

	gpu_dict = dict()

	prev_line = None
	process = subprocess.Popen("nvidia-smi.exe -a",stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell=True)
	output, error = process.communicate()

	gpu_index = 1

	for line in output.splitlines():
		line = line.decode()
		if DEBUG:
			print(line)
		if "GPU 00000000" in line:
			gid = int(line.split(':')[1])
			gpu_dict[gid] = GPU()
			gpu_dict[gid].gid = gpu_index
			print("Found GPU: #{}".format(gpu_dict[gid].gid))
			gpu_index += 1

		if "Product Name" in line:
			model = line.split(':')[1].strip(" ")
			if DEBUG:
				print(model)
			gpu_dict[gid].model = model

		if "Gpu" in line:
			utilization = float(line.split(':')[1].split()[0])/100
			if DEBUG:
				print(utilization)
			gpu_dict[gid].utilization = utilization

		if "GPU Current Temp" in line:
			temp_curr = int(line.split(':')[1].split()[0])
			if DEBUG:
				print(temp_curr)
			gpu_dict[gid].temp_curr = temp_curr

		if "Graphics" in line and prev_line.strip() == "Clocks":
			core_clock = line.split(':')[1].strip()
			if DEBUG:
				print(core_clock)
			gpu_dict[gid].core_clock = core_clock

		if "Power Draw" in line:
			power_draw = line.split(':')[1].strip().strip('W')
			if DEBUG:
				print(power_draw)
			gpu_dict[gid].power_draw = power_draw

		if "Enforced Power Limit" == line.split(':')[0].strip():
			power_limit = line.split(':')[1].strip().strip('W')
			if DEBUG:
				print(power_limit)
			gpu_dict[gid].power_limit = power_limit

		if "Default Power Limit" == line.split(':')[0].strip():
			default_power_limit = line.split(':')[1].strip().strip('W')
			if DEBUG:
				print(default_power_limit)
			gpu_dict[gid].default_power_limit = default_power_limit

		if "Fan Speed" == line.split(':')[0].strip():
			fan_speed = line.split(':')[1].strip()
			if DEBUG:
				print(fan_speed)
			gpu_dict[gid].fan_speed = fan_speed
		prev_line = line

	return gpu_dict



def nvidia_smi_call_stub():

	gpu_dict = dict()
	gpu = gpu_dict[1] = GPU()
	gpu.gid = 1
	gpu.model = "Nvidia GTX 980"
	gpu.utilization = 0.01
	gpu.temp_curr = -5
	gpu.core_clock = "1000 MHz"
	gpu.power_draw = "99"
	gpu.power_limit = "100"
	gpu.default_power_limit = "150"
	gpu.fan_speed = "55%"

	return gpu_dict



def gpu_monitor(miner_id):
	sheet_row_start = {
    	'miner1': 2,
    	'miner2': 10,
    	'miner3': 18,
    	'miner4': 26,
    	'miner5': 36,
    	'miner6': 45,
    	'kai_test_miner': 53
	}

	gpu_dict = nvidia_smi_call()
	# gpu_dict = nvidia_smi_call_stub()

	# use creds to create a client to interact with the Google Drive API
	scope = ['https://spreadsheets.google.com/feeds']
	creds = ServiceAccountCredentials.from_json_keyfile_name('key.json', scope)
	client = gspread.authorize(creds)
	# Find a workbook by name and open the first sheet
	# Make sure you use the right name here.
	sheet = client.open("miner-dashboard").sheet1
	dt_now = datetime.now().strftime('%Y-%m-%d %H:%M')

	row_start = sheet_row_start[miner_id]
	range_build = 'L' + str(row_start)
	cell_list = sheet.range(range_build)
	cell_list[0].value = dt_now
	sheet.update_cells(cell_list)


	for idx, gpu_dict_key in enumerate(gpu_dict.keys()):
		gpu = gpu_dict[gpu_dict_key]
		range_build = 'B' + str(row_start + idx) + ':K' + str(row_start + idx)
		cell_list = sheet.range(range_build)
		cell_list[0].value = gpu.gid
		cell_list[1].value = gpu.model
		cell_list[2].value = gpu.temp_curr
		cell_list[3].value = float(gpu.power_limit)*1.0/float(gpu.default_power_limit)
		cell_list[4].value = gpu.fan_speed
		cell_list[5].value = gpu.utilization
		cell_list[6].value = gpu.core_clock
		cell_list[7].value = gpu.power_draw
		cell_list[8].value = gpu.power_limit
		cell_list[9].value = gpu.default_power_limit

		# Send update in batch mode
		print("Start Sync to gspread")
		sheet.update_cells(cell_list)

def main():
	miner_id = sys.argv[1]
	interval = int(sys.argv[2])
	print("This is Miner: {}".format(miner_id))

	while 1:
		try:
			gpu_monitor(miner_id)
		except:
			print("Exception")
			pass

		time.sleep(interval)


main()
