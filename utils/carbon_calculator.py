# manufacturer/utils/carbon_calculator.py
import requests
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

class CarbonEmissionsCalculator:
    # Emission factors (grams CO2 per km) for different vehicle types
    EMISSION_FACTORS = {
        'small_truck': 250,   # 3.5-7.5 tons
        'medium_truck': 400,  # 7.5-16 tons
        'large_truck': 600,   # 16-32 tons
        'articulated_truck': 900  # >32 tons
    }

    def __init__(self):
        self.api_key = settings.OPENROUTE_API_KEY
        try:
            self.geolocator = Nominatim(user_agent="supply_chain_carbon", timeout=10)
            self.geocode = RateLimiter(self.geolocator.geocode, min_delay_seconds=1)
        except Exception as e:
            logger.error(f"Carbon calculator init failed: {e}")
            raise

    def calculate_road_emissions(self, start_addr, end_addr, vehicle_type, vehicle_count=1, load_percentage=100, empty_return=False):
        """Calculate carbon emissions for road transport"""
        try:
            # Get coordinates
            start_location = self.geocode(start_addr)
            end_location = self.geocode(end_addr)
            
            if not start_location or not end_location:
                raise ValueError("Could not geocode addresses")
                
            # Get route distance
            headers = {
                "Authorization": self.api_key,
                "Content-Type": "application/json"
            }
            body = {
                "coordinates": [
                    [start_location.longitude, start_location.latitude],
                    [end_location.longitude, end_location.latitude]
                ],
                "instructions": "false"
            }
            
            response = requests.post(
                "https://api.openrouteservice.org/v2/directions/driving-car",
                headers=headers,
                json=body,
                timeout=15
            )
            
            if response.status_code != 200:
                raise ValueError(f"Route API error: {response.text}")
                
            distance_km = response.json()['routes'][0]['summary']['distance'] / 1000
            
            # Calculate emissions
            load_factor = load_percentage / 100
            emissions_grams = (self.EMISSION_FACTORS[vehicle_type] * distance_km * vehicle_count) / load_factor
            
            if empty_return:
                emissions_grams *= 2
                distance_km *= 2
            
            return {
                'success': True,
                'distance_km': round(distance_km, 2),
                'total_emissions_kg': round(emissions_grams / 1000, 2),
                'emissions_per_vehicle_kg': round((emissions_grams / vehicle_count) / 1000, 2),
                'equivalent_trees': round(emissions_grams / 21000, 1)  # 21kg CO2 per tree per year
            }
            
        except Exception as e:
            logger.error(f"Carbon calculation failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }