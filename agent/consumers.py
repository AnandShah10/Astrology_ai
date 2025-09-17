# agent/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from faster_whisper import WhisperModel
from gtts import gTTS
import base64,os
from io import BytesIO
from pydub import AudioSegment
from google.generativeai import GenerativeModel, configure
from dotenv import load_dotenv
from datetime import date
load_dotenv()
# Load Whisper once for efficiency
model = WhisperModel("small")  # choose size: tiny, small, medium, large
AI_API_KEY = os.getenv('AI_API_KEY')
configure(api_key=AI_API_KEY)
MODEL = GenerativeModel("gemini-2.5-flash")
SYSTEM_PROMPT_TEMPLATE = (
    "You are Astro AI, a specialized assistant dedicated exclusively to astrology. "
    "Your role is to provide accurate, insightful, and engaging answers about horoscopes, "
    "zodiac signs, natal charts, planetary transits, astrological houses, aspects, "
    "synastry, and other astrology-related topics. Always respond in a mystical, cosmic tone. "
    "- Only answer questions directly related to astrology. Examples: zodiac sign characteristics, "
    "horoscope predictions, birth chart interpretations, planetary influences, or astrological compatibility. "
    "- If a question is not related to astrology (e.g., programming, weather), respond with: "
    '"I\'m Astro AI, your cosmic guide! Please ask about horoscopes, zodiac signs, natal charts, '
    'or other astrology topics to explore the mysteries of the stars." '
    "- If ambiguous, ask for clarification to stay within astrology. "
    "- Keep responses concise, relevant, and aligned with astrological principles. "
    "User's birth details: Date: {birth_date}, Time: {birth_time}, "
    "Place: {birth_place}, Time Zone: {birth_tz}, System: {system}. "
    "Today's Date: {today}. "
    "Reply like a kind, insightful astrologer."
)

class VoiceConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        self.audio_chunks = []
        self.chunk_count = 0
        print("WebSocket connected")

    async def disconnect(self, close_code):
        print("WebSocket disconnected")

    async def receive(self, text_data=None, bytes_data=None):
        """
        Receive either text or audio bytes.
        - For text: directly send to AI and return reply.
        - For audio: buffer chunks, transcribe periodically, and send AI reply.
        """
        # -----------------------
        # Handle text input
        # -----------------------
        if text_data:
            data = json.loads(text_data)
            user_text = data.get("message")
            if user_text:
                # Send AI response
                reply_text = await self.get_ai_reply(user_text)
                audio_base64 = self.get_tts_audio(reply_text)
                await self.send(json.dumps({
                    "reply": reply_text,
                    "audio": audio_base64
                }))

        # -----------------------
        # Handle audio chunks
        # -----------------------
        elif bytes_data:
            self.audio_chunks.append(bytes_data)
            self.chunk_count += 1

            # Transcribe every 10 chunks (adjust for latency vs accuracy)
            if self.chunk_count >= 10:
                await self.process_audio_chunks()
                self.chunk_count = 0

    async def process_audio_chunks(self):
        if not self.audio_chunks:
            return

        audio_data = b"".join(self.audio_chunks)
        audio_file = BytesIO(audio_data)
        # Convert raw chunks to WAV using pydub
        sound = AudioSegment.from_raw(audio_file, sample_width=2, frame_rate=48000, channels=1)
        output = BytesIO()
        sound.export(output, format="wav")
        output.seek(0)

        # Whisper transcription
        result, _ = model.transcribe(output, language="en")
        final_text = " ".join([segment.text for segment in result]).strip()
        if not final_text:
            final_text = "..."

        # Send partial transcript
        await self.send(json.dumps({"transcript": final_text}))

        # Send AI reply
        ai_reply = await self.get_ai_reply(final_text)
        audio_base64 = self.get_tts_audio(ai_reply)
        await self.send(json.dumps({
            "reply": ai_reply,
            "audio": audio_base64
        }))

        # Reset buffer
        self.audio_chunks = []

    async def get_ai_reply(self, user_text):
        """
        Replace this with your actual AI model call.
        For example: MODEL.generate_content(...)
        """
        user = self.scope["user"]
        if not user.is_authenticated:
            # handle unauthenticated case, e.g., disconnect
            await self.close()
            return

        profile = getattr(user, "userprofile", None)
        if not profile:
            # handle missing profile
            await self.send(json.dumps({"error": "User profile not found"}))
            return
        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
            birth_date=profile.birth_date,
            birth_time=profile.birth_time,
            birth_place=profile.birth_place,
            birth_tz=profile.birth_tz,
            system=profile.system,
            today=date.today()
        )
        # Example placeholder logic:
        chat_history = self.session.get("chat_history", [])
        if not chat_history:
            chat_history = [{"role": "model", "parts": [{"text": system_prompt}]}]

        # Add user message
        chat_history.append({"role": "user", "parts": [{"text": user_text}]})

        # Generate AI response
        response = MODEL.generate_content(contents=chat_history[-20:])  # Limit history to last 20 messages
        reply = response.text

        # Add assistant's response
        chat_history.append({"role": "model", "parts": [{"text": reply}]})

        # Store only the last 20 messages in session
        self.session["chat_history"] = chat_history[-20:]
        self.session.modified = True  # Ensure session is saved
        return reply

    def get_tts_audio(self, text):
        """
        Convert text to speech (gTTS) and return base64.
        """
        tts = gTTS(text=text, lang="en")
        tts_buffer = BytesIO()
        tts.write_to_fp(tts_buffer)
        tts_buffer.seek(0)
        audio_base64 = base64.b64encode(tts_buffer.read()).decode("utf-8")
        return audio_base64
