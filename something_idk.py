import platform
import subprocess
import re

SYSTEM_OS = platform.system()
if SYSTEM_OS == "Darwin":
    import objc
    from CoreWLAN import CWWiFiClient
elif SYSTEM_OS == "Windows":
    import subprocess

def get_security_name(sec_type):
    mapping = {
        0: "Open", 1: "WEP", 2: "WPA Personal", 3: "WPA Enterprise",
        4: "WPA2 Personal", 5: "WPA2 Enterprise", 6: "WPA/WPA2 Personal",
        7: "WPA/WPA2 Enterprise", 8: "WPA3 Personal", 9: "WPA3 Enterprise",
        10: "WPA3 Transition (Personal)", 11: "WPA3 Transition"
    }
    try:
        val = int(sec_type)
        return mapping.get(val, f"Unknown ({val})")
    except (ValueError, TypeError):
        return "Not Detected"

def scan_wifi_windows():
    networks = []
    try:
        results = subprocess.check_output(["netsh", "wlan", "show", "networks", "mode=bssid"],
                                         universal_newlines=True, stderr=subprocess.DEVNULL)
        parts = re.split(r"SSID \d+ : ", results)
        for part in parts[1:]:
            lines = part.split('\n')
            ssid = lines[0].strip() if lines[0].strip() else "Hidden"
            bssid_match = re.search(r"BSSID 1\s+: ([\da-fA-F:]+)", part)
            signal_match = re.search(r"Signal\s+: (\d+)%", part)
            auth_match = re.search(r"Authentication\s+: ([\w\s]+)", part)
            if bssid_match and signal_match:
                quality = int(signal_match.group(1))
                rssi = (quality / 2) - 100
                networks.append({
                    "ssid": ssid,
                    "bssid": bssid_match.group(1),
                    "rssi": rssi,
                    "security": auth_match.group(1).strip() if auth_match else "Unknown"
                })
    except Exception as e:
        print(f"Error: {e}")
    return networks

def scan_wifi_mac():
    networks = []
    try:
        client = CWWiFiClient.sharedWiFiClient()
        interface = client.interface()
        scan_results, error = interface.scanForNetworksWithName_error_(None, None)
        if not error and scan_results:
            for net in scan_results:
                networks.append({
                    "ssid": str(net.ssid()) if net.ssid() else "Hidden",
                    "bssid": str(net.bssid()) if net.bssid() else "00:00:00:00:00:00",
                    "rssi": int(net.rssiValue()) if net.rssiValue() is not None else -100,
                    "security": get_security_name(net.securityType())
                })
    except Exception as e:
        print(f"Error: {e}")
    return networks

def scan_wifi():
    if SYSTEM_OS == "Windows":
        return scan_wifi_windows()
    elif SYSTEM_OS == "Darwin":
        return scan_wifi_mac()
    return []

def estimate_distance(rssi):
    n = 2.5
    tx_power = -50
    return round(10 ** ((tx_power - rssi) / (10 * n)), 2)