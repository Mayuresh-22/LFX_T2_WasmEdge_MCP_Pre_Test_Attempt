import asyncio
import json
import pprint
import re
from typing import Optional
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from dotenv import load_dotenv
import os
import openai
load_dotenv(".env.local")


class MCPClient:
    def __init__(self, exit_stack: AsyncExitStack):
        # Initialize session and client objects
        self.session: ClientSession
        self.llm: openai.Client
        self.exit_stack = exit_stack
        self.message_array = [
            {
                "role": "system",
                "content": """You are an AI assistant dedicated to helping students prepare for Linux Foundation Certification exams.
Your objectives:
- Provide accurate, concise, and exam-relevant guidance.
- Use available tools only when necessary:
    - get_random_question: Fetch a random practice question (display only the question, keep the answer private).
    - get_question_answer: Retrieve the answer and a brief explanation for a user-asked question.
- Always call get_question_answer when a user asks a specific question.
- When asked for new practice questions, call get_random_question and do not include the answer in the response.
- Never generate or assume information not provided by the tools or user.
- Keep all responses strictly within the context of Linux Foundation Certification preparation.
- Maintain a natural, supportive, and focused conversation flow.
- Do not answer questions unrelated to Linux Foundation Certification exams.
- If unsure, ask for clarification or suggest using the tools.

Your goal is to maximize the user's exam readiness by leveraging the tools and your knowledge base appropriately."""}
        ]
    
    async def connect_to_server(self, server_script_path: str):
        """Connect to an MCP server

        Args:
            server_script_path: Path to the server script (.py)
        """
        is_python = server_script_path.endswith('.py')
        if not (is_python):
            raise ValueError("Server script must be a .py file")

        command = "python"
        server_params = StdioServerParameters(
            command=command,
            args=[server_script_path],
            cwd=".",
        )

        # Connect to the mcp server using stdio transport protocol
        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))
        await self.session.initialize()

        # Get list of available tools and process them in required json format
        self.mcp_tools = await self.session.list_tools()
        self.tool_dicts = []
        for tool in self.mcp_tools.tools:
            tool_dict = {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description if hasattr(tool, "description") else "",
                    "parameters": {
                        "type": "object",
                        "properties": tool.inputSchema["properties"] if hasattr(tool, "inputSchema") else {},
                    },
                },
            }
            self.tool_dicts.append(tool_dict)
        
        # Initialize the LLM client (eg. any openai compatible LLM provider)
        self.llm = openai.Client(
            api_key=os.getenv("GROQ_API_KEY"),
            base_url="https://api.groq.com/openai/v1",
        )

    async def eval_tools(self, tool_calls):
        """Evaluate the tool calls and return the results
        Args:
            tool_calls: List of tool calls to evaluate
        """
        result = []
        for call in tool_calls:
            fun = call.function
            print("Tool call:", {"name": fun.name, "arguments": fun.arguments})
            tool_call_result = await self.session.call_tool(
                fun.name,
                json.loads(fun.arguments),
            )
            if tool_call_result is not None:
                _result = json.loads(tool_call_result.model_dump_json())
                _result["tool_call_id"] = call.id
                result.append(_result)
                print("Tool call result:", _result)
        return result

    async def llm_resp_stream_handler(self, stream):
        """Handle the streamed response from the LLM and process tool calls if any
        Args:
            stream: The streamed response from the LLM provider
        """
        tool_calls = []
        content = ""
        print("Assistant:")
        for chunk in stream:
            if len(chunk.choices) == 0:
                break
            delta = chunk.choices[0].delta
            print(re.sub(r'\n+', '\n',(str(delta.content))) if delta.content is not None else "", end="")
            content += re.sub(r'\n+', '\n',(str(delta.content))) if delta.content is not None else ""

            if delta.tool_calls is None or (delta.tool_calls) == 0:
                pass
            else:
                if len(tool_calls) == 0:
                    tool_calls = delta.tool_calls
                else:
                    for i, tool_call in enumerate(delta.tool_calls):
                        if tool_calls[i] == None:
                            tool_calls[i] = tool_call
                        else:
                            argument_delta = tool_call["function"]["arguments"]
                            tool_calls[i]["function"]["arguments"].extend(argument_delta)
        if len(tool_calls) == 0:
            self.message_array.append({"role": "assistant", "content": content})
        else:
            tools_calls_json = [calls for calls in tool_calls]
            self.message_array.append(
                {"role": "assistant", "content": content, "tool_calls": tools_calls_json}
            )
        return await self.eval_tools(tool_calls)

    async def process_query(self, query: str) -> str:
        """Process a query using Claude and available tools
        Args:
            query: The query to process
        """
        self.message_array.append({"role": "user", "content": query})

        llm_stream = self.llm.chat.completions.create(
            model=os.getenv("MODEL_NAME"),
            messages=self.message_array,
            tools=self.tool_dicts,
            stream=True,
        )

        tool_result = await self.llm_resp_stream_handler(llm_stream)
        if tool_result:
            for result in tool_result:
                self.message_array.append({"tool_call_id": result["tool_call_id"], "role": "tool", "content": result["content"][0]["text"]})
                llm_stream = self.llm.chat.completions.create(
                    model=os.getenv("MODEL_NAME"),
                    messages=self.message_array,
                    tools=self.tool_dicts,
                    stream=True,
                )
                tool_result = await self.llm_resp_stream_handler(llm_stream)
            return False
        else:
            return True


async def main():
    print("-------------------------------------------------------------")
    print("                     LF Certification Assistant")
    print("An AI agent that helps you with LF Certification Preparation")
    print("          Type 'exit' or 'quit' to stop the assistant")
    print("-------------------------------------------------------------")
    print("Connecting to server...")
    async with AsyncExitStack() as stack:
        client = MCPClient(stack)
        await client.connect_to_server("./server/server.py")
        print("Connected to server")
        # Start a chat loop
        while True:
            query = input("\nYou: ")
            if query.lower() in ["exit", "quit"]:
                break
            if not query:
                continue
            result = await client.process_query(query)
            if result:
                print("\n(Done processing)")
            else:
                print("\n(Processing tool calls completed)") 


if __name__ == "__main__":
    asyncio.run(main())
