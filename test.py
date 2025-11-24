# ================================================
# SarvamAI WebSocket TTS Example
# ================================================

# import asyncio
# import base64
# import io
# import wave
# from sarvamai import AsyncSarvamAI, AudioOutput
# import pyaudio
# import os
# from dotenv import load_dotenv

# load_dotenv()

# async def play_streaming_tts(text: str):
#     client = AsyncSarvamAI(api_subscription_key=os.getenv("SARVAMAI_API_KEY"))
#     print("✅ Initialized SarvamAI client")

#     # audio playback setup
#     p = pyaudio.PyAudio()
#     stream = p.open(format=pyaudio.paInt16, channels=1, rate=24000, output=True)
#     print("🔊 Audio stream opened")

#     async with client.text_to_speech_streaming.connect(
#         model="bulbul:v2",
#         send_completion_event=True
#     ) as ws:
#         # Configure the stream
#         await ws.configure(
#             target_language_code="en-IN",
#             speaker="anushka",
#             output_audio_codec="wav",  # wav is easy to decode for playback
#             enable_preprocessing=True  # enable text preprocessing 
#         )

#         # Send text
#         await ws.convert(text)
#         # Flush to start generating
#         await ws.flush()

#         async for msg in ws:
#             if isinstance(msg, AudioOutput):
#                 # decode base64 audio chunk
#                 audio_bytes = base64.b64decode(msg.data.audio)
#                 with wave.open(io.BytesIO(audio_bytes)) as wf:
#                     data = wf.readframes(wf.getnframes())
#                     stream.write(data)
#             else:
#                 print("Received:", msg)

#     # cleanup
#     stream.stop_stream()
#     stream.close()
#     p.terminate()
#     print("✅ Playback complete")

# if __name__ == "__main__":
#     long_text ="With a single WebSocket connection, you can stream text input and receive synthesized audio continuously, without the overhead of repeated HTTP requests. This makes it ideal for use cases where your application sends or receives text in chunks and needs real-time audio to deliver a smooth, conversational experience"
#     asyncio.run(play_streaming_tts(long_text))

# ------------------- END -------------------

# =================================================
# MURF AI WebSocket TTS Example
# =================================================


# print(response.audio_file)
# import asyncio
# import websockets
# import json
# import base64
# import pyaudio
# import wave
# import io
# import os
# from dotenv import load_dotenv
# load_dotenv()
# # import os


# API_KEY = os.getenv("MURFAI_API_KEY") # Or use os.getenv("MURF_API_KEY") if you have set the API key as an environment variable
# WS_URL = "wss://api.murf.ai/v1/speech/stream-input"
# PARAGRAPH = "With a single WebSocket connection, आप कैसे है में ठीक हू आप बताए ,you can stream text input and receive synthesized audio continuously, without the overhead of repeated HTTP requests. This makes it ideal for use cases where your application sends or receives text in chunks and needs real-time audio to deliver a smooth, conversational experience"

# # Audio format settings (must match your API output)
# SAMPLE_RATE = 44100
# CHANNELS = 1
# FORMAT = pyaudio.paInt16

# async def tts_stream():
#   async with websockets.connect(
#       f"{WS_URL}?api-key={API_KEY}&sample_rate=44100&channel_type=MONO&format=WAV"
#   ) as ws:
#       # Send voice config first (optional)
#       voice_config_msg = {
#           "voice_config": {
#               "voiceId": "en-US-amara",
#               "style": "Conversational",
#               "rate": 0,
#               "pitch": 0,
#               "variation": 1,
#               "multiNativeLocale": "en-IN"
#           }
#       }
#       print(f'Sending payload : {voice_config_msg}')
#       await ws.send(json.dumps(voice_config_msg))

#       # Send text in one go (or chunk if you want streaming)
#       text_msg = {
#           "text": PARAGRAPH,
#           "end" : True # This will close the context. So you can re-run and concurrency is available.
#       }
#       print(f'Sending payload : {text_msg}')
#       await ws.send(json.dumps(text_msg))

