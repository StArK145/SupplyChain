from phi.agent import Agent
from phi.tools.sql import SQLTools
from phi.model.google import Gemini

db_url = "sqlite:///db.sqlite3"  # Adjust path if necessary
agent = Agent(tools=[SQLTools(db_url=db_url)], model=Gemini(id="gemini-2.0-flash-exp", temperature=0.4))

# Your structured prompt
analysis_prompt = """Analyze the 'manufacturer_quoterequest' table to:
1. Extract product details (name, category, specifications) and request patterns
2. Identify high-demand products/categories based on:
   - Frequency of requests
   - Quantity requested (if available)
   - Recent request trends
3. Generate an ordered list (high to low demand) with:
   - Top categories (with justification)
   - Top products in each category
4. Format output as:
**Top High-Demand Product Categories:**
1. [Category Name]
   - Reason: [justification]
   - Top Products:
     - [Product 1]
     - [Product 2]
2. [Category Name]..."""

agent.print_response(
    analysis_prompt,
    markdown=True
)