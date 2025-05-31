from agents import Runner, trace
import asyncio

from agent import jarvis

async def text_conversation_loop():
    inputs = []
    with trace("ACME App Assistant"):
    # with trace(workflow_name="Conversation", group_id=thread_id):
        while True:
            query = input("> ")
            inputs.append({"role": "user", "content": query})
            result = await Runner.run(jarvis, inputs)
            # TODO stream result.final_output
            print(result.final_output)
            print("---")
            inputs = result.to_input_list()


if __name__ == "__main__":
    # Run the tests
    asyncio.run(text_conversation_loop())