#       # Setup audio stream
#       pa = pyaudio.PyAudio()
#       stream = pa.open(format=FORMAT, channels=CHANNELS, rate=SAMPLE_RATE, output=True)

#       first_chunk = True
#       try:
#           while True:
#               response = await ws.recv()
#               data = json.loads(response)
#               print(f'Received data:  {data}')
#               if "audio" in data:
#                   audio_bytes = base64.b64decode(data["audio"])
#                   # Skip the first 44 bytes (WAV header) only for the first chunk
#                   if first_chunk and len(audio_bytes) > 44:
#                       audio_bytes = audio_bytes[44:]
#                       first_chunk = False
#                   stream.write(audio_bytes)
#               if data.get("final"):
#                   break
#       finally:
#           stream.stop_stream()
#           stream.close()
#           pa.terminate()

# if __name__ == "__main__":
#     asyncio.run(tts_stream())


# -------------------- END -------------------
# =================================================
# openai transcription example for 4 second chunks
# =================================================
# import pyaudio
# import wave
# import time
# from openai import OpenAI
# import io
# import threading
# import os
# from dotenv import load_dotenv
# load_dotenv()
# class SimpleRealTimeSTT:
#     def __init__(self, api_key):
#         self.client = OpenAI(api_key=api_key)
#         self.is_listening = False
        
#         # Audio configuration that works well with Whisper
#         self.FORMAT = pyaudio.paInt16
#         self.CHANNELS = 1
#         self.RATE = 16000  # Whisper works best with 16kHz
#         self.CHUNK = 1024
#         self.RECORD_SECONDS = 4  # Process every 4 seconds
        
#         self.audio = pyaudio.PyAudio()
    
#     def bytes_to_wav(self, audio_bytes):
#         """Convert raw bytes to WAV format in memory"""
#         wav_buffer = io.BytesIO()
        
#         with wave.open(wav_buffer, 'wb') as wav_file:
#             wav_file.setnchannels(self.CHANNELS)
#             wav_file.setsampwidth(2)  # 16-bit audio
#             wav_file.setframerate(self.RATE)
#             wav_file.writeframes(audio_bytes)
        
#         wav_buffer.seek(0)
#         return wav_buffer
    
#     def record_and_transcribe_chunk(self):
#         """Record a chunk of audio and transcribe it"""
#         frames = []
#         chunks_per_second = self.RATE // self.CHUNK
#         total_chunks = chunks_per_second * self.RECORD_SECONDS
        
#         stream = self.audio.open(
#             format=self.FORMAT,
#             channels=self.CHANNELS,
#             rate=self.RATE,
#             input=True,
#             frames_per_buffer=self.CHUNK
#         )
        
#         print(f"🔊 Recording {self.RECORD_SECONDS} seconds...")
        
#         for i in range(total_chunks):
#             if not self.is_listening:
#                 break
#             data = stream.read(self.CHUNK, exception_on_overflow=False)
#             frames.append(data)
        
#         stream.stop_stream()
#         stream.close()
        
#         if frames and self.is_listening:
#             audio_data = b''.join(frames)
#             self.transcribe_audio(audio_data)
    
#     def transcribe_audio(self, audio_data):
#         """Transcribe audio data"""
#         try:
#             wav_buffer = self.bytes_to_wav(audio_data)
            
#             transcription = self.client.audio.transcriptions.create(
#                 model="whisper-1",
#                 file=("audio.wav", wav_buffer.read(), "audio/wav"),
#                 response_format="text"
#             )
            
#             if transcription.strip():
#                 print(f"📝 {transcription}")
#             else:
#                 print("🔇 No speech detected")
                
#         except Exception as e:
#             print(f"❌ Transcription failed: {e}")
    
#     def start(self):
#         """Start continuous listening"""
#         self.is_listening = True
#         print("🎤 Starting continuous speech recognition...")
#         print("Press Ctrl+C to stop\n")
        
#         try:
#             while self.is_listening:
#                 self.record_and_transcribe_chunk()
#         except KeyboardInterrupt:
#             print("\n🛑 Stopping...")
#         finally:
#             self.is_listening = False
#             self.audio.terminate()

