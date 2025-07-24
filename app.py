import json
import ast
import os
from openai import AsyncOpenAI

import chainlit as cl
import openai
import tools as tool_belt
import prompts as prompts

cl.instrument_openai()

api_key = os.environ.get("OPENAI_API_KEY")
client = AsyncOpenAI(api_key=api_key)

MAX_ITER = 5

tools = tool_belt.tools
tool_defs = [item[0] for item in tools]

@cl.on_chat_start
def start_chat():
    
    cl.user_session.set(
        "message_history",
        [{"role": "system", "content": prompts.main}],
    )


@cl.step(type="tool")
async def call_tool(tool_call_id, name, arguments, message_history):
    
    # Check the name of the tool and log it to console
    print(f"Calling tool: {name}")
    if arguments:
        print(f"Arguments: {arguments}")
    
    # arguments = ast.literal_eval(arguments)

    current_step = cl.context.current_step
    current_step.name = name
    current_step.input = arguments
    function_response = None

    # This way tools are being stored tools = [(generate_sql_query_def, generate_sql_query_handler)]
    for tool in tools:
        print(f"Looking for tool: {name}. Current tool: {tool[0]['function']['name']}")
        if tool[0]["function"]["name"] == name:
            arguments = ast.literal_eval(arguments)
            function_response = await tool[1](**arguments)
            function_response = json.dumps(function_response)
            break
            

    if function_response is None and name != "draw_plotly_chart":
        raise ValueError(f"No handler found for tool: {name}")

    current_step.output = function_response
    current_step.language = "json"

    message_history.append(
        {
            "role": "assistant",
            "tool_calls":[
                {
                    "id": tool_call_id,
                    "type": "function",
                    "function": {
                        "arguments": json.dumps(arguments),
                        "name": name
                    }
                }
            ] 
        }
    )

    message_history.append(
        {
            "role": "tool",
            "content": function_response,
            "tool_call_id": tool_call_id
        }
    )

async def call_gpt4(message_history):
    settings = {
        "model": "gpt-4o",
        "tools": tool_defs,
        "tool_choice": "auto",
        "temperature": 0,
    }

    try:
        stream = await client.chat.completions.create(
            messages=message_history, stream=True, **settings
        )

        tool_call_id = None
        function_output = {"name": "", "arguments": ""}

        final_answer = cl.Message(content="", author="Assistant")

        async for part in stream:
            new_delta = part.choices[0].delta
            tool_call = new_delta.tool_calls and new_delta.tool_calls[0]
            function = tool_call and tool_call.function
            if tool_call and tool_call.id:
                tool_call_id = tool_call.id

            if function:
                if function.name:
                    function_output["name"] = function.name
                else:
                    function_output["arguments"] += function.arguments
            if new_delta.content:
                if not final_answer.content:
                    await final_answer.send()
                await final_answer.stream_token(new_delta.content)

        if tool_call_id:

            # print(f"Calling tool: {function_output['name']}")
            # print (f"Arguments: {function_output['arguments']}")

            await call_tool(
                tool_call_id,
                function_output["name"],
                function_output["arguments"],
                message_history,
            )

        if final_answer.content:
            await final_answer.update()

        return tool_call_id
    
    except openai.RateLimitError as e:
    # Manejo del error de límite de tokens
        error_message = ("Lo sentimos, la solicitud excedió el límite de tokens permitido. Por favor, intenta reducir el tamaño de la entrada o los resultados.")
        print(f"Error capturado: {e}")  # Para registro en consola
        await cl.Message(content=error_message, author="Assistant").send()

         # Limpiar el historial de mensajes para evitar loops
        cl.user_session.set("message_history", [])
        return None

@cl.on_message
async def on_message(message: cl.Message):
    message_history = cl.user_session.get("message_history")
    message_history.append({"role": "user", "content": message.content, "author": "user"})

    cur_iter = 0

    while cur_iter < MAX_ITER:
        tool_call_id = await call_gpt4(message_history)
        if not tool_call_id:
            break

        cur_iter += 1

if __name__ == "__main__":
    from chainlit.cli import run_chainlit
    run_chainlit(__file__)