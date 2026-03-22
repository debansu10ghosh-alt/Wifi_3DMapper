import objc
from CoreWLAN import CWWiFiClient, CWSecurity
import math
import random
from direct.showbase.ShowBase import ShowBase
from panda3d.core import (
    Vec3, CollisionTraverser, CollisionNode,
    CollisionRay, CollisionHandlerQueue, BitMask32,
    WindowProperties, TextNode
)
from direct.gui.OnscreenText import OnscreenText


def get_security_name(sec_type):
    mapping = {
        0: "Open",
        1: "WEP",
        2: "WPA Personal",
        3: "WPA Enterprise",
        4: "WPA2 Personal",
        5: "WPA2 Enterprise",
        6: "WPA/WPA2 Personal",
        7: "WPA/WPA2 Enterprise",
        8: "WPA3 Personal",
        9: "WPA3 Enterprise",
        11: "WPA3 Transition"
    }
    return mapping.get(sec_type, "Unknown")


def scan_wifi():
    networks = []
    try:
        client = CWWiFiClient.sharedWiFiClient()
        interface = client.interface()
        scan_results, error = interface.scanForNetworksWithName_error_(None, None)
        if not error and scan_results:
            for net in scan_results:
                sec_type = net.securityType()
                networks.append({
                    "ssid": str(net.ssid()) if net.ssid() else "Hidden",
                    "bssid": str(net.bssid()) if net.bssid() else "00:00:00:00:00:00",
                    "rssi": int(net.rssiValue()) if net.rssiValue() is not None else -100,
                    "security": get_security_name(sec_type)
                })
    except Exception as e:
        print(f"Error: {e}")
    return networks


def estimate_distance(rssi):
    n = 2.5
    tx_power = -50
    return round(10 ** ((tx_power - rssi) / (10 * n)), 2)


class WifiVisualizer(ShowBase):
    def __init__(self):
        super().__init__()
        props = WindowProperties()
        props.setTitle("WiFi 3D Mapper - Press space to scan")
        self.win.requestProperties(props)
        self.set_background_color(0, 0, 0, 1)
        self.camera.setPos(0, -60, 20)
        self.camera.lookAt(0, 0, 0)

        self.master_dot = self.loader.loadModel("models/smiley")
        self.master_dot.setTextureOff(1)

        self.nodes = []
        self.active_callout = None
        self.networks = [{"ssid": "Press Space", "bssid": "00:00", "rssi": -60, "security": "N/A"}]
        self.load_scene()
        self.setup_picking()
        self.accept("space", self.refresh_scan)

    def refresh_scan(self):
        new_nets = scan_wifi()
        if new_nets:
            if self.active_callout:
                self.active_callout.removeNode()
                self.active_callout = None
            for node in self.nodes:
                node.removeNode()
            self.nodes = []
            self.networks = new_nets
            self.load_scene()

    def load_scene(self):
        for net in self.networks:
            rssi = net["rssi"]
            dist = estimate_distance(rssi)
            brightness = max(0.1, min(1.0, (rssi + 100) / 70))

            theta, phi = random.uniform(0, 6.28), random.uniform(0, 3.14)
            x = dist * math.sin(phi) * math.cos(theta)
            y = dist * math.sin(phi) * math.sin(theta)
            z = abs(dist * math.cos(phi))

            node = self.render.attachNewNode("star_node")
            self.master_dot.instanceTo(node)
            node.setPos(x, y, z)
            node.setScale(0.2 + (brightness * 0.4))
            node.setColor(brightness, brightness, brightness, 1)

            node.setTag("ssid", net["ssid"])
            node.setTag("bssid", net["bssid"])
            node.setTag("rssi", str(rssi))
            node.setTag("dist", str(dist))
            node.setTag("security", net["security"])
            self.nodes.append(node)

    def setup_picking(self):
        self.picker = CollisionTraverser()
        self.handler = CollisionHandlerQueue()
        picker_node = CollisionNode('mouseRay')
        self.pickerNP = self.camera.attachNewNode(picker_node)
        picker_node.setFromCollideMask(BitMask32.allOn())
        self.pickerRay = CollisionRay()
        picker_node.addSolid(self.pickerRay)
        self.picker.addCollider(self.pickerNP, self.handler)
        self.accept("mouse1", self.on_click)

    def on_click(self):
        if self.mouseWatcherNode.hasMouse():
            mpos = self.mouseWatcherNode.getMouse()
            self.pickerRay.setFromLens(self.camNode, mpos.getX(), mpos.getY())
            self.picker.traverse(self.render)

            if self.handler.getNumEntries() > 0:
                self.handler.sortEntries()
                picked = self.handler.getEntry(0).getIntoNodePath()
                target = picked.findNetTag("ssid")

                if not target.isEmpty():
                    if self.active_callout:
                        self.active_callout.removeNode()

                    s = target.getTag('ssid')
                    b = target.getTag('bssid')
                    r = target.getTag('rssi')
                    d = target.getTag('dist')
                    sec = target.getTag('security')

                    self.active_callout = OnscreenText(
                        text=f"SSID: {s}\nSecurity: {sec}\nMAC: {b}\nSignal: {r}dBm\nDist: ~{d}m",
                        style=1, fg=(1, 1, 1, 1), bg=(0, 0, 0, 0.8),
                        pos=(mpos.getX() + 0.05, mpos.getY() + 0.05),
                        scale=0.04, align=TextNode.ALeft
                    )


if __name__ == "__main__":
    app = WifiVisualizer()
    app.run()