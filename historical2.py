from phi.agent import Agent
from phi.tools.yfinance import YFinanceTools
from phi.model.google import Gemini

# Initialize agent with expanded YFinanceTools
agent = Agent(
    model=Gemini(id="gemini-1.5-flash"),
    debug_mode=True,
    tools=[YFinanceTools(
        historical_prices=True,
        analyst_recommendations=True,  # Enable analyst insights
        company_news=True,            # Get latest news
        technical_indicators=True,    # Add RSI/MACD for trends
    )],
    show_tool_calls=True,
    description="You are a supply chain business analyst that provides procurement recommendations based on commodity data.",
    instructions=[
        "1. Map commodities to Yahoo Finance tickers (e.g., Sugar → 'SB=F').",
        "2. Fetch:",
        "   - Analyst recommendations (Buy/Hold/Sell)",
        "   - Relevant news headlines",
        "3. Return a structured report with:",
        "   - Price trend analysis",
        "   - Procurement recommendations (e.g., 'Buy now', 'Delay purchase')",
        "   - Risk assessment (e.g., 'High volatility expected')",
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
"       - Lead → 'Tell that there is no future options for Lead Commodity'",  # Placeholder - verify correct symbol
"       - Nickel → '^SPGSIK'",  
"       - Tin → 'TINS.JK'",  # Placeholder - verify correct symbol
"       - Zinc → 'ZINC-USD'",  
"       - Antimony → 'UAMY'",  # Placeholder - verify correct symbol
"       - Manganese → 'MN.V'",  # Placeholder - verify correct symbol
"       - Titanium → 'Tell that there is no future options for Lead Commodity'",  # Placeholder - verify correct symbol
"       - Tungsten → 'TGN.AX'",  # Placeholder - verify correct symbol
"       - Steel → 'HRC=F'",  # Placeholder - verify correct symbol
"   - Agriculture:",
"       - Coffee → 'KC=F'",
"       - Sugar → 'SB=F'",
"       - Cotton → 'CT=F'",
"       - Soybeans → 'ZS=F'",
"       - Wheat → 'ZW=F'",
"       - Corn → 'ZC=F'",
"       - Copra → 'Tell that there is no future options for Lead Commodity'",  # Placeholder - verify correct symbol
"       - Hides → 'Tell that there is no future options for Lead Commodity'",  # Placeholder - verify correct symbol
"       - Rubber → 'GT'",  # Placeholder - verify correct symbol
"       - Wool → 'Tell that there is no future options for Lead Commodity'",  # Placeholder - verify correct symbol
"       - Peanuts → 'PEANUTS=F'",  # Placeholder - verify correct symbol
"       - Tea → 'TEA=F'",  # Placeholder - verify correct symbol
"       - Tobacco → 'TOBACCO=F'",  # Placeholder - verify correct symbol
"   - Other:",
"       - Other Agriculture → 'OTHER_AGRI=F'",  # Placeholder
"       - Other Metals → 'OTHER_METALS=F'", 
"If Found Nothing , Display there is no Future Option For required Commodity" # Placeholder
    ],
)

# Get user input and generate full analysis
user_input = input("Which commodity do you want analysis for? (e.g., 'Coffee', 'Copper', 'CL=F'): ")
agent.print_response(
    f"Provide a full business analyst report for {user_input} including price trends, recommendations, and risks",
    markdown=True
)