# # Usage
# if __name__ == "__main__":
#     api_key = os.getenv("OPENAI_API_KEY")  # Replace with your actual API key
#     stt = SimpleRealTimeSTT(api_key)
#     stt.start()

# --------------------- END ----------------------
# ================================================
# openai live transcription example using silero VAD
# ================================================
# import pyaudio
# import wave
# import torch
# import numpy as np
# import time
# import io
# from openai import OpenAI
# import os
# from dotenv import load_dotenv
# load_dotenv()

# # Initialize OpenAI client
# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# # Load Silero VAD
# model, utils = torch.hub.load(
#     repo_or_dir='snakers4/silero-vad',
#     model='silero_vad',
#     trust_repo=True
# )
# (get_speech_timestamps, _, read_audio, *_) = utils

# # Audio setup
# RATE = 16000
# CHUNK = 512   # Silero requires 512 samples for 16kHz
# FORMAT = pyaudio.paInt16
# CHANNELS = 1

# p = pyaudio.PyAudio()
# stream = p.open(format=FORMAT,
#                 channels=CHANNELS,
#                 rate=RATE,
#                 input=True,
#                 frames_per_buffer=CHUNK)

# print("🎤 Listening... (start speaking)")

# frames = []
# is_speaking = False
# silence_start = None
# SILENCE_LIMIT = 0.8  # seconds of silence to detect end of speech


# def transcribe_audio(audio_bytes):
#     """Convert raw PCM bytes -> WAV -> transcribe"""
#     print("🧠 Transcribing...")

#     # Convert raw PCM bytes to numpy array and ensure proper format
#     audio_data = np.frombuffer(audio_bytes, dtype=np.int16)
    
#     # Create a proper WAV file in memory
#     wav_io = io.BytesIO()
#     with wave.open(wav_io, 'wb') as wav_file:
#         wav_file.setnchannels(CHANNELS)
#         wav_file.setsampwidth(2)  # 2 bytes for paInt16
#         wav_file.setframerate(RATE)
#         wav_file.writeframes(audio_data.tobytes())
    
#     wav_io.seek(0)
    
#     # Send to OpenAI with proper parameters
#     try:
#         transcript = client.audio.transcriptions.create(
#             model="gpt-4o-transcribe",  # Use the appropriate transcription model
#             file=("audio.wav", wav_io.read(), "audio/wav"),
#             language="en"  # Optional: specify language
#         )
#         print("🗣️ You said:", transcript.text)
#     except Exception as e:
#         print(f"❌ Transcription error: {e}")
    
#     print("🎤 Listening again...\n")


# def is_speech_chunk(audio_chunk):
#     """Check if current chunk has speech"""
#     audio_tensor = torch.from_numpy(
#         np.frombuffer(audio_chunk, np.int16).astype(np.float32) / 32768.0
#     ).unsqueeze(0)
#     speech_prob = model(audio_tensor, RATE).item()
#     return speech_prob > 0.5


# try:
#     while True:
#         data = stream.read(CHUNK, exception_on_overflow=False)
#         if is_speech_chunk(data):
#             if not is_speaking:
#                 print("🎙️ Speech detected...")
#                 frames = []
#             is_speaking = True
#             frames.append(data)
#             silence_start = None
#         elif is_speaking:
#             if silence_start is None:
#                 silence_start = time.time()
#             elif time.time() - silence_start > SILENCE_LIMIT:
#                 print("🛑 Speech ended, sending to transcribe...")
#                 audio_bytes = b"".join(frames)
#                 transcribe_audio(audio_bytes)
#                 is_speaking = False
#                 frames = []
#                 silence_start = None

# except KeyboardInterrupt:
#     print("👋 Exiting...")
# finally:
#     stream.stop_stream()
#     stream.close()
#     p.terminate()

# ---------------------- END ----------------------
# ================================================
# openai live transcription example using realtime api
# ================================================
# import asyncio
# import websockets
# import json
# import pyaudio
# import base64
# import os
# from dotenv import load_dotenv
# load_dotenv()
# # Configuration
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # Set your API key
# REALTIME_API_URL = "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01"

