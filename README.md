# CS244-final-project - TLS Shortcuts Reproduction

### Setup Instructions
- Open a VM instance in Google Cloud Platform Console (I used 1 CPU
and 1TB boot disk, default for everything else.)
- Install dependencies (build essentials, pip, GO env, and zgrab) as follows
```
git clone https://github.com/jmcrawford45/cs244-final-project
cd cs244-final-project
sudo sh setup.sh
```
### Running your own scan
To start a scan of the top 1 million websites in the background, simply run
```
nohup ./gather_stek &
```
from the project directory.
You should see a *-stek.json file being gradually populated with TLS traffic.

### Fetch data used for analysis
To fetch verbose transcripts of all TLS handshakes attempted 
*WARNING: TOTAL UNCOMPRESSED FILE SIZE >100GB*
```
gsutil cp gs://cs244-jared13-tls-crypto/*-stek.json.lz4 ./
```
To fetch a summary of the TLS handshakes used in analysis (<10 GB)
```
gsutil cp gs://cs244-jared13-tls-crypto/all-steks.json.lz4 ./
```

### Acknowledgements
This project is a reproduction of the key findings from [Measuring the Security Harm of TLS Crypto Shortcuts](https://jhalderm.com/pub/papers/forward-secrecy-imc16.pdf).
The application layer scanning is accomplished with the [ZGrab](https://github.com/zmap/zgrab) tool.
To avoid redundant queries, the Censys Alexa Top 1 Million Download and Lookups  [dataset](https://scans.io/series/alexa-dl-top1mil) is used as an authoritative source for the
A records of Alexa Top 1 Million sites.
