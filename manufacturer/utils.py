# manufacturer/utils.py
import os
from typing import Dict, Optional
from phi.agent import Agent
from phi.model.google import Gemini
from phi.tools.tavily import TavilyTools
from datetime import datetime
import re

class CommodityPriceFetcher:
    """Utility class to fetch commodity prices"""
    
    SYSTEM_PROMPT = """You are a specialized AI agent that estimates commodity price ranges.
    Analyze the available data and provide ONLY a reasonable price RANGE in USD per kg for the Indian region.
    Format should be: 'X-Y USD/kg' where X is the lower estimate and Y is the higher estimate.
    If insufficient data exists, return 'Not available'."""
    
    def __init__(self):
        self.api_keys_configured = self._check_api_keys()
        
    def _check_api_keys(self) -> bool:
        """Check for required API keys"""
        return bool(os.getenv("TAVILY_API_KEY")) and bool(os.getenv("GOOGLE_API_KEY"))
    
    def fetch_price(self, commodity_name: str) -> Dict[str, str]:
        """Fetch price for a commodity"""
        if not self.api_keys_configured:
            return {"error": "API keys not configured"}
            
        try:
            agent = Agent(
                model=Gemini(id="gemini-2.0-flash-exp", temperature=0.4),
                system_prompt=self.SYSTEM_PROMPT,
                tools=[TavilyTools(api_key=os.getenv("TAVILY_API_KEY"))],
                debug_mode=True
            )
            
            query = f"Current market price range of {commodity_name} in USD per kg from Indian markets"
            response = agent.run(query, max_tokens=500)
            
            if response and response.content:
                # Extract price range from response
                numbers = [float(num) for num in re.findall(r'\d+\.?\d*', response.content)]
                if numbers:
                    min_price = min(numbers)
                    max_price = max(numbers)
                    return {
                        "price": f"{min_price:.2f}-{max_price:.2f} USD/kg",
                        "source": "Tavily"
                    }
            return {"price": "Not available"}
            
        except Exception as e:
            return {"error": str(e)}