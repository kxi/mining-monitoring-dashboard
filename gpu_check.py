import subprocess
import sys
from os import path
import gspread
from datetime import datetime
import time
from oauth2client.service_account import ServiceAccountCredentials
import xmltodict
from time import mktime
import uuid
import hmac
import requests
import json
from hashlib import sha256
import optparse


class GPU():
	def __init__(self):
		self.gid = None
		self.model = None
		self.utilization = None
		self.temp_curr = None
		self.core_clock = None
		self.memory_clock = None
		self.power_draw = None
		self.power_limit = None
		self.default_power_limit = None
		self.fan_speed = None
		self.power_ai = None
		self.nh_status = ''
		self.nh_algo = ''
		self.nh_speed = ''



def nvidia_smi_call(DEBUG = False):

	gpu_dict = dict()

	prev_line = None
	process = subprocess.Popen("nvidia-smi -x -q", stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell=True)
	output, error = process.communicate()
	info_dict_gpu_count = xmltodict.parse(output)
	num_GPU = int(info_dict_gpu_count['nvidia_smi_log']['attached_gpus'])

	if DEBUG:
		print(output)

	# print(info_dict['nvidia_smi_log']['gpu'][0])

	print(f"Number of GPU: {num_GPU}")

	for i in range(num_GPU):

		process = subprocess.Popen(f"nvidia-smi -x -q -i {i}", stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell=True)
		output, error = process.communicate()

		info_dict = xmltodict.parse(output)


		gid = i + 1
		gpu_dict[gid] = GPU()
		gpu_dict[gid].gid = gid
		print("Found GPU: #{}".format(gpu_dict[gid].gid))


		model = info_dict['nvidia_smi_log']['gpu']['product_name'].replace("GeForce", "").strip(" ")
		if DEBUG:
			print(model)
		gpu_dict[gid].model = model


		utilization = info_dict['nvidia_smi_log']['gpu']['utilization']['gpu_util']
		if DEBUG:
			print(utilization)
		gpu_dict[gid].utilization = float(utilization.rstrip(' %')) / 100.0

		temp_curr = int(info_dict['nvidia_smi_log']['gpu']['temperature']['gpu_temp'].strip(' C'))
		if DEBUG:
			print(temp_curr)
		gpu_dict[gid].temp_curr = temp_curr


		core_clock = info_dict['nvidia_smi_log']['gpu']['clocks']['graphics_clock']
		if DEBUG:
			print(core_clock)
		gpu_dict[gid].core_clock = core_clock


		memory_clock = info_dict['nvidia_smi_log']['gpu']['clocks']['mem_clock']
		if DEBUG:
			print(memory_clock)
		gpu_dict[gid].memory_clock = memory_clock

		power_draw = info_dict['nvidia_smi_log']['gpu']['power_readings']['power_draw'].strip('W').strip()
		if DEBUG:
			print(power_draw)
		gpu_dict[gid].power_draw = float(power_draw)


		power_limit = info_dict['nvidia_smi_log']['gpu']['power_readings']['enforced_power_limit'].strip('W').strip()
		if DEBUG:
			print(power_limit)
		gpu_dict[gid].power_limit = float(power_limit)


		default_power_limit = info_dict['nvidia_smi_log']['gpu']['power_readings']['default_power_limit'].strip('W').strip()
		if DEBUG:
			print(default_power_limit)
		gpu_dict[gid].default_power_limit = float(default_power_limit)


		fan_speed = info_dict['nvidia_smi_log']['gpu']['fan_speed']
		if DEBUG:
			print(fan_speed)
		gpu_dict[gid].fan_speed = fan_speed

		# print(info_dict['nvidia_smi_log']['gpu'][0]['product_name'].replace("GeForce", "").strip(" "))
		# print(info_dict['nvidia_smi_log']['gpu'][0]['utilization']['gpu_util'])
		# print(info_dict['nvidia_smi_log']['gpu'][0]['temperature']['gpu_temp'])
		# print(info_dict['nvidia_smi_log']['gpu'][0]['clocks']['graphics_clock'])
		# print(info_dict['nvidia_smi_log']['gpu'][0]['clocks']['mem_clock'])
		# print(info_dict['nvidia_smi_log']['gpu'][0]['power_readings']['power_draw'])
		# print(info_dict['nvidia_smi_log']['gpu'][0]['power_readings']['enforced_power_limit'])
		# print(info_dict['nvidia_smi_log']['gpu'][0]['power_readings']['default_power_limit'])
		# print(info_dict['nvidia_smi_log']['gpu'][0]['fan_speed'])

	return gpu_dict



