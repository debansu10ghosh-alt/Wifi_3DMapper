import math
import random
from direct.showbase.ShowBase import ShowBase
from panda3d.core import (
    CollisionTraverser, CollisionNode, CollisionRay,
    CollisionHandlerQueue, BitMask32, WindowProperties, TextNode
)
from direct.gui.OnscreenText import OnscreenText
from something_idk import scan_wifi, estimate_distance

class WifiVisualizer(ShowBase):
    def __init__(self):
        super().__init__()
        props = WindowProperties()
        props.setTitle("WiFi 3D Mapper - Press space to scan")
        self.win.requestProperties(props)
        self.set_backgrou nd_color(0, 0, 0, 1)
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
                    self.active_callout = OnscreenText(
                        text=f"SSID: {target.getTag('ssid')}\nSecurity: {target.getTag('security')}\nMAC: {target.getTag('bssid')}\nSignal: {target.getTag('rssi')}dBm\nDist: ~{target.getTag('dist')}m",
                        style=1, fg=(1, 1, 1, 1), bg=(0, 0, 0, 0.8),
                        pos=(mpos.getX() + 0.05, mpos.getY() + 0.05),
                        scale=0.04, align=TextNode.ALeft
                    )

if __name__ == "__main__":
    app = WifiVisualizer()
    app.run()