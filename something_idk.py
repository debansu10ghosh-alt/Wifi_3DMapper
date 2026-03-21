import objc
from CoreWLAN import CWWiFiClient
import math
import random
from direct.showbase.ShowBase import ShowBase
from panda3d.core import (
    Vec3, CollisionTraverser, CollisionNode,
    CollisionRay, CollisionHandlerQueue, BitMask32,
    WindowProperties
)


def scan_wifi():
    print("\n[SYSTEM] Attempting WiFi Scan...")
    networks = []
    try:
        client = CWWiFiClient.sharedWiFiClient()
        interface = client.interface()
        scan_results, error = interface.scanForNetworksWithName_error_(None, None)

        if not error and scan_results:
            for net in scan_results:
                networks.append({
                    "ssid": str(net.ssid()) if net.ssid() else "Hidden",
                    "rssi": int(net.rssiValue()) if net.rssiValue() is not None else -100
                })
    except:
        pass
    return networks


def estimate_distance(rssi):
    n = 2.5
    tx_power = -50
    return round(10 ** ((tx_power - rssi) / (10 * n)), 2)


class WifiVisualizer(ShowBase):
    def __init__(self):
        super().__init__()

        props = WindowProperties()
        props.setTitle("WiFi Thingi Magingi - Space to Scan")
        self.win.requestProperties(props)
        self.set_background_color(0, 0, 0, 1)

        self.camera.setPos(0, -60, 20)
        self.camera.lookAt(0, 0, 0)

        self.master_dot = self.loader.loadModel("models/smiley")
        self.master_dot.setTextureOff(1)
        self.nodes = []

        self.networks = [
            {"ssid": "Initial_Search_1", "rssi": -45},
            {"ssid": "Initial_Search_2", "rssi": -85}
        ]
        self.load_scene()

        self.setup_picking()
        self.accept("space", self.refresh_scan)
        print("Press SPACE to run a scan.")

    def refresh_scan(self):
        print("Scanning airwaves...")
        new_nets = scan_wifi()
        if new_nets:
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
            node.setTag("rssi", str(rssi))
            node.setTag("dist", str(dist))
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
                    s = target.getTag('ssid')
                    r = target.getTag('rssi')
                    d = target.getTag('dist')
                    print(f"Wifi: {s} | Signal: {r}dBm | Dist: approx-{d}m")


if __name__ == "__main__":
    app = WifiVisualizer()
    app.run()