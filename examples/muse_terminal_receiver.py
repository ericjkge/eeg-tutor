#!/usr/bin/env python3
"""
Simple Muse EEG Data Terminal Receiver
Receives OSC data from Muse device and displays it in the terminal
"""

import sys
import time
from datetime import datetime
from pythonosc import dispatcher, osc_server
import threading

class MuseTerminalReceiver:
    def __init__(self, ip="0.0.0.0", port=8000):
        self.ip = ip
        self.port = port
        self.data_count = 0
        self.start_time = datetime.now()
        
        # Set up OSC dispatcher
        self.dispatcher = dispatcher.Dispatcher()
        
        # Map all possible Muse endpoints
        self.dispatcher.map("/muse/eeg", self.eeg_handler)
        self.dispatcher.map("/muse/acc", self.acc_handler)
        self.dispatcher.map("/muse/gyro", self.gyro_handler)
        self.dispatcher.map("/muse/ppg", self.ppg_handler)
        self.dispatcher.map("/muse/batt", self.battery_handler)
        self.dispatcher.map("/muse/drlref", self.drlref_handler)
        
        # Catch-all for any other endpoints
        self.dispatcher.map("*", self.generic_handler)
        
        print(f"🧠 Muse Terminal Receiver Starting...")
        print(f"📡 Listening on {self.ip}:{self.port}")
        print(f"⏰ Started at {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("-" * 60)
        print("Waiting for Muse data... (Press Ctrl+C to stop)")
        print("-" * 60)

    def eeg_handler(self, address, *args):
        """Handle EEG data (4 channels: TP9, AF7, AF8, TP10)"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.data_count += 1
        
        if len(args) >= 4:
            print(f"🧠 EEG [{timestamp}] TP9:{args[0]:8.3f} AF7:{args[1]:8.3f} AF8:{args[2]:8.3f} TP10:{args[3]:8.3f}")
        else:
            print(f"🧠 EEG [{timestamp}] {args}")

    def acc_handler(self, address, *args):
        """Handle Accelerometer data (X, Y, Z)"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        if len(args) >= 3:
            print(f"📱 ACC [{timestamp}] X:{args[0]:7.3f} Y:{args[1]:7.3f} Z:{args[2]:7.3f}")
        else:
            print(f"📱 ACC [{timestamp}] {args}")

    def gyro_handler(self, address, *args):
        """Handle Gyroscope data (X, Y, Z)"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        if len(args) >= 3:
            print(f"🔄 GYRO [{timestamp}] X:{args[0]:7.3f} Y:{args[1]:7.3f} Z:{args[2]:7.3f}")
        else:
            print(f"🔄 GYRO [{timestamp}] {args}")

    def ppg_handler(self, address, *args):
        """Handle PPG (heart rate) data"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"❤️  PPG [{timestamp}] {args}")

    def battery_handler(self, address, *args):
        """Handle battery level data"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        if args:
            print(f"🔋 BATT [{timestamp}] Level: {args[0]}%")
        else:
            print(f"🔋 BATT [{timestamp}] {args}")

    def drlref_handler(self, address, *args):
        """Handle DRL/REF electrode data"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"🔌 DRL/REF [{timestamp}] {args}")

    def generic_handler(self, address, *args):
        """Handle any other OSC messages"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"📡 {address} [{timestamp}] {args}")

    def print_stats(self):
        """Print connection statistics"""
        elapsed = datetime.now() - self.start_time
        print(f"\n📊 Stats: {self.data_count} messages received in {elapsed}")

    def start(self):
        """Start the OSC server"""
        try:
            server = osc_server.ThreadingOSCUDPServer((self.ip, self.port), self.dispatcher)
            print(f"✅ Server started successfully!")
            server.serve_forever()
        except KeyboardInterrupt:
            print(f"\n\n🛑 Stopping receiver...")
            self.print_stats()
            print("👋 Goodbye!")
        except Exception as e:
            print(f"❌ Error starting server: {e}")
            print("💡 Try a different port (8001, 8002) if 8000 is busy")

def main():
    """Main function"""
    # Default settings
    ip = "0.0.0.0"
    port = 8000
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] in ['-h', '--help']:
            print("Muse Terminal Receiver")
            print("Usage: python muse_terminal_receiver.py [IP] [PORT]")
            print("Default: 0.0.0.0 8000")
            print("\nMake sure your Muse streaming app is configured to send OSC data to this IP and port.")
            return
        
        if len(sys.argv) >= 2:
            ip = sys.argv[1]
        if len(sys.argv) >= 3:
            try:
                port = int(sys.argv[2])
            except ValueError:
                print("❌ Invalid port number. Using default 8000.")
                port = 8000

    # Create and start receiver
    receiver = MuseTerminalReceiver(ip, port)
    receiver.start()

if __name__ == "__main__":
    main()