import platform
import psutil
import subprocess
import sys
import json
from datetime import datetime

def get_system_info():
    """Get basic system information"""
    info = {
        'System': platform.system(),
        'Node Name': platform.node(),
        'Release': platform.release(),
        'Version': platform.version(),
        'Machine': platform.machine(),
        'Processor': platform.processor(),
        'Architecture': platform.architecture()[0],
        'Python Version': platform.python_version()
    }
    return info

def get_cpu_info():
    """Get CPU information and status"""
    cpu_info = {
        'Physical Cores': psutil.cpu_count(logical=False),
        'Total Cores': psutil.cpu_count(logical=True),
        'Max Frequency': f"{psutil.cpu_freq().max:.2f} MHz" if psutil.cpu_freq() else "N/A",
        'Current Frequency': f"{psutil.cpu_freq().current:.2f} MHz" if psutil.cpu_freq() else "N/A",
        'CPU Usage': f"{psutil.cpu_percent(interval=1):.1f}%",
        'Load Average (1min)': psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else "N/A"
    }
    return cpu_info

def get_memory_info():
    """Get memory information"""
    memory = psutil.virtual_memory()
    swap = psutil.swap_memory()
    
    memory_info = {
        'Total RAM': f"{memory.total / (1024**3):.2f} GB",
        'Available RAM': f"{memory.available / (1024**3):.2f} GB",
        'RAM Usage': f"{memory.percent:.1f}%",
        'Total Swap': f"{swap.total / (1024**3):.2f} GB",
        'Swap Usage': f"{swap.percent:.1f}%"
    }
    return memory_info

def get_temperature_info():
    """Get temperature sensors if available"""
    try:
        temps = psutil.sensors_temperatures()
        temp_info = {}
        
        for name, entries in temps.items():
            temp_info[name] = []
            for entry in entries:
                temp_data = {
                    'label': entry.label or 'N/A',
                    'current': f"{entry.current:.1f}°C",
                    'high': f"{entry.high:.1f}°C" if entry.high else "N/A",
                    'critical': f"{entry.critical:.1f}°C" if entry.critical else "N/A"
                }
                temp_info[name].append(temp_data)
        
        return temp_info if temp_info else {"Status": "No temperature sensors detected"}
    except:
        return {"Status": "Temperature monitoring not available"}

def get_disk_info():
    """Get disk information"""
    disk_info = {}
    partitions = psutil.disk_partitions()
    
    for partition in partitions:
        try:
            partition_usage = psutil.disk_usage(partition.mountpoint)
            disk_info[partition.device] = {
                'Mountpoint': partition.mountpoint,
                'File System': partition.fstype,
                'Total Size': f"{partition_usage.total / (1024**3):.2f} GB",
                'Used': f"{partition_usage.used / (1024**3):.2f} GB",
                'Free': f"{partition_usage.free / (1024**3):.2f} GB",
                'Usage %': f"{(partition_usage.used / partition_usage.total) * 100:.1f}%"
            }
        except PermissionError:
            disk_info[partition.device] = {"Status": "Permission denied"}
    
    return disk_info

def get_network_info():
    """Get network interface information"""
    network_info = {}
    interfaces = psutil.net_if_addrs()
    stats = psutil.net_if_stats()
    
    for interface_name, interface_addresses in interfaces.items():
        network_info[interface_name] = {
            'addresses': [],
            'is_up': stats[interface_name].isup if interface_name in stats else False,
            'speed': f"{stats[interface_name].speed} Mbps" if interface_name in stats and stats[interface_name].speed > 0 else "N/A"
        }
        
        for address in interface_addresses:
            network_info[interface_name]['addresses'].append({
                'family': str(address.family),
                'address': address.address,
                'netmask': address.netmask
            })
    
    return network_info

