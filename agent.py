from agents import Agent, function_tool, WebSearchTool, FileSearchTool, set_default_openai_key
from agents.extensions.handoff_prompt import prompt_with_handoff_instructions
from dotenv import load_dotenv
import os

load_dotenv()

set_default_openai_key(os.getenv("OPENAI_API_KEY"))

# --- Agent: Triage Agent ---
jarvis = Agent(
    name="Jarvis",
    instructions=prompt_with_handoff_instructions("""
You are a virtual assistant called Jarvis. Address the user as "Sir" in all of your responses.
"""),
    # handoffs=[account_agent, knowledge_agent, search_agent],
)


