from pynput.keyboard import Key, Listener
from datetime import date
import json
import requests
import threading

DISTRIBUTION_FILE = 'distribution.json'
TIME_FILE = 'time.json'
CONVERT_FILE = 'convert.json'
REQUEST_URL = 'http://127.0.0.1:5000/new-data'
SAVE_COUNTER = 10

current_date = ''
time = {}
dist = {}
ignore = ['shift', 'shift_r', 'ctrl_l', 'ctrl_r', 'alt_l', 'alt_gr', 'backspace', 'delete', 'right', 'down', 'left', 'up']
counter = 0
last_key = ''

def prefix():
	return '[Listener]'


def load():
	global dist, time
	try:
		with open(DISTRIBUTION_FILE, 'r') as f:
			dist = json.load(f)
		with open(TIME_FILE, 'r') as f:
			time = json.load(f)
		# with open(CONVERT_FILE, 'r') as f:
		# 	convert = json.load(f)
	except Exception as e:
		print(prefix(), 'Could not load files')
		print(prefix(), 'Exception:', e)


def save(dist, time):
	try:
		with open(DISTRIBUTION_FILE, 'w') as f:
			json.dump(dist, f)
		with open(TIME_FILE, 'w') as f:
			json.dump(time, f)
	except Exception as e:
		print(prefix(), 'Could not load files')
		print(prefix(), 'Exception:', e)


def check_date(current_date):
	global dist
	temp_date = str(date.today().strftime('%d.%m.%Y'))
	if temp_date == current_date:
		return current_date
	if current_date == '':
		if len(list(time)) != 0:
			return str(list(time)[-1])
	time[temp_date] = 0
	dist = {}
	return temp_date


def count_keystrokes(dist):
	c = 0
	for key in dist:
		c += dist[key]
	return c


def on_press(key):
	global counter, current_date, last_key
	current_date = check_date(current_date)
	key = str(key)
	old = key
	ext = False

	if key.startswith('Key.'):
		key = key.split('.')[1]
	elif key.startswith('\'\\x'):
		key = key.replace('\'\\', '').replace('\'', '')
	elif key.startswith('<'):
		try:
			n = int(key.replace('<', '').replace('>', ''))
			if n > 47 and n < 97:
				key = 'ctrl+alt+' + chr(n)
				if key == 'ctrl+alt+A':
					print('Exit due to CTRL+ALT+A')
					ext = True
			else:
				key = 'ctrl+alt+' + n
		except:
			key = 'ctrl+alt+' + key.replace('<', '').replace('>', '')
	else:
		key = key.replace('\'', '')

	if key == 'ä':
		key = 'ae'
	elif key == 'ö':
		key = 'oe'
	elif key == 'ü':
		key = 'ue'
	elif key == 'Ä':
		key = 'AE'
	elif key == 'Ö':
		key = 'OE'
	elif key == 'Ü':
		key = 'UE'
	elif key == 'ß':
		key = 'ss'

	key = key.replace('\\', '')

	print(old, '->', key)
	if key not in ignore:
		last_key = ''
		if key in dist:
			dist[key] += 1
		else:
			dist[key] = 1
	else:
		if last_key != key:
			last_key = key
			if key in dist:
				dist[key] += 1
			else:
				dist[key] = 1


	if ext:
		exit(0)

	thread = threading.Thread(target = send_request, args = [dist, time,])
	thread.start()

	counter += 1
	if counter >= SAVE_COUNTER:
		counter = 0
		time[current_date] = count_keystrokes(dist)
		save(dist, time)
		print(prefix(), 'dist saved:', count_keystrokes(dist), 'keystrokes')


def send_request(dist, time):
	try:
		requests.get(REQUEST_URL + '?distribution=' + str(dist).replace(' ', '').replace('\'', '%22') + '&time=' + str(time).replace(' ', '').replace('\'', '%22'))
	except:
		print("Server not running")


def start_logger():
	load()
	print(prefix(), 'Started key listener...')
	with Listener(on_press=on_press) as listener:
		listener.join()