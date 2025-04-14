# manufacturer/utils.py
import os
from typing import Dict, Optional
from phi.agent import Agent
from phi.model.google import Gemini
from phi.tools.tavily import TavilyTools
from datetime import datetime
import re
from phi.tools.yfinance import YFinanceTools


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
                numbers = [float(num) for num in re.findall(
                    r'\d+\.?\d*', response.content)]
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


class CommodityAnalytics:
    """Utility class to fetch commodity analytics"""

    @staticmethod
    def get_analytics(commodity: str, category: str) -> Dict[str, str]:
        try:
            agent = Agent(
                model=Gemini(id="gemini-1.5-flash", temperature=0.2),
                debug_mode=True,
                markdown=True,
                tools=[YFinanceTools(
                    historical_prices=True,
                    analyst_recommendations=True,
                    company_news=True,
                    technical_indicators=True,
                )],
                show_tool_calls=True,
                description="You are a supply chain business analyst that provides procurement recommendations based on commodity data.",
                instructions=[
                    "1. Map commodities to Yahoo Finance tickers.",
                    "2. Fetch analyst recommendations, news headlines, and technical indicators.",
                    "3. Return a structured report with:",
                    "   - Price trend analysis",
                    "   - Procurement recommendations",
                    "   - Risk assessment",
                    "   - Key news affecting prices",
                    "Map the commodity name to its Yahoo Finance ticker:",
                    "   - Energy:",
                    "       - Crude Oil → 'CL=F'",
                    "       - Natural Gas → 'NG=F'",
                    "       - Brent Oil → 'BZ=F'",
                    "       - Gasoline → 'RB=F'",
                    "       - Coal → 'MTF=F'",
                    "       - Diesel → 'CL=F'",
                    "   - Metals:",
                    "       - Gold → 'GC=F'",
                    "       - Silver → 'SI=F'",
                    "       - Copper → 'HG=F'",
                    "       - Aluminum → 'ALI=F'",
                    "       - Platinum → 'PL=F'",
                    "       - Iron → '3047.HK'",
                    # Placeholder - verify correct symbol
                    "       - Lead → 'Tell that there is no future options for Lead Commodity'",
                    "       - Nickel → '^SPGSIK'",
                    "       - Tin → 'TINS.JK'",  # Placeholder - verify correct symbol
                    "       - Zinc → 'ZINC-USD'",
                    "       - Antimony → 'UAMY'",  # Placeholder - verify correct symbol
                    "       - Manganese → 'MN.V'",  # Placeholder - verify correct symbol
                    # Placeholder - verify correct symbol
                    "       - Titanium → 'Tell that there is no future options for Lead Commodity'",
                    "       - Tungsten → 'TGN.AX'",  # Placeholder - verify correct symbol
                    "       - Steel → 'HRC=F'",  # Placeholder - verify correct symbol
                    "   - Agriculture:",
                    "       - Coffee → 'KC=F'",
                    "       - Sugar → 'SB=F'",
                    "       - Cotton → 'CT=F'",
                    "       - Soybeans → 'ZS=F'",
                    "       - Wheat → 'ZW=F'",
                    "       - Corn → 'ZC=F'",
                    # Placeholder - verify correct symbol
                    "       - Copra → 'Tell that there is no future options for Lead Commodity'",
                    # Placeholder - verify correct symbol
                    "       - Hides → 'Tell that there is no future options for Lead Commodity'",
                    "       - Rubber → 'GT'",  # Placeholder - verify correct symbol
                    # Placeholder - verify correct symbol
                    "       - Wool → 'Tell that there is no future options for Lead Commodity'",
                    "       - Peanuts → 'PEANUTS=F'",  # Placeholder - verify correct symbol
                    "       - Tea → 'TEA=F'",  # Placeholder - verify correct symbol
                    "       - Tobacco → 'TOBACCO=F'",  # Placeholder - verify correct symbol
                    "   - Other:",
                    "       - Other Agriculture → 'OTHER_AGRI=F'",  # Placeholder
                    "       - Other Metals → 'OTHER_METALS=F'",
                    "If Found Nothing , Display there is no Future Option For required Commodity"
                    "If no data found, state: 'No future options available for this commodity'"
                ]
            )

            response = agent.run(
                f"Provide a full business analyst report for {commodity} (category: {category}) "
                "including price trends, recommendations, and risks",
                markdown=True
            )

            return {"analytics": response.content if response else "No analytics available"}

        except Exception as e:
            return {"error": str(e)}
