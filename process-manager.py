import psutil
import time
import os
import argparse


def get_top_cpu_processes(sort_by='cpu', limit=5):
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']):
        try:
            proc_info = proc.info
            proc_info['cpu_percent'] = proc.cpu_percent()  # Non-blocking CPU usage
            processes.append(proc_info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    sorted_processes = sorted(processes, key=lambda x: x['cpu_percent'], reverse=True)
    print(f"Top {limit} processes sorted by CPU:")
    for proc in sorted_processes[:limit]:
        print(f"PID: {proc['pid']}, Name: {proc['name']}, CPU: {proc['cpu_percent']:.2f}%")
    print()


def get_top_mem_processes(sort_by='mem', limit=5):
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
        try:
            proc_info = proc.info
            processes.append(proc_info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    sorted_processes = sorted(processes, key=lambda x: x['memory_info'].rss, reverse=True)
    print(f"Top {limit} processes sorted by memory usage:")
    for proc in sorted_processes[:limit]:
        print(f"PID: {proc['pid']}, Name: {proc['name']}, Memory: {proc['memory_info'].rss / (1024 * 1024):.2f} MB")
    print()

# Function to retrieve detailed information about a specific process using its PID
def get_process_info(pid):
    try:
        proc = psutil.Process(pid)
        proc_info = {
            "PID": proc.pid,
            "Name": proc.name(),
            "Status": proc.status(),
            "CPU Usage (%)": proc.cpu_percent(interval=1),
            "Memory Usage (RSS)": proc.memory_info().rss,
            "Memory Usage (VMS)": proc.memory_info().vms,
            "Threads": proc.num_threads(),
            "Parent PID": proc.ppid(),
            "Create Time": time.ctime(proc.create_time())
        }
        print(f"Process Information for PID {pid}:")
        for key, value in proc_info.items():
            print(f"{key}: {value}")
    except psutil.NoSuchProcess:
        print(f"Error: No process with PID {pid} found.")
    except psutil.AccessDenied:
        print(f"Error: Access denied to PID {pid}.")
    print()


# Function to search for a process by name or PID
def search_process(name=None, pid=None):
    if pid:
        get_process_info(pid)
    elif name:
        found = False
        for proc in psutil.process_iter(['pid', 'name']):
            if proc.info['name'].lower() == name.lower():
                get_process_info(proc.info['pid'])
                found = True
                break
        if not found:
            print(f"No process found with name {name}.")
    else:
        print("Please provide either a process name or PID to search.")


# Function to terminate a process by PID or name
def kill_process(pid=None, name=None):
    try:
        if pid:
            proc = psutil.Process(pid)
            proc.terminate()
            print(f"Process with PID {pid} has been terminated.")
        elif name:
            for proc in psutil.process_iter(['pid', 'name']):
                if proc.info['name'].lower() == name.lower():
                    proc.terminate()
                    print(f"Process with name {name} has been terminated.")
                    return
            print(f"No process found with name {name}.")
        else:
            print("Please provide either a process name or PID to terminate.")
    except psutil.NoSuchProcess:
        print("Error: The process does not exist.")
    except psutil.AccessDenied:
        print("Error: Access denied to terminate the process.")
    except Exception as e:
        print(f"Error: {e}")


# Function to monitor a process by PID or name continuously
def monitor_process(pid=None, name=None):
    if not pid and not name:
        print("Please provide either a process name or PID to monitor.")
        return

    try:
        if pid:
            proc = psutil.Process(pid)
        elif name:
            found = False
            for proc in psutil.process_iter(['pid', 'name']):
                if proc.info['name'].lower() == name.lower():
                    proc = psutil.Process(proc.info['pid'])
                    found = True
                    break
            if not found:
                print(f"No process found with name {name}.")
                return

        print(f"Monitoring process {proc.info['name']} (PID: {proc.pid})")
        while True:
            cpu_usage = proc.cpu_percent(interval=1)  # CPU usage percentage
            mem_usage = proc.memory_info().rss / (1024 * 1024)  # Memory usage in MB
            print(f"CPU Usage: {cpu_usage:.2f}%, Memory Usage: {mem_usage:.2f} MB")
            time.sleep(1)

    except psutil.NoSuchProcess:
        print("Error: The process has terminated.")
    except psutil.AccessDenied:
        print("Error: Access denied to monitor the process.")
    except Exception as e:
        print(f"Error: {e}")


# Main program entry point
def main():
    parser = argparse.ArgumentParser(description="Process Manager Script")

    # Add arguments
    parser.add_argument('--top_cpu', action='store_true', help="Get the top processes by CPU usage")
    parser.add_argument('--top_mem', action='store_true', help="Get the top processes by Memory usage")
    parser.add_argument('--pid', type=int, help="PID of the process to get information about")
    parser.add_argument('--name', type=str, help="Name of the process to search or kill")
    parser.add_argument('--search', action='store_true', help="Search for a process by name or PID")
    parser.add_argument('--kill', action='store_true', help="Kill a process by PID or name")
    parser.add_argument('--monitor', action='store_true', help="Monitor a process by PID or name")
    parser.add_argument('--sort_by', type=str, choices=['cpu', 'mem'], default='cpu', help="Sort top processes by cpu or mem")
    parser.add_argument('--limit', type=int, default=5, help="Limit for top processes")

    # Parse arguments
    args = parser.parse_args()

    # Execute functions based on arguments
    if args.top_cpu:
        get_top_cpu_processes(sort_by=args.sort_by, limit=args.limit)
    elif args.top_mem:
        get_top_mem_processes(sort_by=args.sort_by, limit=args.limit)
    elif args.pid:
        get_process_info(args.pid)
    elif args.name:
        if args.kill:
            kill_process(name=args.name)
        elif args.monitor:
            monitor_process(name=args.name)
        else:
            search_process(name=args.name)
    elif args.search:
        if args.pid:
            search_process(pid=args.pid)
        else:
            print("Please provide either a process name or PID to search.")
    else:
        print("No valid arguments provided. Use --help for usage details.")


if __name__ == '__main__':
    main()
