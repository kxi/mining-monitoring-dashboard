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
		self.power_ai = None

def nvidia_smi_call(DEBUG = False):

	gpu_dict = dict()

	prev_line = None
	process = subprocess.Popen("nvidia-smi.exe -a", stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell=True)
	output, error = process.communicate()

	gpu_index = 1

	for line in output.splitlines():
		line = line.decode()

		if "GPU 00000000" in line:
			gid = int(line.split(':')[1])
			gpu_dict[gid] = GPU()
			gpu_dict[gid].gid = gpu_index
			print("Found GPU: #{}".format(gpu_dict[gid].gid))
			gpu_index += 1

		if "Product Name" in line:
			model = line.split(':')[1].replace("GeForce", "").strip(" ")
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
			power_draw = line.split(':')[1].strip('W').strip()
			if DEBUG:
				print(power_draw)
			gpu_dict[gid].power_draw = float(power_draw)

		if "Enforced Power Limit" == line.split(':')[0].strip():
			power_limit = line.split(':')[1].strip('W').strip()
			if DEBUG:
				print(power_limit)
			gpu_dict[gid].power_limit = float(power_limit)

		if "Default Power Limit" == line.split(':')[0].strip():
			default_power_limit = line.split(':')[1].strip('W').strip()
			if DEBUG:
				print(default_power_limit)
			gpu_dict[gid].default_power_limit = float(default_power_limit)

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


