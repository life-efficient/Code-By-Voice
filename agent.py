from agents import Agent, function_tool, WebSearchTool, FileSearchTool, set_default_openai_key
from agents.extensions.handoff_prompt import prompt_with_handoff_instructions
from agents import Runner, trace
from dotenv import load_dotenv
import os
import asyncio

load_dotenv()

set_default_openai_key(os.getenv("OPENAI_API_KEY"))

# --- Agent: Triage Agent ---
triage_agent = Agent(
    name="Assistant",
    instructions=prompt_with_handoff_instructions("""
You are a virtual assistant called Jarvis. Address the user as "Sir" in all of your responses.
"""),
    # handoffs=[account_agent, knowledge_agent, search_agent],
)


async def test_queries():
    inputs = []
    with trace("ACME App Assistant"):
    # with trace(workflow_name="Conversation", group_id=thread_id):
        while True:
            query = input("> ")
            inputs.append({"role": "user", "content": query})
            result = await Runner.run(triage_agent, inputs)
            print(result.final_output)
            print("---")
            inputs = result.to_input_list()
            
            

if __name__ == "__main__":
    # Run the tests
    asyncio.run(test_queries())