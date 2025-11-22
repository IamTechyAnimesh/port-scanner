# Port Scanner

A fast, multithreaded TCP port scanner with banner grabbing capabilities.

## Features

- **Multithreaded scanning** - Scan multiple ports simultaneously for fast results
- **Flexible target specification** - Support for single IPs, CIDR ranges, and IP ranges
- **Customizable port selection** - Scan specific ports, ranges, or common ports
- **Banner grabbing** - Automatically detect service banners
- **Clean output** - Easy-to-read results with clear formatting

## Installation

No special installation required. Just ensure you have Python 3.7+ installed.

```bash
python3 port_scan.py --help
```

## Usage

### Basic Usage

Scan a single host:

```bash
python3 port_scan.py 192.168.1.1
```

Scan a CIDR network:

```bash
python3 port_scan.py 192.168.1.0/24
```

Scan an IP range:

```bash
python3 port_scan.py 192.168.1.1-192.168.1.10
```

### Port Selection

Scan default ports (1-1024):

```bash
python3 port_scan.py 127.0.0.1
```

Scan common ports:

```bash
python3 port_scan.py 127.0.0.1 -p top
```

Scan specific ports:

```bash
python3 port_scan.py 127.0.0.1 -p 22,80,443,3306
```

Scan a port range:

```bash
python3 port_scan.py 127.0.0.1 -p 1-1000
```

Scan multiple ranges and ports:

```bash
python3 port_scan.py 127.0.0.1 -p 22,80,443,1000-2000
```

### Advanced Options

**Adjust number of threads** (default: 200):

```bash
python3 port_scan.py 192.168.1.0/24 -p top -t 100
```

**Change timeout** (default: 0.8 seconds):

```bash
python3 port_scan.py 127.0.0.1 --timeout 2.0 -p 1-10000
```

**Customize banner grab size** (default: 1024 bytes):

```bash
python3 port_scan.py 127.0.0.1 --banner-len 512
```

## Command Line Options

```
positional arguments:
  target                Target: hostname/IP, CIDR (e.g., 192.168.1.0/24), 
                        or range (e.g., 192.168.1.1-192.168.1.20)

optional arguments:
  -h, --help            Show help message
  
  -p, --ports PORTS     Ports to scan
                        - Single: 22
                        - Multiple: 22,80,443
                        - Range: 1-1024
                        - Common: top
                        Default: 1-1024

  -t, --threads THREADS Number of worker threads (default: 200)

  --timeout TIMEOUT     Socket connect timeout in seconds (default: 0.8)

  --banner-len LENGTH   Bytes to read for banner grabbing (default: 1024)
```

## Examples

### Example 1: Quick scan of local network

```bash
python3 port_scan.py 192.168.1.0/24 -p top -t 100
```

**Output:**
```
Targets: 254 -> ['192.168.1.1', '192.168.1.2', '192.168.1.3', '192.168.1.4', '192.168.1.5']...
Ports: 31 -> [21, 22, 23, 25, 53, 67, 68, 80, 110, 111]...
Total scans: 7874, Threads: 100, Timeout: 0.8s
[OPEN] 192.168.1.1:22 -> OpenSSH_7.4
[OPEN] 192.168.1.1:80 -> Apache/2.4.6
[OPEN] 192.168.1.5:3306 -> MySQL 5.7.25
=================================================================
                        PORT SCAN RESULTS
=================================================================
Scan Duration: 12.45 seconds
Targets: 254
Ports Checked: 31
Total Scans: 7874
Open Ports Found: 3
=================================================================

OPEN PORTS:
  192.168.1.1       :    22 | OpenSSH_7.4
  192.168.1.1       :    80 | Apache/2.4.6
  192.168.1.5       :  3306 | MySQL 5.7.25
```

### Example 2: Scan specific ports on a single host

```bash
python3 port_scan.py 127.0.0.1 -p 22,80,443,3306,5432,8080,8443
```

**Output:**
```
Targets: 1 -> ['127.0.0.1']
Ports: 7 -> [22, 80, 443, 3306, 5432, 8080, 8443]
Total scans: 7, Threads: 200, Timeout: 0.8s
[OPEN] 127.0.0.1:443
[OPEN] 127.0.0.1:3306 -> MySQL_8.0.32
=================================================================
                        PORT SCAN RESULTS
=================================================================
Scan Duration: 0.82 seconds
Targets: 1
Ports Checked: 7
Total Scans: 7
Open Ports Found: 2
=================================================================

OPEN PORTS:
  127.0.0.1       :   443
  127.0.0.1       :  3306 | MySQL_8.0.32
```

### Example 3: Deep scan with longer timeout

```bash
python3 port_scan.py 10.0.0.1-10.0.0.5 -p 1-10000 -t 50 --timeout 2.0
```

This scans 5 hosts across 10,000 ports each with 50 threads and 2-second timeout.

## Performance Tips

- **Increase threads** for faster scanning (e.g., `-t 500`)
- **Decrease timeout** for unreliable networks (e.g., `--timeout 0.5`)
- **Use port ranges** instead of `top` for more control
- **Reduce banner length** for faster results (e.g., `--banner-len 128`)

## Output Explanation

- **[OPEN]** - Port is open and accepting connections
- **-> Banner** - Service information detected on that port (if available)
- **Scan Duration** - Total time taken for the scan
- **Open Ports Found** - Count of responsive ports

## Supported Targets

- **Single IP**: `192.168.1.1`
- **Hostname**: `example.com` (will be resolved to IP)
- **CIDR Range**: `192.168.1.0/24`
- **IP Range**: `192.168.1.1-192.168.1.10`

## Troubleshooting

**No targets found:**
- Check that your target specification is valid
- Ensure CIDR notation is correct (e.g., `/24`)

**Slow scanning:**
- Increase threads: `-t 500`
- Decrease timeout: `--timeout 0.5`
- Reduce banner length: `--banner-len 128`

**Missing banners:**
- Some services don't send banners immediately
- Increase `--banner-len` if needed
- Banner grabbing is optional, results are valid either way

## License

Copyright (c) 2025 ANIMESH PANNA 