def nvidia_smi_call_stub():

	gpu_dict = dict()
	gpu = gpu_dict[1] = GPU()
	gpu.gid = 1
	gpu.model = "Nvidia GTX 980"
	gpu.utilization = 0.01
	gpu.temp_curr = -5
	gpu.core_clock = "1000 MHz"
	gpu.memory_clock = "8000 MHz"
	gpu.power_draw = "99"
	gpu.power_limit = "100"
	gpu.default_power_limit = "150"
	gpu.fan_speed = "55%"

	return gpu_dict


def check_miner(DEBUG):

	MIN_PW_FLAG = False

	miner_process_count = 0
	process = subprocess.Popen("tasklist /V", stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell=True)
	output, error = process.communicate()

	miner = ""

	for line in output.splitlines():

		line = line.decode(errors='ignore')

		if "miner" and "Zec" in line:
			miner_process_count += 1
			if DEBUG:
				print("EWBF Equihash Miner")
			miner = "EWBF (Equihash)"

		if "zm.exe" in line:
			miner_process_count += 1
			if DEBUG:
				print("DSTM Equihash Miner")
			miner = "DSTM (Equihash)"

		if "ccminer" in line:
			miner_process_count += 1
			if DEBUG:
				print("CC Miner")
			miner = "CC Miner"

		if "excavator" in line:
			miner_process_count += 1
			if DEBUG:
				print("Excavator (Nicehash)")
			miner = "Excavator (Nicehash)"

		if "Claymore" in line:
			miner_process_count += 1
			if DEBUG:
				print("Claymore")
			miner = "Claymore Dual Miner"

		if "PhoenixMiner" in line:
			miner_process_count += 1
			if DEBUG:
				print("Phoenix")
			miner = "Phoenix (Eth)"
			MIN_PW_FLAG = True


	if miner_process_count == 0:
		if DEBUG:
			print("No Miner is Running")
		miner = "Not Running"

	return [miner, MIN_PW_FLAG]

def get_nicehash_secret(gc, DEBUG=False):
	if path.exists("secret.json"):
		print('Load Secret From Local JSON File')
		with open('secret.json') as f:
			secret = json.load(f)
	else:
		print('Load Secret From Google Spreadsheet')
		sheet_auth = gc.open_by_url("https://docs.google.com/spreadsheets/d/1EwzqCCLXVznobht-8LG-sDWapaLlLrzn6jlsLcRyJnI").worksheet("secret")
		secret = dict()

		secret_sheet_values = sheet_auth.batch_get(['A1:B9'])[0]

		for entry in secret_sheet_values:
			if DEBUG:
				print(entry)
			secret[entry[0]] = entry[1]

	return secret


