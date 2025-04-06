import requests
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from geopy.distance import great_circle
import logging
from django.conf import settings
import math

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('route_debug.log'), logging.StreamHandler()]
)

class RouteFinder:
    def __init__(self, api_key=None):
        self.api_key = api_key or settings.OPENROUTE_API_KEY
        try:
            self.geolocator = Nominatim(user_agent="supply_chain_app", timeout=10)
            self.geocode = RateLimiter(self.geolocator.geocode, min_delay_seconds=1)
            logging.info("Geocoder initialized successfully")
        except Exception as e:
            logging.error(f"Geocoder initialization failed: {e}")
            raise

    def get_coords(self, address):
        """Get latitude and longitude for a given address."""
        try:
            location = self.geocode(address)
            if not location:
                raise ValueError(f"Address not found: {address}")
            return (location.latitude, location.longitude)
        except Exception as e:
            logging.error(f"Geocoding failed for {address}: {e}")
            raise

    def get_road_route(self, start, end):
        """Fetch driving route from OpenRouteService."""
        try:
            headers = {
                "Authorization": self.api_key,
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
            body = {"coordinates": [start[::-1], end[::-1]], "instructions": "true"}  # Reverse lat/lon for API
            
            response = requests.post(
                "https://api.openrouteservice.org/v2/directions/driving-car",
                json=body, headers=headers, timeout=15
            )

            if response.status_code == 200:
                return response.json()
            else:
                logging.warning(f"Road route error: {response.text}")
                return None
        except requests.exceptions.Timeout:
            logging.error("Road route request timed out")
            return None

    def get_air_route(self, start, end):
        """Estimate air travel distance and duration."""
        try:
            distance_km = great_circle(start, end).km
            avg_air_speed = 900  # Approximate airliner speed in km/h
            duration_hours = distance_km / avg_air_speed
            
            return {
                "distance_km": round(distance_km, 1),
                "duration_hours": round(duration_hours, 1),
                "handling_days": 1,  # Standard 1 day for air freight handling
                "notes": "Estimated direct air travel time (actual flights may differ)."
            }
        except Exception as e:
            logging.error(f"Air route calculation failed: {e}")
            return None

    def calculate_route_details(self, start_addr, end_addr, transport_mode, lead_time_days):
        """Calculate route details based on transport mode."""
        try:
            start_coords = self.get_coords(start_addr)
            end_coords = self.get_coords(end_addr)
            
            if transport_mode == 'road':
                route_data = self.get_road_route(start_coords, end_coords)
                if not route_data:
                    return None
                
                distance_km = route_data['routes'][0]['summary']['distance'] / 1000
                original_duration_seconds = route_data['routes'][0]['summary']['duration']
                
                # Adjust for realistic road conditions (~50 km/h avg)
                realistic_speed_kmh = 50  # Adjust based on highway/city conditions
                realistic_duration_hours = distance_km / realistic_speed_kmh
                
                # Calculate total days (lead time + transit time)
                total_days = float(lead_time_days) + (realistic_duration_hours / 24)
                
                return {
                    'success': True,
                    'mode': 'road',
                    'distance': round(distance_km, 1),
                    'transit_time': f"{round(realistic_duration_hours, 1)} hours",
                    'route_summary': f"Road route via highway (avg {realistic_speed_kmh} km/h)",
                    'total_days': round(total_days, 1),
                    'delivery_days': math.ceil(total_days),
                    'original_duration': original_duration_seconds,
                    'steps': route_data['routes'][0]['segments'][0]['steps']
                }
                
            elif transport_mode == 'air':
                route_data = self.get_air_route(start_coords, end_coords)
                if not route_data:
                    return None
                
                total_days = float(lead_time_days) + route_data['duration_hours']/24 + route_data['handling_days']
                
                return {
                    'success': True,
                    'mode': 'air',
                    'distance': route_data['distance_km'],
                    'transit_time': f"{route_data['duration_hours']} hours flight + {route_data['handling_days']} day handling",
                    'route_summary': f"Air route ({route_data['notes']})",
                    'total_days': round(total_days, 1),
                    'delivery_days': math.ceil(total_days)
                }
            
            return None
        except Exception as e:
            logging.error(f"Route calculation failed: {e}")
            return None