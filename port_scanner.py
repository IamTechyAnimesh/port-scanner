import argparse
import socket
import ipaddress
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

# Common ports
TOP_PORTS = [21, 22, 23, 25, 53, 67, 68, 80, 110, 111, 123, 135, 139, 143, 161, 179, 389, 443, 445, 465, 514, 587, 993, 995, 1433, 1521, 2049, 3306, 3389, 8080, 8443]

def parse_ports(ports_str):
    ports = set()
    parts = ports_str.split(',')
    
    for p in parts:
        p = p.strip()
        if not p:
            continue
        
        try:
            if p.lower() == 'top':
                ports.update(TOP_PORTS)
            elif '-' in p:
                start, end = p.split('-', 1)
                start_port = int(start.strip())
                end_port = int(end.strip())
                if 1 <= start_port <= 65535 and 1 <= end_port <= 65535 and start_port <= end_port:
                    ports.update(range(start_port, end_port + 1))
            else:
                port = int(p)
                if 1 <= port <= 65535:
                    ports.add(port)
        except ValueError:
            print(f"Warning: Invalid port '{p}', skipping")
            continue
    
    return sorted(ports)

def expand_targets(target_str):
    targets = []
    target_str = target_str.strip()
    
    if '/' in target_str:
        try:
            net = ipaddress.ip_network(target_str, strict=False)
            targets = [str(ip) for ip in net.hosts()]
            if targets:
                return targets
        except ValueError:
            pass
    
    if '-' in target_str:
        try:
            start, end = target_str.split('-', 1)
            start_ip = ipaddress.ip_address(start.strip())
            end_ip = ipaddress.ip_address(end.strip())
            
            if start_ip.version == 4 and end_ip.version == 4:
                s = int(start_ip)
                e = int(end_ip)
                if s <= e:
                    targets = [str(ipaddress.ip_address(i)) for i in range(s, e + 1)]
                    return targets
        except ValueError:
            pass
    
    try:
        resolved = socket.gethostbyname(target_str)
        return [resolved]
    except socket.gaierror:
        return [target_str]

def scan_port(host, port, timeout=1.0, banner_len=1024):
    result = {
        'host': host,
        'port': port,
        'open': False,
        'banner': None,
        'error': None,
    }
    
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            rc = s.connect_ex((host, port))
            
            if rc == 0:
                result['open'] = True
                
                try:
                    s.settimeout(0.5)
                    data = s.recv(banner_len)
                    if data:
                        decoded = data.decode(errors='ignore')
                        printable = ''.join(c for c in decoded if ord(c) >= 32 and ord(c) < 127 or c == '\n')
                        printable = printable.strip().split('\n')[0]
                        if printable:
                            result['banner'] = printable[:80]
                except (socket.timeout, OSError):
                    pass
            else:
                result['open'] = False
    except Exception as e:
        result['error'] = str(e)
    
    return result

def main():
    parser = argparse.ArgumentParser(description="Multithreaded TCP port scanner")
    parser.add_argument('target', help='Target: hostname/IP, CIDR (e.g., 192.168.1.0/24), or range (e.g., 192.168.1.1-192.168.1.20)')
    parser.add_argument('-p', '--ports', default='1-1024', help='Ports: single (22), comma-separated (22,80), range (1-1024), or "top" for common ports. Default: 1-1024')
    parser.add_argument('-t', '--threads', type=int, default=200, help='Number of worker threads (default: 200)')
    parser.add_argument('--timeout', type=float, default=0.8, help='Socket connect timeout in seconds (default: 0.8)')
    parser.add_argument('--banner-len', type=int, default=1024, help='Bytes to read for banner grabbing (default: 1024)')
    parser.add_argument('--json', type=str, metavar='FILE', const='-', nargs='?', help='Save results to JSON file (or "-" for stdout)')
    parser.add_argument('--quiet', action='store_true', help='Suppress the pretty terminal summary')
    args = parser.parse_args()

    targets = expand_targets(args.target)
    if not targets:
        print("Error: No valid targets found")
        return
    
    ports = parse_ports(args.ports)
    if not ports:
        print("Error: No valid ports specified")
        return
    
    total_tasks = len(targets) * len(ports)

    if not args.quiet:
        print(f"Targets: {len(targets)} -> {targets[:5]}{'...' if len(targets) > 5 else ''}")
        print(f"Ports: {len(ports)} -> {ports[:10]}{'...' if len(ports) > 10 else ''}")
        print(f"Total scans: {total_tasks}, Threads: {args.threads}, Timeout: {args.timeout}s")
    
    start = datetime.now(timezone.utc)
    results = []
    
    with ThreadPoolExecutor(max_workers=args.threads) as ex:
        futures = []
        for host in targets:
            for port in ports:
                futures.append(ex.submit(scan_port, host, port, args.timeout, args.banner_len))
        
        for fut in as_completed(futures):
            try:
                r = fut.result()
                if r['open'] and not args.quiet:
                    banner_str = f" -> {r['banner']}" if r['banner'] else ""
                    print(f"[OPEN] {r['host']}:{r['port']}{banner_str}")
                results.append(r)
            except Exception as e:
                print(f"Error: {e}")

    duration = (datetime.now(timezone.utc) - start).total_seconds()
    open_ports = [r for r in results if r['open']]

    # ======================
    # Build compact JSON output
    # ======================
    output = {
        "scan_start": start.isoformat(),
        "scan_end": datetime.now(timezone.utc).isoformat(),
        "duration_seconds": round(duration, 3),
        
         "config": {
            "target_input": args.target,          
            "ports_input": args.ports,            
            "target_count": len(targets),
            "ports_count": len(ports),
            "total_scans": total_tasks,
            "threads": args.threads,
            "timeout": args.timeout,
            "banner_grab": args.banner_len > 0
        },

        "summary": {
            "open_ports_found": len(open_ports),
            "closed_or_filtered": total_tasks - len(open_ports)
        },

        "findings": open_ports
   
    }

    # ======================
    # Save JSON if requested
    # ======================

    if args.json:
        json_output = json.dumps(output, indent=2)
        if args.json == "-":
            print(json_output)
        else:
            with open(args.json, "w", encoding="utf-8") as f:
                f.write(json_output)
            print(f"[+] Full JSON report saved → {args.json}")

    # ======================
    # Pretty terminal output (always shown unless --quiet)
    # ======================

    if not args.quiet:
        print("=" * 65)
        print("PORT SCAN RESULTS".center(65))
        print("=" * 65)
        print(f"Scan Duration: {duration:.2f} seconds")
        print(f"Targets: {len(targets)}")
        print(f"Ports Checked: {len(ports)}")
        print(f"Total Scans: {total_tasks}")
        print(f"Open Ports Found: {len(open_ports)}")
        print("=" * 65)
    
        if open_ports:
            print("\nOPEN PORTS:")
            for result in sorted(open_ports, key=lambda x: (x['host'], x['port'])):
                banner_info = f" | {result['banner']}" if result['banner'] else ""
                print(f"  {result['host']:15} : {result['port']:5d}{banner_info}")
        else:
            print("\nNo open ports found.")
        print()

if __name__ == '__main__':
    main()
