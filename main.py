
from openai import OpenAI
from fastapi import FastAPI, Form, Request, WebSocket
from typing import Annotated
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

openai = OpenAI(
    api_key = os.getenv('OPEN_AI_SECRET_KEY')
)
templates = Jinja2Templates(directory="templates")
chat_response = []

@app.get("/", response_class=HTMLResponse)
async def chat_page(request:Request):
    return templates.TemplateResponse("home.html", {"request" : request, "chat_response": chat_response})

chat_log = [{'role': 'system',
            'content': 'You are a skilled and supportive AI tutor for Computer Science and Information Technology students. Your primary role is to guide students in learning programming by helping them think critically and develop solutions on their own. Use scaffolding techniques — break problems into smaller steps, ask probing questions, ask students to tell you what they think before guiding them, and provide cues that lead the student toward understanding without giving them the final answer or code. Apply Bloom’s Taxonomy: Start with remembering and understanding (e.g., ask them to recall key concepts or definitions). Move to applying and analyzing (e.g., have them trace logic, identify errors, or explain reasoning). Support evaluating and creating (e.g., challenge them to optimize, reflect, or write their own approach). Do not provide complete code — even if the student asks. Instead, encourage them to proide you an attempt of the code, tehn give them hints, analogies, and feedback. Your tone should be warm, patient, and encouraging. Treat mistakes as learning opportunities and celebrate small wins to build confidence. Always help the student grow their problem-solving mindset, not just their syntax skills.'}]


@app.websocket("/ws")
async def chat(websocket: WebSocket):

    await websocket.accept()
    while True:
        user_input = await websocket.receive_text()
        chat_log.append({'role': 'user', 'content': user_input})
        chat_response.append(user_input)

        try:
            response = openai.chat.completions.create(
                model='gpt-4o',
                messages=chat_log,
                temperature=0.6,
                stream = True
            )

            ai_response = ''
            for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    ai_response += chunk.choices[0].delta.content
                    await websocket.send_text(chunk.choices[0].delta.content)
            chat_response.append(ai_response)

        except Exception as e:
            await websocket.send_text(f'Error: {str(e)}')
            break


@app.post("/", response_class=HTMLResponse)
async def chat(request: Request, user_input: Annotated[str, Form()]):

   chat_log.append({'role': 'user', 'content': user_input})
   chat_response.append(user_input)

   response = openai.chat.completions.create(
        model =  'gpt-4o',
        messages =chat_log,
        temperature = 0.6,
        )

   bot_response = response.choices[0].message.content
   chat_log.append({'role': 'assistant', 'content': bot_response})
   chat_response.append(bot_response)

   return templates.TemplateResponse("home.html", {"request" : request, "chat_response": chat_response})

@app.get("/image", response_class=HTMLResponse)
async def image_page(request: Request):
    return templates.TemplateResponse("image.html", {"request": request})

@app.post("/image", response_class=HTMLResponse)
async def create_image(request: Request, user_input: Annotated[str, Form()]):

    response = openai.images.generate(
        prompt = user_input,
        n=1,
        size="256x256"
    )

    image_url = response.data[0].url  # Extract image URL
    #print("Generated Image URL:", image_url)
    return templates.TemplateResponse("image.html", {"request": request, "image_url": image_url})