def check_nicehash(miner_id, gpu_dict, nh_secret, DEBUG=False):

	rigId = nh_secret[miner_id]

	host = 'https://api2.nicehash.com'
	path = f'/main/api/v2/mining/rig2/{rigId}/'
	method = 'GET'

	organisation_id = nh_secret['organisation_id']
	key = nh_secret['API_key']
	secret = nh_secret['API_secret']

	query = f"rigId={rigId}"

	now = datetime.now()
	now_ec_since_epoch = mktime(now.timetuple()) + now.microsecond / 1000000.0
	xtime = int(now_ec_since_epoch * 1000)

	xnonce = str(uuid.uuid4())

	message = bytearray(key, 'utf-8')
	message += bytearray('\x00', 'utf-8')
	message += bytearray(str(xtime), 'utf-8')
	message += bytearray('\x00', 'utf-8')
	message += bytearray(xnonce, 'utf-8')
	message += bytearray('\x00', 'utf-8')
	message += bytearray('\x00', 'utf-8')
	message += bytearray(organisation_id, 'utf-8')
	message += bytearray('\x00', 'utf-8')
	message += bytearray('\x00', 'utf-8')
	message += bytearray(method, 'utf-8')
	message += bytearray('\x00', 'utf-8')
	message += bytearray(path, 'utf-8')
	message += bytearray('\x00', 'utf-8')
	message += bytearray(query, 'utf-8')


	digest = hmac.new(bytearray(secret, 'utf-8'), message, sha256).hexdigest()
	xauth = key + ":" + digest

	headers = {
	    'X-Time': str(xtime),
	    'X-Nonce': xnonce,
	    'X-Auth': xauth,
	    'Content-Type': 'application/json',
	    'X-Organization-Id': organisation_id,
	    'X-Request-Id': str(uuid.uuid4())
	}

	s = requests.Session()
	s.headers = headers

	url = host + path
	if query:
	    url += '?' + query

	print(url)

	response = s.request(method, url)

	# if DEBUG:
	print(response.content)

	if response.status_code == 200:
		nh_info = json.loads(response.content)
		index = 0
		for i in range(len(nh_info['devices'])):
			if nh_info['devices'][i]['deviceType']['description'] == 'CPU':
				continue

			status = nh_info['devices'][i]['status']['description']
			gpu_dict[index+1].nh_status = status

			if len(nh_info['devices'][1]['speeds']) > 0:
				print(nh_info['devices'][i]['speeds'][0])
				algo = nh_info['devices'][i]['speeds'][0]['title']
				speed = str(round(float(nh_info['devices'][i]['speeds'][0]['speed']), 1)) + ' ' + nh_info['devices'][i]['speeds'][0]['displaySuffix']
			else:
				algo = ""
				speed = ""
			gpu_dict[index+1].nh_algo = algo
			gpu_dict[index+1].nh_speed = speed

			index += 1

	return gpu_dict

