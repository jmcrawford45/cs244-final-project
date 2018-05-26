import json
import glob
from collections import defaultdict

stats = defaultdict(int)

def exportStek():
	for f in glob.glob('*-stek.json'):
		with open(f) as data:
			for raw in data:
				entry = json.loads(raw)
				stats['total'] += 1
				if 'error' in entry and 'i/o timeout' in entry['error']:
					stats['timeout'] += 1
				elif 'error' in entry:
					stats['other error'] += 1
				elif 'session_ticket' in entry['data']['tls']:
					print entry['ip'], entry['data']['tls']['session_ticket']
					stats['session_ticket'] += 1
				elif 'session_id' in entry['data']['tls']['server_hello']:
					if entry['data']['tls']['server_hello']['session_id'] != "":
						stats['session_id'] += 1
	print stats


exportStek()