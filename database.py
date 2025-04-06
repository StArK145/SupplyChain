from phi.agent import Agent
from phi.tools.sql import SQLTools
from phi.model.google import Gemini

db_url = "sqlite:///db.sqlite3"  # Adjust path if necessary
agent = Agent(tools=[SQLTools(db_url=db_url)],model=Gemini(id="gemini-2.0-flash-exp", temperature=0.4))

agent.print_response("List the content and the data inside manufacturer_manufacturer table in the database. Tell me about contents of one of the tables", markdown=True)
