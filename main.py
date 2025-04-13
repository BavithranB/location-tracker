from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.utils import platform
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.clock import Clock
import geocoder
import requests
import json
import time
import uuid
from plyer import gps

class LocationTrackerApp(App):
    def build(self):
        # Generate a fallback unique device ID
        self.default_device_id = str(uuid.uuid4())[:8]
        self.device_id = None
        
        # Firebase configuration
        self.firebase_base_url = "https://tracker-55edb-default-rtdb.asia-southeast1.firebasedatabase.app"
        
        # Initialize location variables
        self.using_gps = False
        self.last_known_location = None
        self.location_accuracy = "Unknown"
        
        # Main layout
        self.main_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Show the username input popup
        self.show_username_popup()
        
        return self.main_layout
    
    def show_username_popup(self):
        popup_layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        title_label = Label(
            text='Enter Your Username',
            font_size=20,
            size_hint=(1, 0.3)
        )
        popup_layout.add_widget(title_label)
        
        self.username_input = TextInput(
            hint_text='Username',
            multiline=False,
            font_size=18,
            size_hint=(1, 0.3)
        )
        popup_layout.add_widget(self.username_input)
        
        submit_button = Button(
            text='Start Tracking',
            size_hint=(1, 0.3),
            on_press=self.submit_username
        )
        popup_layout.add_widget(submit_button)
        
        self.popup = Popup(
            title='Location Tracker Login',
            content=popup_layout,
            size_hint=(0.8, 0.4),
            auto_dismiss=False
        )
        self.popup.open()
    
    def submit_username(self, instance):
        username = self.username_input.text.strip()
        
        if username:
            self.device_id = username
        else:
            self.device_id = self.default_device_id
        
        self.popup.dismiss()
        self.initialize_main_interface()
    
    def initialize_main_interface(self):
        self.main_layout.clear_widgets()
        
        # App title
        title_label = Label(
            text='Location Tracker',
            font_size=24,
            size_hint=(1, 0.15)
        )
        self.main_layout.add_widget(title_label)
        
        # Username display
        username_label = Label(
            text=f'Tracking as: {self.device_id}',
            font_size=16,
            size_hint=(1, 0.1)
        )
        self.main_layout.add_widget(username_label)
        
        # Status display
        self.status_label = Label(
            text='Ready to start tracking',
            font_size=18,
            size_hint=(1, 0.1)
        )
        self.main_layout.add_widget(self.status_label)
        
        # Method display
        self.method_label = Label(
            text='Checking location services...',
            font_size=14,
            size_hint=(1, 0.1)
        )
        self.main_layout.add_widget(self.method_label)
        
        # Accuracy display
        self.accuracy_label = Label(
            text='Accuracy: Unknown',
            font_size=14,
            size_hint=(1, 0.1)
        )
        self.main_layout.add_widget(self.accuracy_label)
        
        # Coordinates display
        self.coords_label = Label(
            text='Coordinates will appear here',
            font_size=16,
            size_hint=(1, 0.15)
        )
        self.main_layout.add_widget(self.coords_label)
        
        # Address display (reverse geocode)
        self.address_label = Label(
            text='Address will appear here',
            font_size=14,
            size_hint=(1, 0.1)
        )
        self.main_layout.add_widget(self.address_label)
        
        # Control buttons
        button_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.2), spacing=10)
        
        self.start_button = Button(
            text='Start Tracking',
            on_press=self.start_tracking
        )
        button_layout.add_widget(self.start_button)
        
        self.stop_button = Button(
            text='Stop Tracking',
            on_press=self.stop_tracking,
            disabled=True
        )
        button_layout.add_widget(self.stop_button)
        
        self.main_layout.add_widget(button_layout)
        
        # Initialize variables
        self.tracking_active = False
        self.tracking_event = None
        self.gps_timeout_event = None
        
        # Try to initialize GPS
        self.check_gps_availability()
    
    def check_gps_availability(self):

        try:
            # Only use GPS on Android and iOS
            if platform in ('android', 'ios'):
                # Configure GPS with high accuracy settings
                gps.configure(on_location=self.on_gps_location,
                            on_status=self.on_gps_status)
                self.using_gps = True
                self.method_label.text = 'GPS Ready (High Accuracy)'
                
                # Request Android permissions at runtime (Android only)
                if platform == 'android':
                    from android.permissions import request_permissions, Permission
                    request_permissions([
                        Permission.ACCESS_FINE_LOCATION,
                        Permission.ACCESS_COARSE_LOCATION
                    ])
            else:
                self.using_gps = False
                self.method_label.text = 'Using IP Geolocation (Low Accuracy)'
        except Exception as e:
            self.using_gps = False
            self.method_label.text = 'Using IP Geolocation (Low Accuracy)'
            print(f"GPS not available: {str(e)}")
    
    def on_gps_status(self, *args, **kwargs):
        status = kwargs.get('status', '')
        self.status_label.text = f'GPS: {status}'
        
    def start_tracking(self, instance):
        if not self.tracking_active:
            self.tracking_active = True
            self.start_button.disabled = True
            self.stop_button.disabled = False
            self.status_label.text = 'Starting location tracking...'
            
            if self.using_gps:
                try:
                    # Request more frequent updates with higher accuracy
                    gps.start(minTime=1000, minDistance=0)
                    self.method_label.text = 'Using GPS (High Accuracy)'
                    # Set a timeout for waiting for GPS
                    self.gps_timeout_event = Clock.schedule_once(self.check_gps_timeout, 15)
                    # Also schedule regular checks
                    self.tracking_event = Clock.schedule_interval(self.check_location_updates, 5)
                except Exception as e:
                    # If GPS fails, fall back to IP geolocation
                    self.using_gps = False
                    self.method_label.text = 'GPS failed, using IP Geolocation'
                    self.tracking_event = Clock.schedule_interval(self.update_location_ip, 5)
                    self.update_location_ip(0)
            else:
                # Use IP geolocation
                self.tracking_event = Clock.schedule_interval(self.update_location_ip, 5)
                self.update_location_ip(0)
    
    def stop_tracking(self, instance):
        if self.tracking_active:
            self.tracking_active = False
            self.start_button.disabled = False
            self.stop_button.disabled = True
            self.status_label.text = 'Tracking stopped'
            
            # Stop GPS if using it
            if self.using_gps:
                try:
                    gps.stop()
                except:
                    pass
            
            # Cancel all scheduled events
            if self.tracking_event:
                self.tracking_event.cancel()
                self.tracking_event = None
                
            if self.gps_timeout_event:
                self.gps_timeout_event.cancel()
                self.gps_timeout_event = None
    
    def check_gps_timeout(self, dt):
        # If GPS didn't provide location within timeout, fall back to IP
        if self.tracking_active and self.using_gps and not self.last_known_location:
            self.status_label.text = 'GPS timeout, falling back to IP'
            self.using_gps = False
            self.method_label.text = 'Using IP Geolocation (Low Accuracy)'
            
            try:
                gps.stop()
            except:
                pass
                
            if self.tracking_event:
                self.tracking_event.cancel()
                
            self.tracking_event = Clock.schedule_interval(self.update_location_ip, 5)
            self.update_location_ip(0)
    
    def check_location_updates(self, dt):
        # Regular check for location updates
        if self.tracking_active:
            if not self.last_known_location:
                self.status_label.text = 'Waiting for location...'
    
    def on_gps_location(self, **kwargs):
        # Called by the GPS provider when location is available
        if not self.tracking_active:
            return
        
        try:
            # Cancel the GPS timeout if it's still active
            if self.gps_timeout_event:
                self.gps_timeout_event.cancel()
                self.gps_timeout_event = None
                
            # Get location data
            lat = kwargs.get('lat', 0.0)
            lon = kwargs.get('lon', 0.0)
            accuracy = kwargs.get('accuracy', 0.0)
            timestamp = int(time.time())
            
            # Save last known location
            self.last_known_location = (lat, lon)
            self.location_accuracy = f"{accuracy:.1f} meters" if accuracy else "Unknown"
            
            # Update UI with full precision coordinates
            self.coords_label.text = f'Lat: {lat:.8f}\nLong: {lon:.8f}'
            self.status_label.text = 'GPS location updated'
            self.accuracy_label.text = f'Accuracy: {self.location_accuracy}'
            
            # Try to get address (reverse geocoding)
            self.get_address(lat, lon)
            
            # Update Firebase
            self.update_firebase_record(lat, lon, timestamp, "GPS", accuracy)
            
        except Exception as e:
            self.status_label.text = f'GPS Error: {str(e)}'
            # If GPS fails during tracking, switch to IP geolocation
            if self.tracking_active and self.using_gps:
                self.using_gps = False
                self.method_label.text = 'GPS failed, using IP Geolocation'
                # Cancel GPS tracking event
                if self.tracking_event:
                    self.tracking_event.cancel()
                # Start IP geolocation
                self.tracking_event = Clock.schedule_interval(self.update_location_ip, 5)
                self.update_location_ip(0)
    
    def update_location_ip(self, dt):
        # IP geolocation method (fallback)
        if not self.tracking_active:
            return
            
        try:
            # Get location using IP geolocation
            # Try multiple services for better accuracy
            g = geocoder.ip('me')
            
            if g.ok:
                lat = g.lat
                lon = g.lng
                timestamp = int(time.time())
                
                # Save last known location
                self.last_known_location = (lat, lon)
                self.location_accuracy = "~1000 meters (IP-based)"
                
                # Update UI
                self.coords_label.text = f'Lat: {lat:.8f}\nLong: {lon:.8f}'
                self.status_label.text = 'IP location updated'
                self.accuracy_label.text = f'Accuracy: {self.location_accuracy}'
                
                # Try to get address
                self.get_address(lat, lon)
                
                # Update Firebase
                self.update_firebase_record(lat, lon, timestamp, "IP", 1000)
            else:
                self.status_label.text = 'Failed to get IP location'
                
                # Try alternative service
                try:
                    g2 = geocoder.ipinfo('me')
                    if g2.ok:
                        lat = g2.lat
                        lon = g2.lng
                        timestamp = int(time.time())
                        
                        self.last_known_location = (lat, lon)
                        self.location_accuracy = "~1000 meters (IP-based)"
                        
                        self.coords_label.text = f'Lat: {lat:.8f}\nLong: {lon:.8f}'
                        self.status_label.text = 'IP location updated (alternative)'
                        self.accuracy_label.text = f'Accuracy: {self.location_accuracy}'
                        
                        self.get_address(lat, lon)
                        self.update_firebase_record(lat, lon, timestamp, "IP-alt", 1000)
                except:
                    pass
        except Exception as e:
            self.status_label.text = f'IP Error: {str(e)}'
    
    def get_address(self, lat, lon):
        try:
            # Get address from coordinates (reverse geocoding)
            g = geocoder.osm([lat, lon], method='reverse')
            if g.ok:
                self.address_label.text = g.address
            else:
                self.address_label.text = 'Address not available'
        except:
            self.address_label.text = 'Address lookup failed'
    
    def update_firebase_record(self, lat, lon, timestamp, method, accuracy=None):
        try:
            # Prepare data for Firebase
            location_data = {
                "deviceId": self.device_id,
                "latitude": lat,
                "longitude": lon,
                "timestamp": timestamp,
                "method": method,
                "accuracy": accuracy if accuracy is not None else "Unknown"
            }
            
            # Use PUT request to update the specific node for this device
            device_url = f"{self.firebase_base_url}/locations/{self.device_id}.json"
            
            # Use PUT to replace existing data for this device ID
            response = requests.put(device_url, json=location_data)
            
            if response.status_code == 200:
                self.status_label.text = f'Location updated in Firebase'
            else:
                self.status_label.text = f'Firebase error: {response.status_code}'
        except Exception as e:
            self.status_label.text = f'Firebase error: {str(e)}'

if __name__ == '__main__':
    LocationTrackerApp().run()