# # Audio configuration
# CHUNK = 1024
# FORMAT = pyaudio.paInt16
# CHANNELS = 1
# RATE = 24000  # 24kHz required by Realtime API

# class RealtimeTranscriber:
#     def __init__(self):
#         self.audio = pyaudio.PyAudio()
#         self.stream = None
#         self.ws = None
        
#     async def connect(self):
#         """Connect to OpenAI Realtime API"""
#         headers = {
#             "Authorization": f"Bearer {OPENAI_API_KEY}",
#             "OpenAI-Beta": "realtime=v1"
#         }
        
#         self.ws = await websockets.connect(REALTIME_API_URL, additional_headers=headers)
#         print("Connected to OpenAI Realtime API")
        
#         # Configure session for transcription
#         session_update = {
#             "type": "session.update",
#             "session": {
#                 "modalities": ["text", "audio"],
#                 "instructions": "You are a helpful assistant that transcribes speech.",
#                 "voice": "alloy",
#                 "input_audio_format": "pcm16",
#                 "output_audio_format": "pcm16",
#                 "input_audio_transcription": {
#                     "model": "whisper-1"
#                 },
#                 "turn_detection": {
#                     "type": "server_vad",
#                     "threshold": 0.5,
#                     "prefix_padding_ms": 300,
#                     "silence_duration_ms": 500
#                 }
#             }
#         }
#         await self.ws.send(json.dumps(session_update))
        
#     def start_audio_stream(self):
#         """Start capturing audio from microphone"""
#         self.stream = self.audio.open(
#             format=FORMAT,
#             channels=CHANNELS,
#             rate=RATE,
#             input=True,
#             frames_per_buffer=CHUNK
#         )
#         print("Microphone started. Speak now...")
        
#     async def send_audio(self):
#         """Capture and send audio to the API"""
#         try:
#             while True:
#                 audio_data = self.stream.read(CHUNK, exception_on_overflow=False)
#                 audio_b64 = base64.b64encode(audio_data).decode('utf-8')
                
#                 message = {
#                     "type": "input_audio_buffer.append",
#                     "audio": audio_b64
#                 }
#                 await self.ws.send(json.dumps(message))
#                 await asyncio.sleep(0.01)  # Small delay to prevent overwhelming
                
#         except Exception as e:
#             print(f"Error sending audio: {e}")
            
#     async def receive_transcription(self):
#         """Receive and display transcriptions"""
#         try:
#             async for message in self.ws:
#                 data = json.loads(message)
#                 event_type = data.get("type")
                
#                 # Handle different event types
#                 if event_type == "conversation.item.input_audio_transcription.completed":
#                     transcript = data.get("transcript", "")
#                     print(f"\n[USER]: {transcript}")
                    
#                 elif event_type == "response.audio_transcript.delta":
#                     delta = data.get("delta", "")
#                     print(delta, end="", flush=True)
                    
#                 elif event_type == "response.audio_transcript.done":
#                     transcript = data.get("transcript", "")
#                     print(f"\n[ASSISTANT]: {transcript}")
                    
#                 elif event_type == "error":
#                     error = data.get("error", {})
#                     print(f"\nError: {error.get('message')}")
                    
#         except Exception as e:
#             print(f"Error receiving transcription: {e}")
            
#     async def run(self):
#         """Main execution loop"""
#         try:
#             await self.connect()
#             self.start_audio_stream()
            
#             # Run send and receive concurrently
#             await asyncio.gather(
#                 self.send_audio(),
#                 self.receive_transcription()
#             )
            
#         except KeyboardInterrupt:
#             print("\nStopping transcription...")
#         finally:
#             self.cleanup()
            
#     def cleanup(self):
#         """Clean up resources"""
#         if self.stream:
#             self.stream.stop_stream()
#             self.stream.close()
#         self.audio.terminate()
#         print("Cleanup complete")

