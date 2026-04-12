import math
import random
from direct.showbase.ShowBase import ShowBase
from panda3d.core import (
    CollisionTraverser, CollisionNode, CollisionRay,
    CollisionHandlerQueue, BitMask32, WindowProperties, TextNode
)
from direct.gui.OnscreenText import OnscreenText
from class_scan import get_networks, estimate_distance, SYSTEM_OS

class WifiVisualizer(ShowBase):
    def __init__(self):
        super().__init__()
        props = WindowProperties()
        props.setTitle(f"WiFi 3D Mapper - {SYSTEM_OS}")
        self.win.requestProperties(props)
        self.set_background_color(0, 0, 0, 1)
        self.camera.setPos(0, -100, 30)
        self.camera.lookAt(0, 0, 0)
        self.master_dot = self.loader.loadModel("models/smiley")
        self.master_dot.setTextureOff(1)
        self.nodes = []
        self.active_callout = None
        self.setup_picking()
        self.accept("space", self.refresh_scan)
        self.refresh_scan()

    def refresh_scan(self):
        nets = get_networks()
        for node in self.nodes: node.removeNode()
        self.nodes = []
        if not nets: return
        for net in nets:
            ssid_val = str(net.get("ssid", "")).strip()
            if not ssid_val or ssid_val.lower() == "none" or ssid_val == "NULL":
                continue
            dist = estimate_distance(net["rssi"])
            theta, phi = random.uniform(0, 6.28), math.acos(random.uniform(-1, 1))
            x, y, z = dist * math.sin(phi) * math.cos(theta), dist * math.sin(phi) * math.sin(theta), dist * math.cos(phi)
            node = self.render.attachNewNode("net_node")
            self.master_dot.instanceTo(node)
            node.setPos(x, y, z)
            node.setCollideMask(BitMask32.allOn())
            brightness = max(0.2, min(1.0, (net["rssi"] + 100) / 70))
            node.setColor(brightness, brightness, brightness, 1)
            node.setScale(0.6 + brightness)
            node.setTag("ssid", ssid_val)
            node.setTag("rssi", str(net["rssi"]))
            node.setTag("bssid", str(net.get("bssid", "Unknown")))
            node.setTag("security", str(net.get("security", "Unknown")))
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
                    if self.active_callout: self.active_callout.removeNode()
                    info = (f"SSID: {target.getTag('ssid')}\nSecurity: {target.getTag('security')}\n"
                            f"Signal: {target.getTag('rssi')}dBm\nMAC: {target.getTag('bssid')}\nDist: ~{target.getTag('dist')}m")
                    self.active_callout = OnscreenText(text=info, style=1, fg=(1, 1, 1, 1), bg=(0.1, 0.1, 0.1, 0.85),
                                                      pos=(mpos.getX() + 0.1, mpos.getY()), scale=0.045, align=TextNode.ALeft, mayChange=True)
                    self.active_callout.setBin('fixed', 100)
                    self.active_callout.setDepthTest(False)

if __name__ == "__main__":
    app = WifiVisualizer()
    app.run()