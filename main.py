import sys
import os
import threading
import time
import rumps
import Quartz
import AppKit
import logging
from PyObjCTools import AppHelper
from ApplicationServices import AXIsProcessTrustedWithOptions, kAXTrustedCheckOptionPrompt

# Constants
APP_NAME = "RDP Scroll Fixer"
LOG_FILE = os.path.expanduser("~/rdp_scroll_fixer.log")

# Setup Logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

KNOWN_BUNDLE_IDS = [
    "com.microsoft.rdc.macos",      # Old version
    "com.microsoft.rdc.macos.beta", # Beta version
    "com.microsoft.rdc.mac",        # App Store version
]

class ScrollFixerApp(rumps.App):
    def __init__(self):
        super(ScrollFixerApp, self).__init__(APP_NAME, icon=None)
        
        logging.info("Application started")
        
        # Check permissions immediately
        self.check_permissions()
        
        # Default settings
        self.is_active = True
        self.sensitivity = 5  # Default sensitivity (1-5) - Start Max Sensitivity
        self.accumulator_y = 0.0
        
        # Menu items
        self.menu = [
            rumps.MenuItem("Active", callback=self.toggle_active),
            rumps.separator,
            rumps.MenuItem("Sensitivity"),
            rumps.separator,
            rumps.MenuItem("Autostart", callback=self.toggle_autostart),
            rumps.separator,
        ]
        
        # Sensitivity submenu
        self.sensitivity_items = {}
        for i in range(1, 6):
            item = rumps.MenuItem(f"Level {i}", callback=self.set_sensitivity)
            self.sensitivity_items[i] = item
            self.menu["Sensitivity"].add(item)
            
        # Initialize UI state
        self.update_ui()
        
        # Start the Event Tap in a separate thread (or just setup here and let AppHelper run it)
        # Since rumps uses AppHelper.runEventLoop(), we can just add the tap source to the run loop.
        self.setup_event_tap()

    def update_ui(self):
        # Update Active state
        self.menu["Active"].state = self.is_active
        
        # Update Sensitivity selection
        for i, item in self.sensitivity_items.items():
            item.state = (i == self.sensitivity)
            
        # Check autostart status
        self.menu["Autostart"].state = self.check_autostart()

    def toggle_active(self, sender):
        self.is_active = not self.is_active
        self.update_ui()
        print(f"Active state: {self.is_active}")

    def set_sensitivity(self, sender):
        # Parse level from title "Level X"
        try:
            level = int(sender.title.split()[-1])
            self.sensitivity = level
            self.update_ui()
            print(f"Sensitivity set to: {self.sensitivity}")
        except:
            pass
    
    def get_threshold(self):
        # Map sensitivity 1-5 to pixel threshold
        # Level 1 (Slow/Precise) -> High threshold (requires more movement)
        # Level 5 (Fast) -> Low threshold (requires less movement)
        mapping = {
            1: 50,
            2: 30,
            3: 20,
            4: 10,
            5: 5
        }
        return mapping.get(self.sensitivity, 20)

    def check_permissions(self):
        # Dictionary for options: kAXTrustedCheckOptionPrompt = True means "Show popup if not trusted"
        options = {kAXTrustedCheckOptionPrompt: True}
        is_trusted = AXIsProcessTrustedWithOptions(options)
        if not is_trusted:
            print("WARNING: Process is not trusted! Accessibility permissions required.")
            # We rely on the system prompt triggered by AXIsProcessTrustedWithOptions
            
    # --- Event Tap Logic ---

    def setup_event_tap(self):
        # Create the tap
        # Use kCGHIDEventTap as it works better on modern macOS/Apple Silicon for this use case
        tap = Quartz.CGEventTapCreate(
            Quartz.kCGHIDEventTap, 
            Quartz.kCGHeadInsertEventTap,
            Quartz.kCGEventTapOptionDefault,
            (1 << Quartz.kCGEventScrollWheel),
            self.event_tap_callback,
            None
        )

        if tap is None:
            rumps.alert("Permission Error", "Unable to create Event Tap.\nPlease grant Accessibility permissions to your terminal/application in System Settings.")
            # We don't exit here to allow the tray app to stay open and retry or let user fix it
            return

        # Create a RunLoop Source
        run_loop_source = Quartz.CFMachPortCreateRunLoopSource(None, tap, 0)
        
        # Add to current RunLoop
        Quartz.CFRunLoopAddSource(
            Quartz.CFRunLoopGetCurrent(),
            run_loop_source,
            Quartz.kCFRunLoopCommonModes
        )
        
        # Enable tap
        Quartz.CGEventTapEnable(tap, True)
        self.tap = tap

    def event_tap_callback(self, proxy, type_, event, refcon):
        if type_ == Quartz.kCGEventTapDisabledByTimeout:
            Quartz.CGEventTapEnable(self.tap, True)
            return event

        if not self.is_active:
            return event

        if type_ == Quartz.kCGEventScrollWheel:
            # Check if event is continuous (touchpad)
            is_continuous = Quartz.CGEventGetIntegerValueField(event, Quartz.kCGScrollWheelEventIsContinuous)
            
            # Log input (Debug)
            # logging.info(f"DEBUG: EventType={type_} Continuous={is_continuous}")

            if is_continuous == 0:
                # Discrete event (mouse wheel or injected), pass through
                return event
            
            # Check active application
            active_app = AppKit.NSWorkspace.sharedWorkspace().frontmostApplication()
            
            if active_app:
                bid = active_app.bundleIdentifier()
                # Debug unknown RDP versions
                if bid not in KNOWN_BUNDLE_IDS and ("Microsoft" in str(active_app.localizedName()) or "Remote" in str(active_app.localizedName())):
                     logging.info(f"Potentially unsupported RDP app detected: {bid}")

            if not active_app or active_app.bundleIdentifier() not in KNOWN_BUNDLE_IDS:
                return event

            # We are in target app and it is a continuous scroll
            
            # Get delta (Y axis) with Fallback logic
            # Axis 1 = Vertical (Standard)
            # Axis 2 = Horizontal (Sometimes used for vertical on Apple Silicon/Magic Mouse quirks)
            
            delta_y = Quartz.CGEventGetIntegerValueField(event, Quartz.kCGScrollWheelEventPointDeltaAxis1)
            
            if delta_y == 0:
                 delta_y = Quartz.CGEventGetIntegerValueField(event, Quartz.kCGScrollWheelEventPointDeltaAxis2)
            
            # If delta is still 0, ignore
            if delta_y == 0:
                return event

            # Log continuous scroll event (Only non-zero)
            logging.info(f"DETECTED: Continuous Scroll Event. App: {AppKit.NSWorkspace.sharedWorkspace().frontmostApplication().bundleIdentifier()}")

            # Log input
            logging.info(f"INPUT: DeltaY={delta_y} (Continuous)")

            # Accumulate
            self.accumulator_y += delta_y
            
            threshold = self.get_threshold()
            
            # Check if threshold reached
            if abs(self.accumulator_y) >= threshold:
                # Calculate steps (lines)
                steps = int(self.accumulator_y / threshold)
                
                # Correctly reduce accumulator (Fix modulo for negative numbers)
                self.accumulator_y -= (steps * threshold)
                
                if steps != 0:
                    logging.info(f"ACTION: InputDelta={delta_y} -> Accum={self.accumulator_y + (steps * threshold)} -> Steps={steps}")
                    
                    # Create discrete event
                    # 0 = kCGScrollEventUnitLine (Lines)
                    # 1 = kCGScrollEventUnitPixel (Pixels)
                    
                    # Fix: Use source from original event to mimic hardware
                    source = Quartz.CGEventCreateSourceFromEvent(event)
                    
                    new_event = Quartz.CGEventCreateScrollWheelEvent(
                        source,
                        0, # Units: Lines
                        1, # number of wheels
                        steps,
                        0 # horizontal
                    )
                    
                    # Fix: Set location to match original event (RDP might ignore events at 0,0)
                    location = Quartz.CGEventGetLocation(event)
                    Quartz.CGEventSetLocation(new_event, location)
                    
                    # Fix: Copy flags (modifiers like Cmd/Shift)
                    flags = Quartz.CGEventGetFlags(event)
                    Quartz.CGEventSetFlags(new_event, flags)
                    
                    # Ensure it is NOT continuous
                    Quartz.CGEventSetIntegerValueField(new_event, Quartz.kCGScrollWheelEventIsContinuous, 0)
                    
                    # Post it
                    Quartz.CGEventPost(Quartz.kCGHIDEventTap, new_event)
                    
                    logging.info(f"ACTION: Posted Scroll Steps={steps} at {location}")
            
            # Suppress the original continuous event
            return None

        return event

    # --- Autostart Logic ---
    
    def get_plist_path(self):
        home = os.path.expanduser("~")
        return os.path.join(home, "Library", "LaunchAgents", "com.fixscroll.rdp.plist")

    def check_autostart(self):
        return os.path.exists(self.get_plist_path())

    def toggle_autostart(self, sender):
        plist_path = self.get_plist_path()
        if os.path.exists(plist_path):
            try:
                os.remove(plist_path)
                rumps.notification("Autostart", "Disabled", "Removed from LaunchAgents")
            except Exception as e:
                rumps.alert("Error", str(e))
        else:
            # Create plist
            
            # Check if running as a frozen app (py2app)
            if getattr(sys, 'frozen', False):
                # If frozen, we just execute the app bundle executable
                # sys.executable points to .../Contents/MacOS/AppName
                program_args = [sys.executable]
            else:
                # If running from source
                exe_path = sys.executable
                script_path = os.path.abspath(sys.argv[0])
                program_args = [exe_path, script_path]
            
            # Build the <array> part of the plist
            args_xml = "\n".join([f"        <string>{arg}</string>" for arg in program_args])
            
            plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.fixscroll.rdp</string>
    <key>ProgramArguments</key>
    <array>
{args_xml}
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
"""
            try:
                with open(plist_path, "w") as f:
                    f.write(plist_content)
                rumps.notification("Autostart", "Enabled", "Added to LaunchAgents")
            except Exception as e:
                rumps.alert("Error", str(e))
        
        self.update_ui()

if __name__ == "__main__":
    app = ScrollFixerApp()
    app.run()
