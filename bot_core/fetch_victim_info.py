import platform
import wmi
import winreg
import socket
import uuid
import time
from datetime import datetime, timedelta

def decode_windows_product_key():
    try:
        # Access the Registry key for Windows product key
        registry = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
        key_path = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion"
        key = winreg.OpenKey(registry, key_path)
        value, _ = winreg.QueryValueEx(key, "ProductName")
        product_name = value
        digital_product_id, _ = winreg.QueryValueEx(key, "DigitalProductId")
        winreg.CloseKey(key)

        # Decode DigitalProductId to get the 25-character product key
        key_chars = "BCDFGHJKMPQRTVWXY2346789"
        product_key = ""
        digits = list(digital_product_id[52:67])  # Relevant bytes for product key
        for i in range(24, -1, -1):
            r = 0
            for j in range(14, -1, -1):
                r = (r * 256) ^ digits[j]
                digits[j] = r // 24
                r = r % 24
            product_key = key_chars[r] + product_key
        # Format the key in groups of 5
        formatted_key = "-".join([product_key[i:i+5] for i in range(0, 25, 5)])
        return f"{product_name} (Product Key: {formatted_key})"
    except Exception as e:
        return f"Error retrieving product key: {str(e)}"

def get_system_info():
    # Initialize WMI
    c = wmi.WMI()

    # Gather basic system info from platform
    system_info = {
        "OS": platform.system(),
        "OS Version": platform.release(),
        "OS Build": platform.version(),
        "Platform": platform.platform(),
        "Machine": platform.machine(),
        "Architecture": platform.architecture()[0],
        "Node Name": platform.node(),
        "Processor": platform.processor(),
    }

    # Add Windows product key (full 25-character key)
    system_info["Windows Product Key"] = decode_windows_product_key()

    # Gather system info from WMI
    for system in c.Win32_ComputerSystem():
        system_info["Manufacturer"] = system.Manufacturer
        system_info["Model"] = system.Model
        system_info["Total Physical Memory (GB)"] = str(round(int(system.TotalPhysicalMemory) / (1024**3), 2))
        system_info["System Type"] = system.SystemType
        system_info["Domain"] = system.Domain

    # Gather OS details
    for os in c.Win32_OperatingSystem():
        system_info["OS Caption"] = os.Caption
        system_info["Service Pack"] = f"{os.ServicePackMajorVersion}.{os.ServicePackMinorVersion}"
        system_info["Install Date"] = datetime.strptime(os.InstallDate[:14], "%Y%m%d%H%M%S").strftime("%Y-%m-%d %H:%M:%S")
        system_info["Last Boot Time"] = datetime.strptime(os.LastBootUpTime[:14], "%Y%m%d%H%M%S").strftime("%Y-%m-%d %H:%M:%S")
        system_info["System Uptime (Hours)"] = str(round((time.time() - time.mktime(datetime.strptime(os.LastBootUpTime[:14], "%Y%m%d%H%M%S").timetuple())) / 3600, 2))

    # Gather CPU info
    for cpu in c.Win32_Processor():
        system_info["CPU Name"] = cpu.Name
        system_info["CPU Cores"] = str(cpu.NumberOfCores)
        system_info["CPU Threads"] = str(cpu.ThreadCount)
        system_info["CPU Max Clock Speed (MHz)"] = str(cpu.MaxClockSpeed)

    # Gather motherboard info
    for board in c.Win32_BaseBoard():
        system_info["Motherboard Manufacturer"] = board.Manufacturer
        system_info["Motherboard Model"] = board.Product
        system_info["Motherboard Serial Number"] = board.SerialNumber

    # Gather BIOS info
    for bios in c.Win32_BIOS():
        system_info["BIOS Version"] = bios.SMBIOSBIOSVersion
        system_info["BIOS Manufacturer"] = bios.Manufacturer
        system_info["BIOS Serial Number"] = bios.SerialNumber

    # Gather disk info
    for disk in c.Win32_DiskDrive():
        system_info["Disk Model"] = disk.Model
        system_info["Disk Size (GB)"] = str(round(int(disk.Size) / (1024**3), 2))
        system_info["Disk Serial Number"] = disk.SerialNumber
        break  # Get first disk only for simplicity

    # Gather memory module info
    memory_modules = []
    for mem in c.Win32_PhysicalMemory():
        memory_modules.append(f"Type: {mem.MemoryType}, Speed: {mem.Speed} MHz, Capacity: {round(int(mem.Capacity) / (1024**3), 2)} GB")
    system_info["Memory Modules"] = "; ".join(memory_modules) if memory_modules else "Unknown"

    # Gather GPU info
    for gpu in c.Win32_VideoController():
        system_info["GPU Name"] = gpu.Name
        system_info["GPU Driver Version"] = gpu.DriverVersion
        system_info["GPU Video Memory (MB)"] = str(gpu.AdapterRAM // (1024**2)) if gpu.AdapterRAM else "Unknown"
        break  # Get first GPU only for simplicity

    # Gather network adapter info
    network_adapters = []
    for adapter in c.Win32_NetworkAdapterConfiguration(IPEnabled=True):
        network_adapters.append(f"Adapter: {adapter.Description}, IP: {adapter.IPAddress[0] if adapter.IPAddress else 'N/A'}, MAC: {adapter.MACAddress}")
    system_info["Network Adapters"] = "; ".join(network_adapters) if network_adapters else "Unknown"

    # Gather battery info (for laptops)
    for battery in c.Win32_Battery():
        system_info["Battery Name"] = battery.Name
        system_info["Battery Status"] = battery.BatteryStatus
        system_info["Estimated Charge Remaining (%)"] = str(battery.EstimatedChargeRemaining) if battery.EstimatedChargeRemaining else "Unknown"
        break  # Get first battery only

    # Gather network info
    system_info["Hostname"] = socket.gethostname()
    system_info["IP Address"] = socket.gethostbyname(socket.gethostname())
    system_info["MAC Address"] = ':'.join(['{:02x}'.format((uuid.getnode() >> i) & 0xff) for i in range(0, 48, 8)][::-1])

    # Convert to formatted string
    info_string = "System Information:\n"
    info_string += "\n".join(f"{key}: {value}" for key, value in system_info.items())
    
    return info_string

# Store all info in a variable
info_string = get_system_info()

# Print the string (for verification)
print(info_string)