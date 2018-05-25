import os
import datetime

date = datetime.datetime.now().strftime('%Y%m%d')
os.system('python parser.py | /usr/local/sbin/zgrab --port 443 --tls --output-file={}-stek.json --tls-verbose --tls-session-ticket'.format(date))
