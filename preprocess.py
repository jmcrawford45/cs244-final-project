import glob
import json

DATA_RE = '*-stek.json'
USED = ['server_hello', 'session_ticket']

with open('all-steks.json', 'w') as out:
	for f in sorted(glob.glob(DATA_RE), reverse=True):
			seen = set()
			with open(f) as data:
				for raw in data:
					entry = json.loads(raw)
					remove = list()
					server_hello_remove = list()
					if 'data' in entry and 'tls' in entry['data']:
						for step in entry['data']['tls']:
							if step not in USED:
								remove.append(step)
							elif step == 'server_hello':
								for field in entry['data']['tls']['server_hello']:
									if field != 'session_id':
										server_hello_remove.append(field)
					for step in remove:
						del entry['data']['tls'][step]
					for field in server_hello_remove:
						del entry['data']['tls']['server_hello'][field]
					out.write(json.dumps(entry) + '\n')
