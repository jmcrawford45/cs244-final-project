import time
DEBUG = False

DATA_SET_URL = 'https://scans.io/series/alexa-dl-top1mil'
DATA_BASE_URL = 'https://scans.io/zsearch/'
COMPRESSION_EXT = '.lz4'
HASH_FILE = 'known_hashes.txt'

# Extract the session key identifier if possible from the ticket
def extractStek(ticket):
    pass

def getKnownHashes():
    with open(HASH_FILE, 'a+') as f:
        f.seek(0)
        return [l.split(',')[0] for l in f.readlines()]

def recordHash(h, name):
    with open(HASH_FILE, 'a') as f:
        f.write('{},{}\n'.format(h, name))

def getScansIOFile(all_days, local_name):
    now = datetime.datetime.now()
    s = now.strftime('%Y%m%d')
    match_re =  local_name.format('*')
    #Cache for debug
    matches = sorted(glob.glob(match_re), reverse=True)
    file_re = '({}.*?-{}{})'.format(DATA_BASE_URL, all_days, COMPRESSION_EXT)
    hash_re = '.*?<code>(.*?)</code>'
    resource_re = re.compile('{}{}'.format(file_re, hash_re), re.DOTALL)
    response = requests.get(DATA_SET_URL).content
    m = resource_re.search(response)
    if m and m.groups()[1] not in getKnownHashes():
        debug('Fetching: {}'.format(m.groups()[0]))
        file_name = wget.download(m.groups()[0])
        new_name = local_name.format(s)
        call(['/usr/local/bin/unlz4', file_name, new_name])
        recordHash(m.groups()[1], m.groups()[0])
        return new_name
    return matches[0]


def getARecords():
    return getScansIOFile('alexa-top1m-a-zgrab.*?.csv', '{}-alexa-top1m-a-zgrab.csv')

# Return a map from IP to rank
def getSiteRankings():
    rank_file = getScansIOFile('alexa-top1m-www-alookups.*?.json', '{}-alexa-top1m-www-alookups.json')
    res = defaultdict(lambda: 1000000)
    with open(rank_file) as ranks:
        for raw in ranks:
            entry = json.loads(raw)
            if 'alexa_rank' in entry:
                rank = entry['alexa_rank']
                if 'altered_name' in entry:
                    res[entry['altered_name']] = rank
                if 'name' in entry:
                    res[entry['name']] = rank
                if 'ipv4_addresses' in entry['data']:
                    for addr in entry['ipv4_addresses']:
                        res[addr] = rank 
    return res 

    

def debug(s):
	if DEBUG:
		print s

def RateLimited(maxPerSecond):
    minInterval = 1.0 / float(maxPerSecond)
    def decorate(func):
        lastTimeCalled = [0.0]
        def rateLimitedFunction(*args,**kargs):
            elapsed = time.clock() - lastTimeCalled[0]
            leftToWait = minInterval - elapsed
            if leftToWait>0:
                time.sleep(leftToWait)
            ret = func(*args,**kargs)
            lastTimeCalled[0] = time.clock()
            return ret
        return rateLimitedFunction
    return decorate