from phi.agent import Agent
from phi.tools.yfinance import YFinanceTools
from phi.model.google import Gemini

# Initialize agent with YFinanceTools
agent = agent = Agent(
    model=Gemini(id="gemini-1.5-flash"),
    debug_mode=True,
    tools=[YFinanceTools(historical_prices=True, stock_price=False)],
    analyst_recommendations=True,
    show_tool_calls=True,
    description="You are a commodity analyst that fetches historical prices for commodities",
    instructions=[
        "The user will ask for historical data for a specific commodity",
        "Map the commodity name to its Yahoo Finance ticker:",
        "   - Energy:",
        "       - Crude Oil → 'CL=F'",
        "       - Natural Gas → 'NG=F'",
        "       - Brent Oil → 'BZ=F'",
        "       - Gasoline → 'RB=F'",
        "       - Coal → 'MTF=F'",
        "   - Metals:",
        "       - Gold → 'GC=F'",
        "       - Silver → 'SI=F'",
        "       - Copper → 'HG=F'",
        "       - Aluminum → 'ALI=F'",
        "       - Platinum → 'PL=F'",
        "   - Agriculture:",
        "       - Coffee → 'KC=F'",
        "       - Sugar → 'SB=F'",
        "       - Cotton → 'CT=F'",
        "       - Soybeans → 'ZS=F'",
        "       - Wheat → 'ZW=F'",
        "       - Corn → 'ZC=F'",
        "If the user provides a custom ticker (e.g., 'BTC-USD'), use it directly.",
        "Always return historical data in a structured markdown table.",
        "If no time period is specified, default to '30d' (last 30 days).",
        "If a commodity isn't listed here but exists on Yahoo Finance, try searching for its ticker.",
        "Also predict the price changes of next 10 days based on the historical data.",
    ],
)

# Example: Let the user input the commodity
user_input = input(
    "Which commodity do you want historical data for? (e.g., 'Gold', 'Silver', 'CL=F'): ")
agent.print_response(
    f"Get the last 30 days of historical prices for {user_input}", markdown=True)
