import requests
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import logging
from functools import partial

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class CarbonEmissionsCalculator:
    # Emission factors (grams CO2 per km) for different vehicle types
    EMISSION_FACTORS = {
        'small_truck': 250,   # 3.5-7.5 tons
        'medium_truck': 400,  # 7.5-16 tons
        'large_truck': 600,   # 16-32 tons
        'articulated_truck': 900  # >32 tons
    }

    def __init__(self, api_key):
        self.api_key = api_key
        try:
            self.geolocator = Nominatim(
                user_agent="carbon_calculator",
                timeout=10
            )
            self.geocode = RateLimiter(
                self.geolocator.geocode,
                min_delay_seconds=1
            )
            logging.info("Carbon emissions calculator initialized")
        except Exception as e:
            logging.error(f"Initialization failed: {e}")
            raise

    def get_coords(self, address):
        """Get coordinates for an address"""
        try:
            location = self.geocode(address)
            if not location:
                raise ValueError(f"Address not found: {address}")
            return [location.longitude, location.latitude]
        except Exception as e:
            logging.error(f"Geocoding failed for {address}: {e}")
            raise

    def get_route_distance(self, start_addr, end_addr):
        """Get route distance between two addresses"""
        try:
            start = self.get_coords(start_addr)
            end = self.get_coords(end_addr)
            
            headers = {
                "Authorization": self.api_key,
                "Accept": "application/json, application/geo+json",
                "Content-Type": "application/json"
            }
            
            body = {
                "coordinates": [start, end],
                "instructions": "false"
            }
            
            response = requests.post(
                "https://api.openrouteservice.org/v2/directions/driving-car",
                json=body,
                headers=headers,
                timeout=15
            )
            
            if response.status_code != 200:
                error_msg = response.json().get('error', response.text)
                raise Exception(f"API Error: {error_msg}")
                
            distance_km = response.json()['routes'][0]['summary']['distance'] / 1000
            return distance_km
            
        except Exception as e:
            logging.error(f"Route calculation failed: {e}")
            raise

    def calculate_emissions(self, start_addr, end_addr, vehicle_type, vehicle_count=1, load_factor=1.0, empty_return=False):
        """
        Calculate carbon emissions for a road shipment
        
        Args:
            start_addr: Starting address (string)
            end_addr: Destination address (string)
            vehicle_type: One of EMISSION_FACTORS keys
            vehicle_count: Number of vehicles used (int)
            load_factor: Utilization percentage (0.0-1.0)
            empty_return: Include empty return trip (bool)
            
        Returns:
            Dictionary with emissions data
        """
        if vehicle_type not in self.EMISSION_FACTORS:
            raise ValueError(f"Invalid vehicle type. Choose from: {list(self.EMISSION_FACTORS.keys())}")
        
        if not 0 < load_factor <= 1:
            raise ValueError("Load factor must be between 0 and 1")
        
        # Get route distance
        distance_km = self.get_route_distance(start_addr, end_addr)
        
        # Calculate emissions (grams CO2 per km × km × vehicles / load factor)
        emissions_grams = (self.EMISSION_FACTORS[vehicle_type] * distance_km * vehicle_count) / load_factor
        
        # Add return trip if needed
        if empty_return:
            emissions_grams *= 2
            distance_km *= 2
        
        return {
            'distance_km': round(distance_km, 2),
            'total_emissions_kg': round(emissions_grams / 1000, 2),
            'emissions_per_vehicle_kg': round((emissions_grams / vehicle_count) / 1000, 2),
            'vehicle_type': vehicle_type,
            'vehicle_count': vehicle_count,
            'load_percentage': round(load_factor * 100, 1)
        }

def print_emissions_report(data):
    """Display emissions data in readable format"""
    print("\n=== Carbon Emissions Report ===")
    print(f"Route Distance: {data['distance_km']} km")
    print(f"Vehicle Type: {data['vehicle_type']} ({data['vehicle_count']} vehicles)")
    print(f"Load Percentage: {data['load_percentage']}%")
    print("\nTotal CO2 Emissions:")
    print(f"  - {data['total_emissions_kg']} kg")
    print(f"  - {data['total_emissions_kg'] / 1000:.3f} metric tons")
    print(f"\nPer Vehicle: {data['emissions_per_vehicle_kg']} kg CO2")

def main():
    print("Road Transport Carbon Emissions Calculator")
    print("Vehicle Types Available:")
    print("1. Small Truck (3.5-7.5 tons)")
    print("2. Medium Truck (7.5-16 tons)")
    print("3. Large Truck (16-32 tons)")
    print("4. Articulated Truck (>32 tons)")
    
    try:
        # Get your API key from https://openrouteservice.org
        API_KEY = "5b3ce3597851110001cf62489fb869a41b884c29a4f0adb4581c6209"  # Replace with your actual key
        
        if not API_KEY or "YOUR_API_KEY_HERE" in API_KEY:
            raise ValueError("Please provide a valid OpenRouteService API key")
        
        calculator = CarbonEmissionsCalculator(API_KEY)
        
        # Get user input
        start_addr = input("\nEnter origin address (e.g., 'New York, NY'): ")
        end_addr = input("Enter destination address (e.g., 'Boston, MA'): ")
        
        vehicle_choice = input("Select vehicle type (1-4): ")
        vehicle_types = ['small_truck', 'medium_truck', 'large_truck', 'articulated_truck']
        vehicle_type = vehicle_types[int(vehicle_choice)-1]
        
        vehicle_count = int(input("Number of vehicles: "))
        load_percent = float(input("Load percentage (1-100): "))
        empty_return = input("Include empty return trip? (y/n): ").lower() == 'y'
        
        # Calculate emissions
        result = calculator.calculate_emissions(
            start_addr=start_addr,
            end_addr=end_addr,
            vehicle_type=vehicle_type,
            vehicle_count=vehicle_count,
            load_factor=load_percent/100,
            empty_return=empty_return
        )
        
        # Display results
        print_emissions_report(result)
        
    except Exception as e:
        print(f"\nError: {str(e)}")
        print("Please check your inputs and try again.")

if __name__ == "__main__":
    main()