#!/usr/bin/env python3
"""
EEG Service for Synapse
Provides EEG connection status and data for the main application
"""

import time
import threading
from datetime import datetime
from pythonosc import dispatcher, osc_server
from collections import deque
from typing import Optional, Dict, Any

class EEGService:
    def __init__(self, port=8001):
        self.port = port
        self.is_connected = False
        self.last_data_time = None
        self.data_count = 0
        self.start_time = datetime.now()
        
        # Store recent EEG data for connection monitoring
        self.recent_data = deque(maxlen=100)  # Keep last 100 samples
        self.connection_timeout = 5.0  # Consider disconnected after 5 seconds of no data
        
        # OSC server components
        self.server = None
        self.server_thread = None
        self.dispatcher = dispatcher.Dispatcher()
        
        # Setup OSC endpoints
        self.setup_endpoints()
        
    def setup_endpoints(self):
        """Setup OSC message handlers"""
        self.dispatcher.map("/muse/eeg", self.eeg_handler)
        self.dispatcher.map("/muse/acc", self.acc_handler)
        self.dispatcher.map("/muse/gyro", self.gyro_handler)
        self.dispatcher.map("/muse/ppg", self.ppg_handler)
        self.dispatcher.map("/muse/batt", self.battery_handler)
        self.dispatcher.map("/muse/drlref", self.drlref_handler)
        self.dispatcher.map("/eeg", self.eeg_handler)  # Alternative endpoint
        self.dispatcher.map("*", self.generic_handler)
    
    def eeg_handler(self, address, *args):
        """Handle incoming EEG data"""
        if len(args) >= 4:
            current_time = time.time()
            
            # Update connection status
            if not self.is_connected:
                self.is_connected = True
                print(f"✅ EEG Device Connected at {datetime.now().strftime('%H:%M:%S')}")
            
            self.last_data_time = current_time
            self.data_count += 1
            
            # Store the data sample
            sample = {
                'timestamp': current_time,
                'tp9': float(args[0]),
                'af7': float(args[1]),
                'af8': float(args[2]),
                'tp10': float(args[3]),
                'address': address
            }
            self.recent_data.append(sample)
    
    def acc_handler(self, address, *args):
        """Handle accelerometer data"""
        self.last_data_time = time.time()
    
    def gyro_handler(self, address, *args):
        """Handle gyroscope data"""
        self.last_data_time = time.time()
    
    def ppg_handler(self, address, *args):
        """Handle PPG data"""
        self.last_data_time = time.time()
    
    def battery_handler(self, address, *args):
        """Handle battery data"""
        self.last_data_time = time.time()
    
    def drlref_handler(self, address, *args):
        """Handle DRL/REF data"""
        self.last_data_time = time.time()
    
    def generic_handler(self, address, *args):
        """Handle any other OSC messages"""
        self.last_data_time = time.time()
    
    def start_server(self):
        """Start the OSC server in a background thread"""
        if self.server_thread and self.server_thread.is_alive():
            return True
        
        try:
            self.server = osc_server.ThreadingOSCUDPServer(("0.0.0.0", self.port), self.dispatcher)
            self.server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.server_thread.start()
            print(f"🎯 EEG Service: OSC server started on port {self.port}")
            return True
        except Exception as e:
            print(f"❌ EEG Service: Failed to start OSC server: {e}")
            return False
    
    def stop_server(self):
        """Stop the OSC server"""
        if self.server:
            self.server.shutdown()
            self.server = None
        if self.server_thread:
            self.server_thread.join(timeout=1.0)
            self.server_thread = None
        print("🛑 EEG Service: OSC server stopped")
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Get current connection status and stats"""
        current_time = time.time()
        
        # Check if we've received data recently
        if self.last_data_time and (current_time - self.last_data_time) > self.connection_timeout:
            self.is_connected = False
        
        # Calculate session duration
        session_duration = current_time - self.start_time.timestamp()
        
        # Get recent sample rate (samples per second)
        recent_samples = [s for s in self.recent_data if current_time - s['timestamp'] <= 1.0]
        sample_rate = len(recent_samples)
        
        return {
            'is_connected': self.is_connected,
            'last_data_time': self.last_data_time,
            'data_count': self.data_count,
            'session_duration': session_duration,
            'sample_rate': sample_rate,
            'server_running': self.server is not None,
            'port': self.port,
            'recent_samples_count': len(self.recent_data),
            'connection_quality': self._get_connection_quality()
        }
    
    def _get_connection_quality(self) -> str:
        """Determine connection quality based on sample rate"""
        current_time = time.time()
        recent_samples = [s for s in self.recent_data if current_time - s['timestamp'] <= 1.0]
        sample_rate = len(recent_samples)
        
        if not self.is_connected:
            return "disconnected"
        elif sample_rate >= 200:  # Muse typically streams at ~256Hz
            return "excellent"
        elif sample_rate >= 100:
            return "good"
        elif sample_rate >= 50:
            return "fair"
        else:
            return "poor"
    
    def get_live_data(self, seconds: float = 1.0) -> list:
        """Get live EEG data from the last N seconds"""
        if not self.recent_data:
            return []
        
        current_time = time.time()
        cutoff_time = current_time - seconds
        
        return [
            {
                'timestamp': sample['timestamp'],
                'tp9': sample['tp9'],
                'af7': sample['af7'],
                'af8': sample['af8'],
                'tp10': sample['tp10']
            }
            for sample in self.recent_data
            if sample['timestamp'] >= cutoff_time
        ]

# Global EEG service instance
eeg_service = EEGService()
