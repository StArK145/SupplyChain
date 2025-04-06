import os
from typing import Dict, Optional
from phi.agent import Agent
from phi.model.google import Gemini
from phi.tools.tavily import TavilyTools
from datetime import datetime
import re

class CommodityPriceFetcher:
    """
    A class to fetch estimated commodity price ranges using Tavily.
    """
    
    SYSTEM_PROMPT = """You are a specialized AI agent that estimates commodity price ranges.
    Analyze the available data and provide ONLY a reasonable price RANGE in USD per kg for the Indian region.
    Format should be: 'X-Y USD/kg' where X is the lower estimate and Y is the higher estimate.
    If insufficient data exists, return 'Not available'."""
    
    def __init__(self):
        self.api_keys_configured = self._check_api_keys()
        
    def _check_api_keys(self) -> bool:
        """Verify required API keys are present."""
        tavily_key = os.getenv("TAVILY_API_KEY")
        google_key = os.getenv("GOOGLE_API_KEY")
        
        if not tavily_key or not google_key:
            print("Warning: Missing API keys. Some services may not work.")
            return False
        return True
    
    def _create_agent(self) -> Optional[Agent]:
        """Create an agent with Tavily tool."""
        try:
            return Agent(
                model=Gemini(id="gemini-2.0-flash-exp", temperature=0.4),
                system_prompt=self.SYSTEM_PROMPT,
                tools=[TavilyTools(api_key=os.getenv("TAVILY_API_KEY"))],
                debug_mode=True,
                tool_config={
                    "TavilyTools": {
                        "max_results": 10,
                        "include_raw_content": True,
                        "search_depth": "advanced"
                    }
                }
            )
        except Exception as e:
            print(f"Error creating Tavily agent: {str(e)}")
            return None
    
    def _generate_estimate_range(self, price_data: str) -> str:
        """Generate a reasonable price range from raw price data."""
        try:
            # Extract all numeric values from the response
            numbers = [float(num) for num in re.findall(r'\d+\.?\d*', price_data)]
            if not numbers:
                return "Not available"
            
            min_val = min(numbers)
            max_val = max(numbers)
            
            # Calculate a reasonable range (20% variance)
            range_size = max(0.1, (max_val - min_val) * 0.2)  # Ensure minimum range size
            lower_bound = max(0, min_val - range_size)
            upper_bound = max_val + range_size
            
            return f"{lower_bound:.2f}-{upper_bound:.2f} USD/kg"
        except:
            return "Not available"
    
    def fetch_price(self, commodity_name: str) -> Dict[str, str]:
        """
        Fetch estimated commodity price range using Tavily.
        
        Args:
            commodity_name: Name of the commodity to search for
            
        Returns:
            Dictionary with Tavily's price range estimate
        """
        results = {}
        
        try:
            print("\nAttempting to fetch price using Tavily...")
            agent = self._create_agent()
            if not agent:
                results["Tavily"] = "Agent initialization failed"
                return results
                
            query = (f"Current market price range of {commodity_name} in USD per kg "
                    f"from Indian markets or Indian commodity exchanges. "
                    f"Provide comprehensive data including spot prices, futures prices.")
            
            response = agent.run(query, max_tokens=1500)
            
            if response and response.content:
                content = response.content.strip()
                print(f"Raw response from Tavily: {content[:1000]}...")
                
                # Generate estimate range from the response
                price_range = self._generate_estimate_range(content)
                results["Tavily"] = price_range
            else:
                results["Tavily"] = "No response received"
                
        except Exception as e:
            results["Tavily"] = f"Error: {str(e)}"
            print(f"Error with Tavily: {str(e)}")
            
        return results
    
    def format_results(self, results: Dict[str, str]) -> str:
        """Format the results for display."""
        valid_results = {}
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        for source, price in results.items():
            if "-" in price and "USD/kg" in price:  # Check for range format
                valid_results[source] = price
                
        if not valid_results:
            return f"As of {timestamp}: Could not retrieve valid price range."
            
        formatted = [f"As of {timestamp}:"]
        for source, price in valid_results.items():
            formatted.append(f"{source} estimate: {price}")
            
        formatted.append("\nNote: This is an estimated range and actual prices may vary.")
        return "\n".join(formatted)


def main():
    print("Commodity Price Range Estimator (Tavily)")
    print("----------------------------------------")
    
    fetcher = CommodityPriceFetcher()
    commodity_name = input("Enter commodity name (e.g., steel, rubber, cotton): ").strip()
    
    if not commodity_name:
        print("Please enter a valid commodity name.")
        return
        
    print(f"\nEstimating price range for {commodity_name}...")
    results = fetcher.fetch_price(commodity_name)
    output = fetcher.format_results(results)
    print(f"\n{output}")


if __name__ == "__main__":
    main()