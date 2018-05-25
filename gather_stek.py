import os
import datetime

date = datetime.datetime.now().strftime('%Y%m%d')
os.system('python parser.py | ~/go/bin/zgrab --port 443 --timeout 10 --senders 50 --ca-file=cacert.pem --tls --output-file={}-stek.json --tls-verbose --tls-session-ticket'.format(date))
