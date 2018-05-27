import os
import datetime

date = datetime.datetime.now().strftime('%Y%m%d')
os.system('cat whitelist.txt | ~/go/bin/zgrab --port 443 --timeout 30 --senders 100 --ca-file=cacert.pem --tls --output-file={}-stek.json --tls-session-ticket --tls-verbose'.format(date))