def check_miner(DEBUG):

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
			miner = "EWBF(Equihash)"

		if "zm.exe" in line:
			miner_process_count += 1
			if DEBUG:
				print("DSTM Equihash Miner")
			miner = "DSTM(Equihash)"

		if "ccminer" in line:
			miner_process_count += 1
			if DEBUG:
				print("CC Miner")
			miner = "CC Miner"

		if "excavator" in line:
			miner_process_count += 1
			if DEBUG:
				print("Excavator(Nicehash)")
			miner = "Excavator(Nicehash)"

		if "Claymore" in line:
			miner_process_count += 1
			if DEBUG:
				print("Claymore")
			miner = "Claymore Dual Miner"


	if miner_process_count == 0:
		if DEBUG:
			print("No Miner is Running")
		miner = "Not Running"

	return miner


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
    	'miner3': 24,
    	'miner4': 31,
    	'miner5': 41,
    	'miner6': 50,
    	'kai_test_miner': 54
	}


	gpu_dict = nvidia_smi_call(DEBUG)
	# gpu_dict = nvidia_smi_call_stub()



	# use creds to create a client to interact with the Google Drive API
	scope = ['https://spreadsheets.google.com/feeds']
	creds = ServiceAccountCredentials.from_json_keyfile_name('key.json', scope)
	gc = gspread.authorize(creds)
	# Find a workbook by name and open the first sheet
	# Make sure you use the right name here.
	sheet = gc.open_by_url("https://docs.google.com/spreadsheets/d/1EwzqCCLXVznobht-8LG-sDWapaLlLrzn6jlsLcRyJnI").sheet1
	dt_now = datetime.now().strftime('%Y-%m-%d %H:%M')


	# Miner Type
	miner = check_miner(DEBUG)
	row_start =miner_row_start[miner_id]
	miner_range_build = 'A' + str(row_start) + ':' + 'A' + str(row_start)
	cell_list = sheet.range(miner_range_build)
	cell_list[0].value = miner
	sheet.update_cells(cell_list)


	# Script Run Time
	row_start = sheet_row_start[miner_id]
	range_build = 'L' + str(row_start) + ':' + 'L' + str(row_start)
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
#		cell_list[8].value = gpu.power_limit
		cell_list[9].value = gpu.default_power_limit


		# Smart Power Logic
		ENABLE_SMART_POWER_FLAG = sheet.acell('S' + str(row_start  + idx)).value

		# IF Power AI Strategy is Enabled
		if ENABLE_SMART_POWER_FLAG == "Y":
			print("GPU #{}: Smart Power Enabled, Check and Adjust Power if Necessary!".format(gpu.gid))

			device_id = gpu.gid - 1

			if gpu.utilization < 0.3:
				print("GPU #{}: GPU is Not Mining, Don't Adjust Power".format(gpu.gid))

			temperature_lb = int(sheet.acell('O' + str(row_start + idx)).value)
			temperature_ub = int(sheet.acell('P' + str(row_start + idx)).value)
			raw_pw_limit_lb_str = sheet.acell('Q' + str(row_start + idx)).value
			raw_pw_limit_ub_str = sheet.acell('R' + str(row_start + idx)).value

			if '%' in raw_pw_limit_lb_str:
				pw_limit_lb = float(raw_pw_limit_lb_str.strip('%'))/100.0
			else:
				pw_limit_lb = float(raw_pw_limit_lb_str)

			if '%' in raw_pw_limit_ub_str:
				pw_limit_ub = float(raw_pw_limit_ub_str.strip('%'))/100.0
			else:
				pw_limit_ub = float(raw_pw_limit_ub_str)

			# Just in Case, Wrong Value in Spreadsheet
			if temperature_lb > 67 or pw_limit_lb < 0.5 or pw_limit_ub > 0.9:
				print("GPU #{}: Smart Power Value is Not Reasonable, Please Check Spreadsheet".format(gpu.gid))
				pass


			power_delta_inc = int(gpu.default_power_limit * 0.02)
			power_delta_dec = int(gpu.default_power_limit * 0.03)


			if gpu.temp_curr < temperature_lb:
				if gpu.power_limit <= pw_limit_ub * float(gpu.default_power_limit):
					print("GPU #{}: Temperature is Too Low, Power Up. \
					 Current Power Limit = {} W, Power Limit UB = {} W".format(gpu.gid, gpu.power_limit, pw_limit_ub * float(gpu.default_power_limit)))
					new_power_limit = min(int(gpu.power_limit) + power_delta_inc, gpu.default_power_limit)

					process = subprocess.Popen("nvidia-smi.exe -i {} -pl {}".format(device_id, new_power_limit), stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell=True)
					output, error = process.communicate()
					print("GPU #{}: Power Increased: {}".format(gpu.gid, output))

					sheet.update_acell('N' + str(row_start + idx), '=image("https://lh3.googleusercontent.com/DXCOc9NZQ_aYEt6wDp0xOQU76xxVajegVFSWikuZg7vxF34zeFtQSauE7e06yTdt0eMhyWq0HTJ9g_4vcgI2DFMcRtZW24sKyUBMy4InoafJiE9xr-MpG4IWlbXOfbHUeNnNkmIMfqTTIuiz5xJhw-QhoaB4Huh8CPnZlIiBk30e2Vz09p7MdLdiBLgoEGGqhXp6a3XQyVK_l4kVlR1PJ1hw0qanPmvhu-C3bn_l1yrxlMNZnaOsm5JFLGIYrRgrJOYrUDMYZ-MB2CS14SPfE0KkdVS04673SHoy8c7r9CZjGCirTvEmr2tPPM-PVv8ZwMZrZt5nuRJrrr3VsV6Gibl1hyFCXoLz-h4XpqJVJ_67mTpIY-VWosB73dxZDXdEHeg5g2sr6SwMgb2HslFK597QGYpSEOrIQdtYHie8Xhe-Ws_xRy5OhvAShTWkej9Y-KmVrcAKw1QxG_jf0iDSbznLb7qwjZwqplYi9iAex1QwN0gcW7F4LcfTqMQhXFsjJssfyyD7qtadUjeVzzap6FNAVwk_hUuagU1CTjD8-7PYBTe8etmduBN78Ia2MNvyWlx6ivDN67UEv3O__nB_xad_3h4WwS2-PMCILT4=w94-h125-no",4,15,15)')

					gpu.power_limit = str(new_power_limit)


				else:
					print("GPU #{}: Temperature is Too Low, However Already Hit Power Limit UB. \
					  Current Power Limit = {} W, Power Limit UB = {} W".format(gpu.gid, gpu.power_limit, pw_limit_ub * float(gpu.default_power_limit)))

					sheet.update_acell('N' + str(row_start + idx), '=image("https://lh3.googleusercontent.com/YLDGZwvCqW5FocPEvAWEubrcJcie79_YQSXGs5mt4-LRpTg6Wtxyzbuqjka2FgS-IhOZr9GWHbKwVJVwLWimCPAIgPfCDPxX--sSmGnaMncp78AmWbDpQiecLa3G01kWlIFwDSagy6QE_dzs5fnr6CV6owsDQ_-rVnHlRorRy_JrUbA3oGsRDk-T5-h0C3RPpzleubA1q1xXzjmERgu4J1A7hExFB8TimZthmLj_QwMlP5VN6gg50nyhIRmsjYWZLChAVZRAo7IXt3ajaQavYldsSbiAdhpEbZmpiAvXUbPjzaCCSLFAZ_Jo1sDtdPDcLiflLUHRi_J9cnESvjU60Tb2YO8r1SZ7k1ikRswNE8917zph-JiOWqhAuBHDRTAA6-gwtDLy-SUEDTzBv9m2Kn0bh1IiWUdLCApSczAaVY9pB3gqgSkvju1dmf2gfOhNxEv58mc5R35CT4hIeO5HdmFZ48E_3jzD-JBXwBF_UQmff_x3fXqV7pDbv26d0L0StZTGab1QDtR_z_rON01PxmPYeWz9_cBCHUCBhh3HKB65xug9hl4oguXwEahsu8mLlTCg68-E9MFFkG4jLgqaUrnAzXqGiA_RwEw6DuQ=w124-h93-no",4,15,15)')



			if gpu.temp_curr >= temperature_ub:
				if gpu.power_limit > pw_limit_lb * float(gpu.default_power_limit):
					print("GPU #{}: Temperature is Too High, Power Down. \
					 Current Power Limit = {} W, Power Limit LB = {} W".format(gpu.gid, gpu.power_limit, pw_limit_lb * float(gpu.default_power_limit)))
					new_power_limit = max(int(gpu.power_limit) - power_delta_dec, int(gpu.default_power_limit * 0.5))

					process = subprocess.Popen("nvidia-smi.exe -i {} -pl {}".format(device_id, new_power_limit), stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell=True)
					output, error = process.communicate()
					print("GPU #{}: Power Reduced: {}".format(gpu.gid, output))
					gpu.power_limit = str(new_power_limit)
					sheet.update_acell('N' + str(row_start + idx), '=image("https://lh3.googleusercontent.com/ol3MTFbh2r4KeFwOt3lQ_5b-QKtPGgEwmuaHpHJ5988OvVKskhto-sJL8MNtdmzWI_YwJFx3CKoaW7ies7umXIVqhfjxe6ZQxcna8aPyvf8DMyZlvkx67hVQ_c6y30h_yIJWb3K0uM_pDOXtpIBcOs_Edt0U3JafEpP-DMCQ_j46oVXV1VpMVggCRTh3kXExj-Hb9OwZW9FVrl7hcGFSXog1UKF0VnlGpUumOLEaWEHg8PUVjwJiXeJvWQ9ibkEtPwpAGcDvDvLLL0UhZtX9b3OiwVVDi2Rge7fbWoAcXJ2ozl_1wdfcIJ68n1k8vp-u_yUWOFyV8qBdpmnK3ekH9Pz4ljgrkCuwmcjNZg63n3g_3BLQ1wGSVP6e6Bez9ZLZGPg80yQUv-Z-hHTMIVZtV1Wrp-0WcXDLk44Rvle6Lct_UVp2wXje_gaMEbHxjCqXTfrVEeMxQGTPpB8MILAawdz238ctD6g9GIJZemgnabsV3XcgeqLC3AaIUVyBwAgprHxk64H2FNrZQQs5xLEr0gHsnStWV2uorIsKAMj7-RykE-DB6VQWqWLBTrUb8AKL0kw4cE-392R1hDgHNBjmSqeDAmCdidyk9a_tqCk=w94-h128-no",4,15,15)')



				else:
					print("GPU #{}: Temperature is Too High, However Already Hit Power Limit LB.	\
					Current Power Limit = {} W, Power Limit LB = {} W".format(gpu.gid, gpu.power_limit, pw_limit_lb * float(gpu.default_power_limit)))
					sheet.update_acell('N' + str(row_start + idx), '=image("https://lh3.googleusercontent.com/YLDGZwvCqW5FocPEvAWEubrcJcie79_YQSXGs5mt4-LRpTg6Wtxyzbuqjka2FgS-IhOZr9GWHbKwVJVwLWimCPAIgPfCDPxX--sSmGnaMncp78AmWbDpQiecLa3G01kWlIFwDSagy6QE_dzs5fnr6CV6owsDQ_-rVnHlRorRy_JrUbA3oGsRDk-T5-h0C3RPpzleubA1q1xXzjmERgu4J1A7hExFB8TimZthmLj_QwMlP5VN6gg50nyhIRmsjYWZLChAVZRAo7IXt3ajaQavYldsSbiAdhpEbZmpiAvXUbPjzaCCSLFAZ_Jo1sDtdPDcLiflLUHRi_J9cnESvjU60Tb2YO8r1SZ7k1ikRswNE8917zph-JiOWqhAuBHDRTAA6-gwtDLy-SUEDTzBv9m2Kn0bh1IiWUdLCApSczAaVY9pB3gqgSkvju1dmf2gfOhNxEv58mc5R35CT4hIeO5HdmFZ48E_3jzD-JBXwBF_UQmff_x3fXqV7pDbv26d0L0StZTGab1QDtR_z_rON01PxmPYeWz9_cBCHUCBhh3HKB65xug9hl4oguXwEahsu8mLlTCg68-E9MFFkG4jLgqaUrnAzXqGiA_RwEw6DuQ=w124-h93-no",4,15,15)')



			if gpu.temp_curr < temperature_ub and \
				gpu.temp_curr > temperature_lb:
				print("GPU #{}: Temperatur is Alright, No Change on Power.".format(gpu.gid))
				sheet.update_acell('N' + str(row_start + idx), '=image("https://lh3.googleusercontent.com/YLDGZwvCqW5FocPEvAWEubrcJcie79_YQSXGs5mt4-LRpTg6Wtxyzbuqjka2FgS-IhOZr9GWHbKwVJVwLWimCPAIgPfCDPxX--sSmGnaMncp78AmWbDpQiecLa3G01kWlIFwDSagy6QE_dzs5fnr6CV6owsDQ_-rVnHlRorRy_JrUbA3oGsRDk-T5-h0C3RPpzleubA1q1xXzjmERgu4J1A7hExFB8TimZthmLj_QwMlP5VN6gg50nyhIRmsjYWZLChAVZRAo7IXt3ajaQavYldsSbiAdhpEbZmpiAvXUbPjzaCCSLFAZ_Jo1sDtdPDcLiflLUHRi_J9cnESvjU60Tb2YO8r1SZ7k1ikRswNE8917zph-JiOWqhAuBHDRTAA6-gwtDLy-SUEDTzBv9m2Kn0bh1IiWUdLCApSczAaVY9pB3gqgSkvju1dmf2gfOhNxEv58mc5R35CT4hIeO5HdmFZ48E_3jzD-JBXwBF_UQmff_x3fXqV7pDbv26d0L0StZTGab1QDtR_z_rON01PxmPYeWz9_cBCHUCBhh3HKB65xug9hl4oguXwEahsu8mLlTCg68-E9MFFkG4jLgqaUrnAzXqGiA_RwEw6DuQ=w124-h93-no",4,15,15)')

		cell_list[3].value = float(gpu.power_limit)*1.0/float(gpu.default_power_limit)
		cell_list[8].value = gpu.power_limit

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

	if DEBUG:
		gpu_monitor(miner_id, DEBUG)

	while 1:
		try:
			gpu_monitor(miner_id, DEBUG)
		except Exception as e:
			print(e)
			pass

		time.sleep(interval)

main()