# async def main():
#     if not OPENAI_API_KEY:
#         print("Error: OPENAI_API_KEY environment variable not set")
#         print("Set it with: export OPENAI_API_KEY='your-api-key'")
#         return
        
#     transcriber = RealtimeTranscriber()
#     await transcriber.run()

# if __name__ == "__main__":
#     # Install required packages:
#     # pip install websockets pyaudio
    
#     asyncio.run(main())

# ----------------------- END ----------------------
# ================================================
# pipecat voice assistant example using openai whisper, gpt-4o-realtime and openai tts
# ================================================
# import asyncio
# import os
# from dotenv import load_dotenv

# from pipecat.pipeline.pipeline import Pipeline
# from pipecat.pipeline.runner import PipelineRunner
# from pipecat.pipeline.task import PipelineTask

# # The real service you want to use (speech-to-speech)
# from pipecat.services.openai_realtime import OpenAIRealtimeLLMService

# load_dotenv()

# async def main():
#     api_key = os.getenv("OPENAI_API_KEY")
#     if not api_key:
#         print("Error: OPENAI_API_KEY not set")
#         return

#     # Create the OpenAI Realtime service
#     llm = OpenAIRealtimeLLMService(api_key=api_key)

#     # Build a pipeline that uses that service directly
#     pipeline = Pipeline([
#         llm,  # the service handles both input and output internally
#     ])

#     task = PipelineTask(pipeline)
#     runner = PipelineRunner()

#     await runner.run(task)

# if __name__ == "__main__":
#     asyncio.run(main())
# -------------------------------- END ----------------------
# ================================================
# openai llm chat example with streaming
# ================================================
# from openai import OpenAI
# import os
# # Load your API key
# from dotenv import load_dotenv
# load_dotenv()
# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
# MODEL = "gpt-4o-mini"  # your fine-tuned model ID
# print("🗨️  Fine-tuned Chat (type 'exit' to quit)\n")
# messages = [
#     {
#         "role": "system",
#         "content": (
#             "You are an angry and strict manager. You dislike sudden or casual Work From Home (WFH) requests. "
#             "Your tone should be blunt, slightly irritated, and firm but not rude. "
#             "Do not break character or mention that this is a roleplay or simulation. "
#             "You are talking to your team member who is asking for WFH at the last moment. "
#             "Keep responses realistic and short, as if in an actual chat between manager and employee."
#         )
#     },
#     {
#         "role": "user",
#         "content": "Hey, I wanted to ask if I could work from home tomorrow. I have a passport appointment in the morning."
#     }
# ]

# while True:
#     user_input = input("You: ")
#     if user_input.lower() in ["exit", "quit"]:
#         print("👋 Bye!")
#         break
    
#     messages.append({"role": "user", "content": user_input})
    
#     try:
#         print("AI: ", end="", flush=True)
        
#         # Enable streaming
#         stream = client.chat.completions.create(
#             model=MODEL,
#             messages=messages,
#             stream=True  # Enable streaming
#         )
        
#         reply = ""
#         # Print each token as it arrives
#         for chunk in stream:
#             if chunk.choices[0].delta.content is not None:
#                 token = chunk.choices[0].delta.content
#                 print(token, end="", flush=True)
#                 reply += token
        
#         print("\n")  # New line after complete response
        
#         messages.append({"role": "assistant", "content": reply})
        
#     except Exception as e:
#         print(f"\n❌ Error: {e}")

# ----------------------- END ----------------------



# import pyaudio
# import wave
# import torch
# import numpy as np
# import time
# import io
# from openai import OpenAI
# import os
# from dotenv import load_dotenv

# load_dotenv()

# # Initialize OpenAI client
# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# # Load Silero VAD
# model, utils = torch.hub.load(
#     repo_or_dir='snakers4/silero-vad',
#     model='silero_vad',
#     trust_repo=True
# )
# (get_speech_timestamps, _, read_audio, *_) = utils

# # Audio setup
# RATE = 16000
# CHUNK = 512
# FORMAT = pyaudio.paInt16
# CHANNELS = 1

