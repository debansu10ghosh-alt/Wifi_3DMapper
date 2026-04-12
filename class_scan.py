import platform
import subprocess
import re
import math
import random

SYSTEM_OS = platform.system()

if SYSTEM_OS == "Darwin":
    try:
        import objc
        from CoreWLAN import CWWiFiClient
    except ImportError:
        pass

def scan_wifi_linux():
    networks = []
    try:
        cmd = ["nmcli", "-t", "-f", "SSID,BSSID,SIGNAL,SECURITY", "dev", "wifi"]
        output = subprocess.check_output(cmd, universal_newlines=True)
        for line in output.strip().split('\n'):
            parts = line.split(':')
            if len(parts) >= 4:
                networks.append({
                    "ssid": parts[0],
                    "bssid": ":".join(parts[1:7]),
                    "rssi": (int(parts[7]) / 2) - 100,
                    "security": parts[8] if parts[8] else "Open"
                })
    except:
        pass
    return networks

def scan_wifi_windows():
    networks = []
    try:
        results = subprocess.check_output(["netsh", "wlan", "show", "networks", "mode=bssid"],
                                          universal_newlines=True, stderr=subprocess.DEVNULL)
        parts = re.split(r"SSID \d+ : ", results)
        for part in parts[1:]:
            lines = part.split('\n')
            ssid = lines[0].strip()
            auth_match = re.search(r"Authentication\s+: ([\w\s\d\-]+)", part)
            bssid_match = re.search(r"BSSID 1\s+: ([\da-fA-F:]+)", part)
            signal_match = re.search(r"Signal\s+: (\d+)%", part)
            if bssid_match and signal_match:
                networks.append({
                    "ssid": ssid,
                    "bssid": bssid_match.group(1),
                    "rssi": (int(signal_match.group(1)) / 2) - 100,
                    "security": auth_match.group(1).strip() if auth_match else "Unknown"
                })
    except:
        pass
    return networks

def scan_wifi_mac():
    networks = []
    try:
        client = CWWiFiClient.sharedWiFiClient()
        if client:
            interface = client.interface()
            scan_results, error = interface.scanForNetworksWithName_error_(None, None)
            for net in scan_results:
                sec_val = net.securityType()
                sec_name = "Secure" if sec_val > 0 else "Open"
                networks.append({
                    "ssid": str(net.ssid()) if net.ssid() else None,
                    "bssid": str(net.bssid()),
                    "rssi": int(net.rssiValue()),
                    "security": sec_name
                })
    except:
        pass
    return networks

def get_networks():
    if SYSTEM_OS == "Windows":
        return scan_wifi_windows()
    elif SYSTEM_OS == "Darwin":
        return scan_wifi_mac()
    else:
        return scan_wifi_linux()

def estimate_distance(rssi):
    return round(10 ** ((-50 - rssi) / (10 * 2.5)), 2)