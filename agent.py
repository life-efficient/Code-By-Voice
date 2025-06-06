from agents import Agent, function_tool, WebSearchTool, FileSearchTool, set_default_openai_key
from agents.extensions.handoff_prompt import prompt_with_handoff_instructions
from dotenv import load_dotenv
import os
from tool_factory import generated_function_tools

load_dotenv()

set_default_openai_key(os.getenv("OPENAI_API_KEY"))

# --- Agent: Triage Agent ---
jarvis = Agent(
    name="Jarvis",
    instructions=prompt_with_handoff_instructions("""
You are a virtual assistant called Jarvis. You're a fast talking, witty, British assistant. 
                                                  
Address the user as "Sir" in all of your responses.
                                                  
When the conversation begins:
- start by asking the user if they have any major updates regarding any projects
- then ask them if there's any updates from people in their network that you should know about
                                                  
"""),
    tools=generated_function_tools,
    # handoffs=[account_agent, knowledge_agent, search_agent],
)
