# crawl_marketo_forms

Crawl a website's pages based on its sitemap.xml and find Marketo forms.
Written using [Python](https://www.python.org) and [Scrapy](https://scrapy.org/).

## Installation

### Windows

Download the latest release from [Latest Release](https://github.com/george-cm/marketo-forms-crawler/releases/latest)
Unzip the archive in your desired folder.

## From source

Clone the repo:

```sh
git clone https://github.com/george-cm/marketo-forms-crawler.git
cd marketo-forms-crawler
```

Create a virtual environment:

```sh
python -m venv .venv
```

Activate the virtual environment:

- Linux and MacOS

```sh
source .venv/bin/activate
```

- Windows PowerShell

```PowerShell
.\.venv\Scripts\activate.ps1
```

- Windows cmd.exe

```cmd.exe
.venv\Scripts\activate.bat
```

Install dependencies:

```sh
python -m pip install -r requirements.txt
```

## Usage

### On Windows

```sh
crawl_marketo_forms.exe [-h] [--append] [--version] [--noautothrottle] [--autothrottlemaxdelay ATHROTTLEMAXDELAY] [--logfile LOGFILE] [--loglevel {DEBUG,INFO,WARNING,ERROR,CRITICAL}] [--logappend] url output

Crawl links from a sitemap.xml url and extract Marketo form ids.

positional arguments:
  url                   URL of sitemap
  output                CSV output file.

options:
  -h, --help            show this help message and exit
  --append, -a          append to CSV file. Otherwise, overwrite.
  --version, -V         show program's version number and exit
  --noautothrottle, -na
                        disable autothrottle. The software will crawl faster, but may be blocked by the website server.
  --autothrottlemaxdelay ATHROTTLEMAXDELAY, -amd ATHROTTLEMAXDELAY
                        set the maximum delay between requests. Default is 60.
  --logfile LOGFILE, -lf LOGFILE
                        log file
  --loglevel {DEBUG,INFO,WARNING,ERROR,CRITICAL}, -ll {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        log level. Default: DEBUG
  --logappend, -la      append to log file instead of overwriting.
```

### On Linux and MacOS

```sh
python .\crawl_marketo_forms.py [-h] [--append] [--version] [--noautothrottle] [--autothrottlemaxdelay ATHROTTLEMAXDELAY] [--logfile LOGFILE] [--loglevel {DEBUG,INFO,WARNING,ERROR,CRITICAL}] [--logappend] url output

Crawl links from a sitemap.xml url and extract Marketo form ids.

positional arguments:
  url                   URL of sitemap
  output                CSV output file.

options:
  -h, --help            show this help message and exit
  --append, -a          append to CSV file. Otherwise, overwrite.
  --version, -V         show program's version number and exit
  --noautothrottle, -na
                        disable autothrottle. The software will crawl faster, but may be blocked by the website server.
  --autothrottlemaxdelay ATHROTTLEMAXDELAY, -amd ATHROTTLEMAXDELAY
                        set the maximum delay between requests. Default is 60.
  --logfile LOGFILE, -lf LOGFILE
                        log file
  --loglevel {DEBUG,INFO,WARNING,ERROR,CRITICAL}, -ll {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        log level. Default: DEBUG
  --logappend, -la      append to log file instead of overwriting.
```
