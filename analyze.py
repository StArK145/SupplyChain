from phi.agent import Agent
from phi.tools.sql import SQLTools
from phi.model.google import Gemini

db_url = "sqlite:///db.sqlite3"  # Adjust path if necessary
agent = Agent(tools=[SQLTools(db_url=db_url)],model=Gemini(id="gemini-2.0-flash-exp", temperature=0.4))

agent.print_response(
    f"""Analyze all feedback comments for supplier with {ID} from the supplier_supplierreview table and provide ONLY the final recommendation based on:
    1. The key points from each feedback
    2. Common themes across all feedbacks
    3. Overall supplier performance assessment
    4. Specific strengths and weaknesses
    5. Areas needing improvement
    
    Present JUST the recommendation in one concise paragraph.""",
    markdown=True
)