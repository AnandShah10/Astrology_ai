# agent/consumers.py
import json, os, base64, asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from faster_whisper import WhisperModel
# from gtts import gTTS
from io import BytesIO
from pydub import AudioSegment
# from google.generativeai import GenerativeModel, configure
from dotenv import load_dotenv
from datetime import date

load_dotenv()

# Load Whisper once
model = WhisperModel("small")  # tiny/small/medium/large
# AI_API_KEY = os.getenv("AI_API_KEY")
# configure(api_key=AI_API_KEY)
# MODEL = GenerativeModel("gemini-2.5-flash")
from openai import AzureOpenAI
endpoint = os.getenv("ENDPOINT_URL", "https://jivihireopenai.openai.azure.com/")
client = AzureOpenAI(
        azure_endpoint=endpoint,
        api_key=os.environ['OPENAI_API_KEY'],
        api_version="2024-05-01-preview",
    )
SYSTEM_PROMPT_TEMPLATE = (
    "You are Astro AI, a specialized assistant dedicated exclusively to astrology. "
    "Your role is to provide accurate, insightful, and engaging answers about horoscopes, "
    "zodiac signs, natal charts, planetary transits, astrological houses, aspects, "
    "synastry, and other astrology-related topics. Always respond in a mystical, cosmic tone. "
    "- Only answer questions directly related to astrology. "
    "- If a question is not related to astrology, respond with: "
    "\"I'm Astro AI, your cosmic guide! Please ask about horoscopes, zodiac signs, natal charts, "
    "or other astrology topics to explore the mysteries of the stars.\" "
    "- Keep responses concise, relevant, and aligned with astrological principles. "
    "User's birth details: Date: {birth_date}, Time: {birth_time}, "
    "Place: {birth_place}, Time Zone: {birth_tz}, System: {system}. "
    "Today's Date: {today}. "
    "Reply like a kind, insightful astrologer."
)


class VoiceConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        self.chat_history = []
        print("🔮 WebSocket connected")

    async def disconnect(self, close_code):
        print("❌ WebSocket disconnected")

    async def receive(self, text_data=None, bytes_data=None):
        if text_data:  # plain text message
            data = json.loads(text_data)
            user_text = data.get("message")
            if user_text:
                await self.handle_user_message(user_text)

        elif bytes_data:  # audio bytes
            asyncio.create_task(self.handle_audio_chunk(bytes_data))

    async def handle_audio_chunk(self, bytes_data):
        """Transcribe audio chunk & respond live"""
        audio_file = BytesIO(bytes_data)
        sound = AudioSegment.from_raw(audio_file, sample_width=2, frame_rate=48000, channels=1)
        output = BytesIO()
        sound.export(output, format="wav")
        output.seek(0)

        # Whisper partial transcription
        result, _ = model.transcribe(output, language="en")
        text = " ".join([seg.text for seg in result]).strip()
        if text:
            await self.send(json.dumps({"transcript": text}))
            await self.handle_user_message(text)

    async def handle_user_message(self, user_text):
        reply_stream = await self.get_ai_reply(user_text)

        sentence_buffer = ""
        async for piece in reply_stream:
            if not piece.strip():
                continue

            # Send partial reply text
            await self.send(json.dumps({"partial_reply": piece}))
            sentence_buffer += piece

            # If sentence ends, TTS immediately
            if sentence_buffer.endswith((".", "!", "?")):
                audio_base64 = await asyncio.to_thread(self.get_tts_audio, sentence_buffer)
                await self.send(json.dumps({"audio_chunk": audio_base64}))
                sentence_buffer = ""

        # Flush remainder
        if sentence_buffer:
            audio_base64 = await asyncio.to_thread(self.get_tts_audio, sentence_buffer)
            await self.send(json.dumps({"audio_chunk": audio_base64}))

    async def get_ai_reply(self, user_text):
        user = self.scope["user"]
        if not user.is_authenticated:
            await self.close()
            return []

        profile = await database_sync_to_async(lambda: getattr(user, "userprofile", None))()
        if not profile:
            await self.send(json.dumps({"error": "User profile not found"}))
            return []

        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
            birth_date=profile.birth_date,
            birth_time=profile.birth_time,
            birth_place=profile.birth_place,
            birth_tz=profile.birth_tz,
            system=profile.system,
            today=date.today(),
        )

        if not self.chat_history:
            self.chat_history = [{"role": "model", "parts": [{"text": system_prompt}]}]

        self.chat_history.append({"role": "user", "parts": [{"text": user_text}]})

        # chat = MODEL.start_chat(history=self.chat_history)
        # response = chat.send_message(user_text, stream=True)
        response = client.chat.completions.create(
            model="gpt-4o-mini", 
            messages=self.chat_history[-20:],  
            temperature=0.7
        )
        # reply = response.choices[0].message.content.strip()

        async def generator():
            reply_accum = ""
            for chunk in response:
                if chunk.text:
                    reply_accum += chunk.text
                    yield chunk.text
            self.chat_history.append({"role": "model", "parts": [{"text": reply_accum}]})
            self.chat_history = self.chat_history[-20:]

        return generator()

    def get_tts_audio(self, text):
        # tts = gTTS(text=text, lang="en")
        # tts_buffer = BytesIO()
        # tts.write_to_fp(tts_buffer)
        # tts_buffer.seek(0)
        # audio_base64 = base64.b64encode(tts_buffer.read()).decode("utf-8")
        # return audio_base64
        return None #change afterwards and uncomment the code