def gpu_monitor(miner_id, DEBUG = False):
	sheet_row_start = {
    	'miner1': 2,
    	'miner2': 10,
    	'miner3': 18,
    	'miner4': 26,
    	'miner5': 36,
    	'miner6': 45,
    	'kai_test_miner': 53
	}

	miner_row_start = {
    	'miner1': 7,
    	'miner2': 15,
    	'miner3': 22,
    	'miner4': 33,
    	'miner5': 41,
    	'miner6': 50,
    	'kai_test_miner': 54
	}

	up_icon_img_url = "http://users.tpg.com.au/heroxk82/up2.PNG"
	down_icon_img_url = "http://users.tpg.com.au/heroxk82/down2.PNG"
	stable_icon_img_url = "http://users.tpg.com.au/heroxk82/stable2.PNG"
	gpu_dict = nvidia_smi_call(DEBUG)
	# gpu_dict = nvidia_smi_call_stub()

	if miner_id in ['miner1', 'miner3', 'miner5']:
		key_file = 'key.json'
	else:
		key_file = 'key2.json'

	# use creds to create a client to interact with the Google Drive API
	scope = ['https://spreadsheets.google.com/feeds']
	creds = ServiceAccountCredentials.from_json_keyfile_name(key_file, scope)
	gc = gspread.authorize(creds)
	# Find a workbook by name and open the first sheet
	# Make sure you use the right name here.
	sheet = gc.open_by_url("https://docs.google.com/spreadsheets/d/1EwzqCCLXVznobht-8LG-sDWapaLlLrzn6jlsLcRyJnI").worksheet("Dashboard")
	dt_now = datetime.now().strftime('%Y-%m-%d %H:%M')


	# Check NH
	nh_secret = get_nicehash_secret(gc, DEBUG)
	gpu_dict = check_nicehash(miner_id, gpu_dict, nh_secret, DEBUG)

	# Miner Type
	miner, MIN_PW_FLAG = check_miner(DEBUG)
	row_start = miner_row_start[miner_id]
	miner_range_build = 'A' + str(row_start) + ':' + 'A' + str(row_start)
	cell_list = sheet.range(miner_range_build)
	cell_list[0].value = miner
	sheet.update_cells(cell_list)


	# Script Run Time
	row_start = sheet_row_start[miner_id]
	range_build = 'P' + str(row_start) + ':' + 'P' + str(row_start)
	cell_list = sheet.range(range_build)
	cell_list[0].value = dt_now
	sheet.update_cells(cell_list)


	for idx, gpu_dict_key in enumerate(gpu_dict.keys()):
		gpu = gpu_dict[gpu_dict_key]
		range_build = 'B' + str(row_start + idx) + ':O' + str(row_start + idx)
		cell_list = sheet.range(range_build)
		cell_list[0].value = gpu.gid
		cell_list[1].value = gpu.model
		cell_list[2].value = gpu.temp_curr
		cell_list[3].value = gpu.nh_status
		cell_list[4].value = gpu.nh_algo
		cell_list[5].value = gpu.nh_speed
		cell_list[6].value = float(gpu.power_limit)*1.0/float(gpu.default_power_limit)
		cell_list[7].value = gpu.fan_speed
		cell_list[8].value = gpu.utilization
		cell_list[9].value = gpu.core_clock
		cell_list[10].value = gpu.memory_clock
		cell_list[11].value = gpu.power_draw
		cell_list[12].value = gpu.power_limit
		cell_list[13].value = gpu.default_power_limit


		# Smart Power Logic
		ENABLE_SMART_POWER_FLAG = sheet.acell('X' + str(row_start  + idx)).value

		# IF Power AI Strategy is Enabled
		if ENABLE_SMART_POWER_FLAG == "Y":
			print("GPU #{}: Smart Power Enabled, Check and Adjust Power if Necessary!".format(gpu.gid))

			device_id = gpu.gid - 1

			if gpu.utilization < 0.3:
				print("GPU #{}: GPU is Not Mining, Don't Adjust Power".format(gpu.gid))
				sheet.update_acell('R' + str(row_start + idx), '=image("{}",4,15,15)'.format(stable_icon_img_url))

			else:
				smart_power_entry = sheet.batch_get(['S'+str(row_start + idx)+':'+'W'+str(row_start  + idx)])[0][0]
				if DEBUG:
					print(smart_power_entry)

				temperature_lb = int(smart_power_entry[0])
				temperature_ub = int(smart_power_entry[1])
				raw_pw_limit_lb_str = smart_power_entry[2]
				raw_pw_limit_ub_str = smart_power_entry[3]
				raw_current_pw_limit = smart_power_entry[4]

				# temperature_lb = int(sheet.acell('S' + str(row_start + idx)).value)
				# temperature_ub = int(sheet.acell('T' + str(row_start + idx)).value)
				# raw_pw_limit_lb_str = sheet.acell('U' + str(row_start + idx)).value
				# raw_pw_limit_ub_str = sheet.acell('V' + str(row_start + idx)).value
				# raw_current_pw_limit = sheet.acell('W' + str(row_start  + idx)).value

				if '%' in raw_pw_limit_lb_str:
					pw_limit_lb = float(raw_pw_limit_lb_str.strip('%'))/100.0
				else:
					pw_limit_lb = float(raw_pw_limit_lb_str)

				if '%' in raw_pw_limit_ub_str:
					pw_limit_ub = float(raw_pw_limit_ub_str.strip('%'))/100.0
				else:
					pw_limit_ub = float(raw_pw_limit_ub_str)

				if '%' in raw_current_pw_limit:
					pw_limit_curr = float(raw_current_pw_limit.strip('%'))/100.0
				elif not raw_current_pw_limit:
					pw_limit_curr = None
				else:
					pw_limit_curr = float(raw_current_pw_limit)


				# Just in Case, Wrong Value in Spreadsheet
				if temperature_lb > 67 or pw_limit_lb < 0.5 or pw_limit_ub > 0.9:
					print("GPU #{}: Smart Power Value is Not Reasonable, Please Check Spreadsheet".format(gpu.gid))
					pass


				##############################################################
				# Case 1: Eth Mini - Minimize Power
				##############################################################

				if MIN_PW_FLAG == True:
					print("Eth Mining Detected. Suppress Power")

					if not pw_limit_curr: # No Value, Last Run is Non-Eth
						print("Temperature Checkpoint Has No Value, Last Run is Non-Eth")
						pw_limit_checkpoint = cell_list[6].value # Store Latest Power Limit
						sheet.update_acell('W' + str(row_start + idx), pw_limit_checkpoint)

					# Adjust Power
					new_power_limit = int(max(110, pw_limit_lb * float(gpu.default_power_limit)))

					if int(gpu.power_limit) > new_power_limit:
						sheet.update_acell('R' + str(row_start + idx), '=image("{}",4,15,15)'.format(down_icon_img_url))
						process = subprocess.Popen("nvidia-smi.exe -i {} -pl {}".format(device_id, new_power_limit), stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell=True)
						output, error = process.communicate()
						print("GPU #{}: Power Suppressed: {}".format(gpu.gid, output))


					if int(gpu.power_limit) < new_power_limit:
						sheet.update_acell('R' + str(row_start + idx), '=image("{}",4,15,15)'.format(up_icon_img_url))
						process = subprocess.Popen("nvidia-smi.exe -i {} -pl {}".format(device_id, new_power_limit), stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell=True)
						output, error = process.communicate()
						print("GPU #{}: Power Suppressed: {}".format(gpu.gid, output))


					if int(gpu.power_limit) == new_power_limit:
						sheet.update_acell('R' + str(row_start + idx), '=image("{}",4,15,15)'.format(stable_icon_img_url))

					gpu.power_limit = str(int(new_power_limit))



				##############################################################
				# Case 2: Do Non-Eth Mining such as Equihash
				##############################################################

				if MIN_PW_FLAG == False:
					print("Non-Eth Mining Detected. Enter Normal Power Cycle")

					if pw_limit_curr: # No Value, Last Run is Eth, Need to Recover
						if pw_limit_curr <= pw_limit_ub and pw_limit_curr >= 0.5:
							recovered_power_limit = pw_limit_curr * float(gpu.default_power_limit)
							process = subprocess.Popen("nvidia-smi.exe -i {} -pl {}".format(device_id, recovered_power_limit), stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell=True)
							output, error = process.communicate()
							print("GPU #{}: Power Recovered: {}".format(gpu.gid, output))

							sheet.update_acell('R' + str(row_start + idx), '=image("{}",4,15,15)'.format(up_icon_img_url))

							gpu.power_limit = str(int(recovered_power_limit))

							# Clear Checkpoint Cell
							sheet.update_acell('W' + str(row_start + idx), "")
						else:
							print("You Power Limit Checkpoint is Not Reasonable, Please Check")

					if not pw_limit_curr: # No Value, Last Run is Non-Eth

						power_delta_inc = int(gpu.default_power_limit * 0.02)
						power_delta_dec = int(gpu.default_power_limit * 0.03)

						# Is Over Limit Now! Reduce Power Immediately:
						if gpu.power_limit > int(pw_limit_ub * float(gpu.default_power_limit)):
							new_power_limit = int(pw_limit_ub * float(gpu.default_power_limit))
							process = subprocess.Popen("nvidia-smi.exe -i {} -pl {}".format(device_id, new_power_limit), stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell=True)
							output, error = process.communicate()
							print("GPU #{}: Over Power Limit UB. Reset to UB: {}".format(gpu.gid, output))

							sheet.update_acell('R' + str(row_start + idx), '=image("{}",4,15,15)'.format(down_icon_img_url))

							gpu.power_limit = str(int(new_power_limit))

						else:
							if gpu.temp_curr < temperature_lb:
								if int(gpu.power_limit) < int(pw_limit_ub * float(gpu.default_power_limit)):
									print("GPU #{}: Temperature is Too Low, Power Up. \
									 Current Power Limit = {} W, Power Limit UB = {} W".format(gpu.gid, gpu.power_limit, pw_limit_ub * float(gpu.default_power_limit)))
									new_power_limit = min(float(gpu.power_limit) + power_delta_inc, float(gpu.default_power_limit * pw_limit_ub))

									process = subprocess.Popen("nvidia-smi.exe -i {} -pl {}".format(device_id, new_power_limit), stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell=True)
									output, error = process.communicate()
									print("GPU #{}: Power Increased: {}".format(gpu.gid, output))

									sheet.update_acell('R' + str(row_start + idx), '=image("{}",4,15,15)'.format(up_icon_img_url))

									gpu.power_limit = str(int(new_power_limit))


								else:
									print("GPU #{}: Temperature is Too Low, However Already Hit Power Limit UB. \
									  Current Power Limit = {} W, Power Limit UB = {} W".format(gpu.gid, gpu.power_limit, pw_limit_ub * float(gpu.default_power_limit)))

									sheet.update_acell('R' + str(row_start + idx), '=image("{}",4,15,15)'.format(stable_icon_img_url))


							if gpu.temp_curr >= temperature_ub:
								if int(gpu.power_limit) > int(pw_limit_lb * float(gpu.default_power_limit)):
									print("GPU #{}: Temperature is Too High, Power Down. \
									 Current Power Limit = {} W, Power Limit LB = {} W".format(gpu.gid, gpu.power_limit, pw_limit_lb * float(gpu.default_power_limit)))
									new_power_limit = max(float(gpu.power_limit) - power_delta_dec, float(gpu.default_power_limit * 0.5))

									process = subprocess.Popen("nvidia-smi.exe -i {} -pl {}".format(device_id, new_power_limit), stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell=True)
									output, error = process.communicate()
									print("GPU #{}: Power Reduced: {}".format(gpu.gid, output))
									gpu.power_limit = str(int(new_power_limit))
									sheet.update_acell('R' + str(row_start + idx), '=image("{}",4,15,15)'.format(down_icon_img_url))

								else:
									print("GPU #{}: Temperature is Too High, However Already Hit Power Limit LB.	\
									Current Power Limit = {} W, Power Limit LB = {} W".format(gpu.gid, gpu.power_limit, pw_limit_lb * float(gpu.default_power_limit)))
									sheet.update_acell('R' + str(row_start + idx), '=image("{}",4,15,15)'.format(stable_icon_img_url))


							if gpu.temp_curr < temperature_ub and \
								gpu.temp_curr >= temperature_lb:
								print("GPU #{}: Temperatur is Alright, No Change on Power.".format(gpu.gid))
								sheet.update_acell('R' + str(row_start + idx), '=image("{}",4,15,15)'.format(stable_icon_img_url))

		cell_list[6].value = float(gpu.power_limit)*1.0/float(gpu.default_power_limit)
		cell_list[12].value = int(gpu.power_limit)

		# Send update in batch mode
		print("Start Sync to gspread")
		sheet.update_cells(cell_list)


def main():
	miner_id = sys.argv[1]
	interval = int(sys.argv[2])
	print("This is Miner: {}".format(miner_id))

	if len(sys.argv) == 4 and sys.argv[3] == "debug":
		DEBUG = True
	else:
		DEBUG = False

	# if DEBUG:
	gpu_monitor(miner_id, DEBUG)


main()