# p = pyaudio.PyAudio()
# stream = p.open(format=FORMAT,
#                 channels=CHANNELS,
#                 rate=RATE,
#                 input=True,
#                 frames_per_buffer=CHUNK)

# # LLM setup
# MODEL = "gpt-4o-mini"

# # Enhanced conversation setup with realistic, extended roleplay
# messages = [
#     {
#         "role": "system",
#         "content": (
#             "You are MR. THOMPSON, a 45-year-old senior manager at 'TechInnovate Solutions'. "
#             "You've been managing the development team for 8 years and have a reputation for being tough but fair. "
#             "You're currently stressed about the upcoming product launch in 2 weeks.\n\n"
            
#             "CURRENT CONTEXT:\n"
#             "- It's Tuesday morning, 9:15 AM\n"
#             "- The team is behind schedule on the 'Project Phoenix' launch\n"
#             "- There's a critical client demo scheduled for Friday\n"
#             "- Two team members are already out sick\n"
#             "- You're reviewing quarterly performance reports\n\n"
            
#             "PERSONALITY & BEHAVIOR:\n"
#             "- Initially curt but warms up slightly as conversation progresses\n"
#             "- Constantly multitasking - typing while talking, checking watch\n"
#             "- Uses manager jargon: 'bandwidth', 'deliverables', 'KPIs', 'sprint planning'\n"
#             "- Remembers past incidents: 'Like last month when Sarah missed the deadline...'\n"
#             "- Gives unsolicited career advice and productivity tips\n"
#             "- Has specific pet peeves: last-minute requests, vague explanations, phone use in meetings\n\n"
            
#             "CONVERSATION PATTERNS:\n"
#             "GREETINGS:\n"
#             "- 'Morning. What do you need?' (if busy)\n"
#             "- 'Yes? Make it quick, I've got a 9:30 with marketing.'\n"
#             "- 'Thompson here. What's up?' (while typing)\n"
#             "- 'You caught me at a bad time, but go ahead.'\n\n"
            
#             "FOLLOW-UP QUESTIONS:\n"
#             "- 'And how does that impact your current deliverables?'\n"
#             "- 'What's your plan for catching up on missed work?'\n"
#             "- 'Have you discussed this with your team lead?'\n"
#             "- 'Is this something that could have been planned better?'\n\n"
            
#             "WORKING RELATIONSHIP BUILDING:\n"
#             "- Reference past projects: 'Remember the Atlas launch? We can't have repeats of that.'\n"
#             "- Mention team dynamics: 'The team is counting on everyone right now.'\n"
#             "- Share pressure: 'The board is breathing down my neck about this launch.'\n"
#             "- Show occasional appreciation: 'I noticed you stayed late yesterday on the backend fixes.'\n\n"
            
#             "CONVERSATION FLOW MANAGEMENT:\n"
#             "1. ACKNOWLEDGE greeting and assess urgency\n"
#             "2. PROBE for details and impact analysis\n"
#             "3. CHALLENGE assumptions and planning\n"
#             "4. NEGOTIATE terms if considering approval\n"
#             "5. SET expectations and follow-up requirements\n"
#             "6. CLOSE with clear next steps\n\n"
            
#             "EXTENDED DIALOGUE TECHNIQUES:\n"
#             "- Ask about workload: 'How's the API integration going?'\n"
#             "- Check team coordination: 'Have you synced with David on the frontend changes?'\n"
#             "- Mention deadlines: 'We can't push the client demo again.'\n"
#             "- Give context: 'The reason I'm hesitant is because...'\n"
#             "- Share business impact: 'If we miss this launch, the Q4 targets are at risk.'\n\n"
            
#             "ENDING CONDITIONS:\n"
#             "Use '[END_CONVERSATION]' only when:\n"
#             "- Clear resolution reached AND natural closing remarks exchanged\n"
#             "- Employee says definitive goodbye: 'Thanks, bye' / 'See you tomorrow' / 'Okay, will do'\n"
#             "- You've given final instructions and dismissed them\n"
#             "- Conversation naturally winds down with mutual understanding\n\n"
            
