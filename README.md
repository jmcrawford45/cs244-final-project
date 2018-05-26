# CS244-final-project - TLS Shortcuts Reproduction

### Setup Instructions
- Open a VM instance in Google Cloud Platform Console (I used 1 CPU
and 1TB boot disk, default for everything else.)
- Install dependencies (build essentials, pip, GO env, and zgrab) as follows
```
git clone https://github.com/jmcrawford45/cs244-final-project
cd cs244-final-project
sudo setup.sh
```
### Running your own scan
To start a scan of the top 1 million websites in the background, simply run
```
nohup ./gather_stek &
```
from the project directory.
You should see a *-stek.json file being gradually populated with TLS traffic.

### Acknowledgements
This project is a reproduction of the key findings from [Measuring the Security Harm of TLS Crypto Shortcuts](https://jhalderm.com/pub/papers/forward-secrecy-imc16.pdf).
The application layer scanning is accomplished with the [ZGrab](https://github.com/zmap/zgrab) tool.
To avoid redundant queries, the Censys Alexa Top 1 Million Download and Lookups  [dataset](https://scans.io/series/alexa-dl-top1mil) is used as an authoritative source for the
A records of Alexa Top 1 Million sites.