def get_bios_info():
    """Get BIOS/UEFI information (Windows/Linux)"""
    bios_info = {}
    
    try:
        if platform.system() == "Windows":
            # Try to get BIOS info using wmic
            result = subprocess.run(['wmic', 'bios', 'get', 'name,serialnumber,version', '/format:list'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if '=' in line and line.strip():
                        key, value = line.split('=', 1)
                        if value.strip():
                            bios_info[key] = value.strip()
        
        elif platform.system() == "Linux":
            # Try to read DMI information
            try:
                with open('/sys/class/dmi/id/bios_version', 'r') as f:
                    bios_info['BIOS Version'] = f.read().strip()
            except:
                pass
            
            try:
                with open('/sys/class/dmi/id/board_name', 'r') as f:
                    bios_info['Board Name'] = f.read().strip()
            except:
                pass
                
            try:
                with open('/sys/class/dmi/id/board_vendor', 'r') as f:
                    bios_info['Board Vendor'] = f.read().strip()
            except:
                pass
    
    except Exception as e:
        bios_info['Error'] = f"Could not retrieve BIOS info: {str(e)}"
    
    return bios_info if bios_info else {"Status": "BIOS information not accessible"}

def check_system_health():
    """Perform basic system health checks"""
    health_status = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'uptime': str(datetime.now() - datetime.fromtimestamp(psutil.boot_time())),
        'boot_time': datetime.fromtimestamp(psutil.boot_time()).strftime('%Y-%m-%d %H:%M:%S')
    }
    
    # Check CPU usage
    cpu_usage = psutil.cpu_percent(interval=1)
    if cpu_usage > 80:
        health_status['cpu_warning'] = f"High CPU usage: {cpu_usage}%"
    
    # Check memory usage
    memory = psutil.virtual_memory()
    if memory.percent > 85:
        health_status['memory_warning'] = f"High memory usage: {memory.percent}%"
    
    # Check disk usage
    for partition in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(partition.mountpoint)
            usage_percent = (usage.used / usage.total) * 100
            if usage_percent > 90:
                health_status[f'disk_warning_{partition.device}'] = f"Low disk space: {usage_percent:.1f}% used"
        except PermissionError:
            continue
    
    return health_status

def main():
    """Main function to gather and display all motherboard/system information"""
    print("=" * 60)
    print("MOTHERBOARD & SYSTEM STATUS CHECK")
    print("=" * 60)
    print(f"Scan Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # System Information
    print("SYSTEM INFORMATION:")
    print("-" * 30)
    system_info = get_system_info()
    for key, value in system_info.items():
        print(f"{key}: {value}")
    print()
    
    # BIOS Information
    print("BIOS/MOTHERBOARD INFORMATION:")
    print("-" * 30)
    bios_info = get_bios_info()
    for key, value in bios_info.items():
        print(f"{key}: {value}")
    print()
    
    # CPU Information
    print("CPU STATUS:")
    print("-" * 30)
    cpu_info = get_cpu_info()
    for key, value in cpu_info.items():
        print(f"{key}: {value}")
    print()
    
    # Memory Information
    print("MEMORY STATUS:")
    print("-" * 30)
    memory_info = get_memory_info()
    for key, value in memory_info.items():
        print(f"{key}: {value}")
    print()
    
    # Temperature Information
    print("TEMPERATURE SENSORS:")
    print("-" * 30)
    temp_info = get_temperature_info()
    if isinstance(temp_info, dict) and 'Status' in temp_info:
        print(temp_info['Status'])
    else:
        for sensor_name, readings in temp_info.items():
            print(f"{sensor_name}:")
            for reading in readings:
                print(f"  {reading['label']}: {reading['current']} (High: {reading['high']}, Critical: {reading['critical']})")
    print()
    
    # Disk Information
    print("DISK STATUS:")
    print("-" * 30)
    disk_info = get_disk_info()
    for device, info in disk_info.items():
        print(f"{device}:")
        for key, value in info.items():
            print(f"  {key}: {value}")
        print()
    
    # Network Information
    print("NETWORK INTERFACES:")
    print("-" * 30)
    network_info = get_network_info()
    for interface, info in network_info.items():
        print(f"{interface}:")
        print(f"  Status: {'UP' if info['is_up'] else 'DOWN'}")
        print(f"  Speed: {info['speed']}")
        for addr in info['addresses'][:2]:  # Limit output
            print(f"  {addr['family']}: {addr['address']}")
        print()
    
    # Health Check
    print("SYSTEM HEALTH CHECK:")
    print("-" * 30)
    health = check_system_health()
    for key, value in health.items():
        if 'warning' in key.lower():
            print(f"⚠️  {key.replace('_', ' ').title()}: {value}")
        else:
            print(f"{key.replace('_', ' ').title()}: {value}")
    print()
    
    print("=" * 60)
    print("SCAN COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    try:
        # Check if required modules are installed
        main()
    except ImportError as e:
        print(f"Missing required module: {e}")
        print("Install with: pip install psutil")
    except Exception as e:
        print(f"Error running system check: {e}")
        print("Make sure you're running with appropriate permissions.")