#             "RESPONSE LENGTH: 3-6 sentences typically. Mix short blunt responses with occasional longer explanations. "
#             "Make it feel like a real workplace conversation that could last 5-10 exchanges naturally."
#         )
#     }
# ]

# print("🗨️  REALISTIC MANAGER ROLEPLAY: MR. THOMPSON")
# print("🎤 Start speaking... (Ctrl+C to exit)\n")
# print("💡 Try: 'Hi', 'Morning', 'Got a minute?', or dive straight into a WFH request\n")

# # Speech detection variables
# frames = []
# is_speaking = False
# silence_start = None
# SILENCE_LIMIT = 1.5  # Increased for natural conversation pauses
# conversation_active = True
# conversation_turn = 0

# def transcribe_audio(audio_bytes):
#     """Convert raw PCM bytes -> WAV -> transcribe"""
#     print("🧠 Processing...", end="\r")
    
#     # Convert raw PCM bytes to numpy array
#     audio_data = np.frombuffer(audio_bytes, dtype=np.int16)
    
#     # REMOVED the short audio check - accept all audio lengths
#     # Even short greetings like "Hi" will be processed
    
#     # Create a proper WAV file in memory
#     wav_io = io.BytesIO()
#     with wave.open(wav_io, 'wb') as wav_file:
#         wav_file.setnchannels(CHANNELS)
#         wav_file.setsampwidth(2)
#         wav_file.setframerate(RATE)
#         wav_file.writeframes(audio_data.tobytes())
    
#     wav_io.seek(0)
    
#     # Send to OpenAI for transcription
#     try:
#         transcript = client.audio.transcriptions.create(
#             model="whisper-1",
#             file=("audio.wav", wav_io.read(), "audio/wav"),
#             language="en"
#         )
#         user_text = transcript.text.strip()
#         if user_text:
#             print(" " * 20, end="\r")  # Clear the processing line
#             print(f"👤 You: {user_text}")
#             return user_text
#         else:
#             print(" " * 20, end="\r")
#             print("No clear speech detected")
#             return None
#     except Exception as e:
#         print(" " * 20, end="\r")
#         print(f"❌ Transcription error: {e}")
#         return None

# def get_llm_response(user_input):
#     """Get streaming response from LLM"""
#     global conversation_active, conversation_turn
    
#     conversation_turn += 1
#     messages.append({"role": "user", "content": user_input})
    
#     try:
#         print("🤖 Mr. Thompson: ", end="", flush=True)
        
#         # Enable streaming with parameters for more natural responses
#         stream_response = client.chat.completions.create(
#             model=MODEL,
#             messages=messages,
#             stream=True,
#             temperature=0.85,  # Slightly higher for more varied responses
#             max_tokens=250,    # Increased for longer, more natural responses
#             presence_penalty=0.1  # Encourages slightly more varied responses
#         )
        
#         reply = ""
#         # Print each token as it arrives
#         for chunk in stream_response:
#             if chunk.choices[0].delta.content is not None:
#                 token = chunk.choices[0].delta.content
#                 print(token, end="", flush=True)
#                 reply += token
        
#         print("\n")  # New line after complete response
        
#         # Check if conversation should end
#         if "[END_CONVERSATION]" in reply:
#             # Remove the tag from the stored message
#             reply_clean = reply.replace("[END_CONVERSATION]", "").strip()
#             messages.append({"role": "assistant", "content": reply_clean})
#             conversation_active = False
#             print("🏢 Conversation concluded naturally.\n")
#         else:
#             messages.append({"role": "assistant", "content": reply})
        
#     except Exception as e:
#         print(f"\n❌ LLM Error: {e}")

# def is_speech_chunk(audio_chunk):
#     """Check if current chunk has speech"""
#     try:
#         audio_tensor = torch.from_numpy(
#             np.frombuffer(audio_chunk, np.int16).astype(np.float32) / 32768.0
#         ).unsqueeze(0)
#         speech_prob = model(audio_tensor, RATE).item()
#         return speech_prob > 0.5
#     except Exception:
#         return False

# try:
#     print("🎤 Ready for conversation...\n")
    
#     while conversation_active:
#         data = stream.read(CHUNK, exception_on_overflow=False)
        
#         if is_speech_chunk(data):
#             if not is_speaking:
#                 print("🎙️ I'm listening...", end="\r")
#                 frames = []
#             is_speaking = True
#             frames.append(data)
#             silence_start = None
            
#         elif is_speaking:
#             if silence_start is None:
#                 silence_start = time.time()
#             elif time.time() - silence_start > SILENCE_LIMIT:
#                 print(" " * 25, end="\r")  # Clear the listening line
                
#                 # Transcribe the audio (NO LENGTH CHECK - accept short audio)
#                 audio_bytes = b"".join(frames)
#                 user_text = transcribe_audio(audio_bytes)
                
#                 # Get LLM response if transcription succeeded
#                 if user_text and conversation_active:
#                     get_llm_response(user_text)
                
#                 if conversation_active:
#                     print("💭 Your turn...")
                
#                 # Reset for next speech
#                 is_speaking = False
#                 frames = []
#                 silence_start = None

# except KeyboardInterrupt:
#     print("\n👋 Ending conversation...")
# finally:
#     stream.stop_stream()
#     stream.close()
#     p.terminate()
#     print("Audio resources cleaned up.")


# ==============================================
# 🧩 NLP Pipeline: Grammar + Tone + Keywords
# ==============================================

from transformers import pipeline
import language_tool_python
from rake_nltk import Rake

# ---------------------------------------------------
# 1️⃣ Grammar Correction (LanguageTool)
# ---------------------------------------------------
def grammar_check(text):
    tool = language_tool_python.LanguageTool('en-US')
    matches = tool.check(text)
    corrected = language_tool_python.utils.correct(text, matches)
    return corrected, len(matches)

# ---------------------------------------------------
# 2️⃣ Tone / Emotion Classification (Hugging Face)
# ---------------------------------------------------
def tone_classification(text):
    # Expanded label list for tone/emotion/rudeness detection
    labels = [
        "angry", "rude", "polite", "friendly", "nervous",
        "confident", "sarcastic", "neutral", "happy", "sad",
        "professional", "disrespectful", "helpful"
    ]
    
    classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
    result = classifier(text, candidate_labels=labels)
    
    # Return top 3 likely tones
    top_labels = [
        {"label": result["labels"][i], "confidence": round(result["scores"][i], 3)}
        for i in range(min(3, len(result["labels"])))]
    
    return top_labels

# ---------------------------------------------------
# 3️⃣ Keyword Extraction (RAKE)
# ---------------------------------------------------
def extract_keywords(text):
    rake = Rake()
    rake.extract_keywords_from_text(text)
    keywords = rake.get_ranked_phrases()[:5]  # top 5
    return keywords

# ---------------------------------------------------
# 🚀 Combine All Three
# ---------------------------------------------------
def analyze_text(text):
    print("🧾 Original Text:")
    print(text)
    print("-" * 60)

    # Grammar
    corrected_text, errors = grammar_check(text)
    print(f"✅ Grammar Correction: ({errors} issues fixed)")
    print(corrected_text)
    print("-" * 60)

    # Tone / Emotion
    tones = tone_classification(corrected_text)
    print("💬 Detected Tone / Emotion:")
    for tone in tones:
        print(f"{tone['label']} ({tone['confidence']})")
    print("-" * 60)

    # Keywords
    keywords = extract_keywords(corrected_text)
    print("🔑 Key Phrases:")
    print(", ".join(keywords))
    print("=" * 60)



# ---------------------------------------------------
# 🧪 Example Run
# ---------------------------------------------------
if __name__ == "__main__":
    text_input = "I is wnat to kno how to use thiss pipline! It's sooo coool!!!"
    analyze_text(text_input)


# Stop and remove the current container
# docker-compose down

# # Rebuild with the new code
# docker-compose build --no-cache

# # Start fresh
# docker-compose up