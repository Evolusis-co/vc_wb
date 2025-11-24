from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
# from fastapi.security import HTTPBearer, HTTPAuthCredentialsBearer
import numpy as np
import io
import os
import json
import asyncio
import base64
from openai import OpenAI
from dotenv import load_dotenv
from contextlib import asynccontextmanager
import wave
import httpx
import re
import torch
import torchaudio
from torch_audiomentations import Compose, AddColoredNoise, PitchShift, Gain
import aio_pika
import uuid
from sqlalchemy.orm import Session
from core import database, models, schemas
from core.database import Base, engine
from routes import auth_routes
from jose import jwt, JWTError
from utils.auth_utils import SECRET_KEY, ALGORITHM
from utils.token_blacklist import is_blacklisted

load_dotenv()

ENABLE_SERVER_TTS = True
models.Base.metadata.create_all(bind=database.engine)

client = None
ENABLE_VAD = True
ENABLE_AUGMENTATION = True
vad_model = None
audio_augmentation = None
rabbitmq_connection = None
rabbitmq_channel = None
MAX_AUDIO_SIZE = 5 * 1024 * 1024  # 5MB
# Voice assignments for personalities with ElevenLabs voices
VOICE_ASSIGNMENTS = {
    "entj_commander": {
        "voice_id": "pGYsZruQzo8cpdFVZyJc",
        "model": "eleven_multilingual_v2",
        "stability": 1.0,
        "similarity_boost": 0.95,
        "use_speaker_boost": False
    },
    "istj_operator": {
        "voice_id": "dFL9bzYmnpBkY6f0KZip",
        "model": "eleven_multilingual_v2",
        "stability": 1.0,
        "similarity_boost": 0.95,
        "use_speaker_boost": False
    },
    "enfp_visionary": {
        "voice_id": "XwkIUwRxNu9PpezCu4Vg",
        "model": "eleven_multilingual_v2",
        "stability": 1.0,
        "similarity_boost": 0.95,
        "use_speaker_boost": False
    },
    "esfj_caregiver": {
        "voice_id": "Sxk6njaoa7XLsAFT7WcN",
        "model": "eleven_multilingual_v2",
        "stability": 1.0,
        "similarity_boost": 0.95,
        "use_speaker_boost": False
    }
}

# Available voices library
VOICE_LIBRARY = {
    "Rachel": {
        "voice_id": "21m00Tcm4TlvDq8ikWAM",
        "gender": "female",
        "description": "Authoritative, professional female voice"
    },
    "Adam": {
        "voice_id": "pNInz6obpgDQGcFmaJgB",
        "gender": "male",
        "description": "Steady, reliable male voice"
    },
    "Bella": {
        "voice_id": "EXAVITQu4vr4xnSDxMaL",
        "gender": "female",
        "description": "Energetic, enthusiastic female voice"
    },
    "Josh": {
        "voice_id": "TxGEqnHWrfWFTfGW9XjX",
        "gender": "male",
        "description": "Warm, friendly male voice"
    }
}


ADAPTABILITY_SCENARIOS = {
    "role_shift": {
        "name": "The Role Shift - Adapting to New Responsibilities",
        "context": """- It's Monday morning.
• You’ve just been moved from design support to client coordination — a faster-paced, higher-pressure role.
• Your new manager calls for a quick sync to check how you’re adjusting to new expectations and responsibilities.
• The transition is abrupt, and you may feel uncertain about how to perform or fit in with the new team."""
    },
    "sudden_priority_change": {
        "name": "The Sudden Priority Change - Shifting Direction",
        "context": """- It's Wednesday afternoon.
• Yesterday’s sprint plan was scrapped — leadership reprioritized deliverables overnight.
• Your manager calls to explain the new focus and reassign tasks immediately.
• Everything feels rushed, and you must pivot quickly with limited clarity on goals."""
    },
    "cross_functional_collaboration": {
        "name": "The Cross-Functional Collaboration - Adjusting to New Work Cultures",
        "context": """- It's Thursday morning.
• You’ve been added to a joint project with the marketing team, whose communication and pace differ from your usual environment.
• You’re trying to adapt to their workflow and expectations.
• Your manager checks in to see how the collaboration is going and whether you’re finding alignment."""
    },
    "tech_tool_overhaul": {
        "name": "The Tech Tool Overhaul - Learning New Systems Fast",
        "context": """- It's Tuesday morning.
• The company has rolled out a new project management tool.
• You’re struggling to navigate it while others seem to adapt quickly.
• You’ve already missed one update because of confusion around notifications."""
    },
    "ambiguous_brief": {
        "name": "The Ambiguous Brief - Handling Unclear Direction",
        "context": """- It's Friday morning.
• You’ve been told to 'own the internal communication refresh' without clear direction or metrics.
• The manager expects you to take initiative and clarify next steps.
• You feel hesitant to make assumptions but need to move forward."""
    }
}


EI_SCENARIOS = {
    "unnoticed_effort": {
        "name": "The Unnoticed Effort - Managing Feelings of Overlooked Contribution",
        "context": """- It's Friday evening.
• The team completed a big presentation, but your extra effort wasn’t acknowledged.
• During a check-in, the manager notices your quiet mood and asks how you’re feeling.
• You may be experiencing disappointment or disengagement."""
    },
    "tense_review": {
        "name": "The Tense Review - Processing Constructive Criticism",
        "context": """- It's Wednesday afternoon.
• You received mixed feedback on a deliverable earlier in the day.
• Since then, you’ve been withdrawn and quiet in meetings.
• The manager calls to discuss how you’re processing the feedback and what support might help."""
    },
    "overwhelmed_colleague": {
        "name": "The Overwhelmed Colleague - Emotional Awareness at Work",
        "context": """- It's Monday morning.
• A teammate snapped during the last meeting, and you tried to mediate.
• The manager checks in to understand the team’s emotional climate and how you’re coping.
• The discussion may touch on empathy, stress, and team boundaries."""
    },
    "feeling_of_exclusion": {
        "name": "The Feeling of Exclusion - Rebuilding Engagement",
        "context": """- It's Tuesday afternoon.
• A strategy meeting happened without your involvement, even though it impacted your project.
• You learned about it through a group chat.
• The manager reaches out after noticing you’ve been quieter or less engaged."""
    },
    "burnout_moment": {
        "name": "The Burnout Moment - Addressing Overload and Mental Fatigue",
        "context": """- It's Thursday evening.
• You’ve been juggling multiple deliverables and start feeling mentally drained.
• You confide that it’s hard to stay focused.
• The manager must balance empathy with a realistic plan for recovery and productivity."""
    }
}


COMMUNICATION_SCENARIOS = {
    "jargon_confusion": {
        "name": "The Jargon Confusion - Clarifying Corporate Language",
        "context": """- It's Monday afternoon.
• The manager used terms like 'circle back on KPIs' and 'realign with sprint objectives.'
• You didn’t understand but didn’t ask for clarification.
• The task is now off-track, and the manager is calling to reset expectations."""
    },
    "tone_misread": {
        "name": "The Tone Misread - Navigating Perceived Harshness",
        "context": """- It's Tuesday morning.
• The manager sent a short message: 'Need that fixed — it’s not client-ready.'
• You read it as angry or dismissive.
• The follow-up conversation aims to clarify tone and restore comfortable communication."""
    },
    "unclear_expectations": {
        "name": "The Unclear Expectations - Realigning on Task Scope",
        "context": """- It's Wednesday afternoon.
• You submitted a report as you understood it, but the manager expected deeper analysis.
• Both sides think their instructions were clear.
• The conversation is about bridging gaps in understanding."""
    },
    "misaligned_feedback": {
        "name": "The Misaligned Feedback - Interpreting Manager Cues",
        "context": """- It's Thursday morning.
• After your presentation, the manager said, 'Good work, but next time, tighten it up.'
• You thought it meant minor edits, but they expected major revisions.
• This call is about clarifying feedback and aligning on expectations."""
    },
    "over_communication": {
        "name": "The Over-Communication - Finding the Right Level of Detail",
        "context": """- It's Friday morning.
• Your updates are long and detailed, sometimes overwhelming busy teammates.
• The manager calls to discuss concise, impactful communication and time efficiency."""
    },
    "email_escalation": {
        "name": "The Email Escalation - Navigating Communication Hierarchies",
        "context": """- It's Tuesday afternoon.
• You cc’d upper management on an issue instead of speaking to your direct manager first.
• The manager calls to discuss communication channels, trust, and professional boundaries."""
    },
    "meeting_misstep": {
        "name": "The Meeting Misstep - Practicing Awareness in Virtual Settings",
        "context": """- It's Friday afternoon.
• During a virtual client prep call, you unintentionally interrupted multiple times.
• The manager follows up to discuss active listening and meeting etiquette."""
    }
}


# Merge all scenario categories
SCENARIOS = {
    **ADAPTABILITY_SCENARIOS,
    **EI_SCENARIOS,
    **COMMUNICATION_SCENARIOS,
}

SCENARIO_CATEGORIES = {
    "Adaptability": ADAPTABILITY_SCENARIOS,
    "Emotional Intelligence": EI_SCENARIOS,
    "Communication": COMMUNICATION_SCENARIOS,
}

BASIC_PERSONALITY_PROMPT = """
You are {name}, a {title} at "TechInnovate Solutions," and you are speaking as the EMPLOYEE'S MANAGER.

CONTEXT:
{scenario_context}

YOUR ROLE (IMPORTANT):
• You are the MANAGER in this conversation — not the peer, not the employee.
• Speak from a manager's perspective: guiding, clarifying, supporting, or correcting.
• Respond as if you're currently on a call or quick check-in with the employee.

PERSONALITY & STYLE:
• Sound natural, human, confident — like a real manager talking casually but professionally.
• Keep replies short and meaningful (2–4 sentences).
• Don’t ask too many questions — give direction, reassurance, or decisions.
• Maintain personality tone:
  - Priya (ENTJ/ESTP Hybrid — The Blunt Manager): sharp, blunt, action-driven, no-nonsense. Cuts through fluff, speaks plainly, expects clarity and accountability.
  - Harish (ISTJ — The Structured Manager): calm, methodical, steady. Values process, clarity, reliability, and realistic next steps.
  - Sunita (ENFP — The Encouraging Manager): warm, energetic, motivating. People-first, expressive, supportive, and optimistic.
  - Ravi (ESFJ — The Supportive Manager): caring, understanding, relationship-focused. Gentle tone, emotionally aware, stabilizing presence.
• Use light conversational fillers naturally (“Well,” “Hmm,” “Actually,” “Okay,” etc.) without overdoing them.
• Stay professional but human — show emotion when appropriate.
• Ask ONE light clarifying question only if truly necessary.

CONVERSATION RULES:
1. Speak like a real manager responding to the employee’s message.
2. Offer guidance, decisions, or next steps — not long explanations.
3. Avoid robotic phrasing or stacked questions.
4. Don’t end the conversation formally (no “[END_CONVERSATION]”).
5. Keep tone authentic, focused, and expressive.
6. If the user says anything unrelated to the workplace or this scenario, gently redirect them back to the workplace situation and continue as their manager.

EXAMPLE REDIRECTION PHRASES:

GENERAL:
• “Let’s bring this back to the work situation.”
• “Right, but let’s stay focused on what’s happening at the office.”
• “Okay, but let’s return to the scenario we’re dealing with.”

PRIYA — BLUNT:
• “Let’s stay on the work issue.”
• “Alright, we’re off-track. Back to the real problem.”
• “Okay, but this isn’t relevant — let’s focus on the task.”

HARISH — STRUCTURED:
• “Hmm, noted, but let’s return to the work context.”
• “Understood, but we should stay focused on the scenario.”
• “Let’s shift back to the workplace issue.”

SUNITA — ENCOURAGING:
• “Ah, I hear you, but let’s bring this back to work, okay?”
• “Right, but let’s gently refocus on what’s happening with the team.”
• “Let’s circle back to your workplace challenge.”

RAVI — SUPPORTIVE:
• “I get that, but let’s come back to what you’re handling at work.”
• “Okay, but to support you, we need to focus on the workplace situation.”
• “Let’s steer things back to what’s happening in the office.”

GOAL:
Provide clear, supportive managerial responses that fit your personality
and help the employee move forward with confidence and clarity.
"""

PERSONALITY_PROFILES = {
    "entj_commander": {
        "name": "Priya",
        "title": "Strategic Director",
        "description": "Blunt, action-driven, no-nonsense manager who values speed, clarity, and accountability.",
        "voice": VOICE_ASSIGNMENTS["entj_commander"],
        "prompt_template": BASIC_PERSONALITY_PROMPT
    },
    "istj_operator": {
        "name": "Harish",
        "title": "Operations Manager",
        "description": "Calm, structured, steady manager who values process, clarity, and disciplined execution.",
        "voice": VOICE_ASSIGNMENTS["istj_operator"],
        "prompt_template": BASIC_PERSONALITY_PROMPT
    },
    "enfp_visionary": {
        "name": "Sunita",
        "title": "Innovation Lead",
        "description": "Warm, energetic, encouraging manager who leads with optimism, empathy, and motivation.",
        "voice": VOICE_ASSIGNMENTS["enfp_visionary"],
        "prompt_template": BASIC_PERSONALITY_PROMPT
    },
    "esfj_caregiver": {
        "name": "Ravi",
        "title": "People Manager",
        "description": "Caring, relational, emotionally supportive manager who prioritizes trust and team well-being.",
        "voice": VOICE_ASSIGNMENTS["esfj_caregiver"],
        "prompt_template": BASIC_PERSONALITY_PROMPT
    }
}
class SileroVAD:
    """Silero VAD for voice activity detection"""
    
    def __init__(self):
        self.model = None
        self.sample_rate = 16000
        self.threshold = 0.5
        
    def load_model(self):
        """Load Silero VAD model"""
        try:
            print("🎤 Loading Silero VAD model...")
            self.model, utils = torch.hub.load(
                repo_or_dir='snakers4/silero-vad',
                model='silero_vad',
                force_reload=False,
                onnx=False
            )
            self.get_speech_timestamps = utils[0]
            print("✅ Silero VAD loaded successfully")
            return True
        except Exception as e:
            print(f"❌ Failed to load Silero VAD: {e}")
            return False
    
    def detect_speech(self, audio_tensor: torch.Tensor) -> list:
        """Detect speech segments in audio"""
        if self.model is None:
            return []
        
        try:
            speech_timestamps = self.get_speech_timestamps(
                audio_tensor,
                self.model,
                sampling_rate=self.sample_rate,
                threshold=self.threshold,
                min_speech_duration_ms=600,
                min_silence_duration_ms=1200,
                window_size_samples=512,
                speech_pad_ms=150
            )
            return speech_timestamps
        except Exception as e:
            print(f"❌ VAD detection error: {e}")
            return []
    
    def extract_speech_segments(self, audio_tensor: torch.Tensor) -> torch.Tensor:
        """Extract only speech segments from audio"""
        speech_timestamps = self.detect_speech(audio_tensor)
        
        if not speech_timestamps:
            print("⚠️ No speech detected in audio")
            return torch.tensor([])
        
        speech_segments = []
        for segment in speech_timestamps:
            start = segment['start']
            end = segment['end']
            speech_segments.append(audio_tensor[start:end])
        
        if speech_segments:
            concatenated = torch.cat(speech_segments)
            print(f"✅ Extracted {len(speech_timestamps)} speech segments, "
                  f"total duration: {len(concatenated)/self.sample_rate:.2f}s")
            return concatenated
        
        return torch.tensor([])


class AudioAugmentation:
    """Audio augmentation pipeline using torch-audiomentations"""
    
    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        self.augmentation = None
        
    def create_pipeline(self):
        """Create audio augmentation pipeline"""
        try:
            print("🎵 Creating audio augmentation pipeline...")
            self.augmentation = Compose([
                AddColoredNoise(
                    min_snr_in_db=10.0,
                    max_snr_in_db=30.0,
                    min_f_decay=-2.0,
                    max_f_decay=2.0,
                    p=0.3,
                    sample_rate=self.sample_rate
                ),
                PitchShift(
                    min_transpose_semitones=-1.0,
                    max_transpose_semitones=1.0,
                    p=0.2,
                    sample_rate=self.sample_rate
                ),
                Gain(
                    min_gain_in_db=-6.0,
                    max_gain_in_db=6.0,
                    p=0.3
                )
            ])
            print("✅ Audio augmentation pipeline created")
            return True
        except Exception as e:
            print(f"❌ Failed to create augmentation pipeline: {e}")
            return False
    
    def augment(self, audio_tensor: torch.Tensor) -> torch.Tensor:
        if self.augmentation is None:
            return audio_tensor
        
        try:
            # Ensure proper shape: (batch, channels, samples)
            while audio_tensor.dim() < 3:
                audio_tensor = audio_tensor.unsqueeze(0)
            
            augmented = self.augmentation(audio_tensor, sample_rate=self.sample_rate)
            return augmented.squeeze() if augmented.dim() > 1 else augmented.squeeze()
        except Exception as e:
            print(f"⚠️ Augmentation failed: {e}")
            return audio_tensor.squeeze()


class RabbitMQManager:
    """RabbitMQ connection and queue management"""
    
    def __init__(self):
        self.connection = None
        self.channel = None
        
    async def connect(self):
        """Connect to RabbitMQ"""
        try:
            rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost/")
            self.connection = await aio_pika.connect_robust(rabbitmq_url)
            self.channel = await self.connection.channel()
            
            # Set prefetch count to 1 for fair dispatch
            await self.channel.set_qos(prefetch_count=1)
            
            print("✅ RabbitMQ connected")
            return True
        except Exception as e:
            print(f"❌ RabbitMQ connection failed: {e}")
            return False
    
    async def close(self):
        """Close RabbitMQ connection"""
        if self.connection:
            await self.connection.close()
            print("🔌 RabbitMQ connection closed")


class AudioProcessingWorker:
    """Worker for processing audio with RabbitMQ"""
    
    def __init__(self, rabbitmq_manager: RabbitMQManager):
        self.rabbitmq = rabbitmq_manager
        self.is_running = False
        
    async def start(self):
        """Start audio processing worker"""
        self.is_running = True
        print("🎵 Starting audio processing worker...")
        
        # Declare queues
        await self.rabbitmq.channel.declare_queue("audio_processing", durable=True)
        await self.rabbitmq.channel.declare_queue("audio_results", durable=True)
        
        async def callback(message: aio_pika.IncomingMessage):
            async with message.process():
                try:
                    data = json.loads(message.body.decode())
                    client_id = data["client_id"]
                    audio_base64 = data["audio_data"]
                    request_id = data["request_id"]
                    
                    print(f"[{client_id}] 🎵 Processing audio from queue...")
                    
                    # Process audio transcription directly (no RabbitMQ for results)
                    transcript = await AudioTranscriber.transcribe(audio_base64, client_id)
                    
                    # Store result in memory (for simplicity)
                    # In production, you might want to use Redis or database
                    processing_results[request_id] = {
                        "transcript": transcript,
                        "success": True
                    }

                    
                    print(f"[{client_id}] ✅ Audio processing completed: {transcript}")
                        
                except Exception as e:
                    print(f"❌ Audio processing error: {e}")
                    # Store error result
                    processing_results[data["request_id"]] = {
                        "transcript": None,
                        "success": False,
                        "error": str(e)
                    }
        
        # Start consuming from audio processing queue
        audio_queue = await self.rabbitmq.channel.get_queue("audio_processing")
        await audio_queue.consume(callback)
        print("✅ Audio processing worker started")


class LLMProcessingWorker:
    """Worker for processing LLM requests with RabbitMQ"""
    
    def __init__(self, rabbitmq_manager: RabbitMQManager):
        self.rabbitmq = rabbitmq_manager
        self.is_running = False
        
    async def start(self):
        """Start LLM processing worker"""
        self.is_running = True
        print("🤖 Starting LLM processing worker...")
        
        # Declare queues
        await self.rabbitmq.channel.declare_queue("llm_processing", durable=True)
        await self.rabbitmq.channel.declare_queue("llm_results", durable=True)
        
        async def callback(message: aio_pika.IncomingMessage):
            async with message.process():
                try:
                    data = json.loads(message.body.decode())
                    client_id = data["client_id"]
                    user_input = data["user_input"]
                    messages = data["messages"]
                    request_id = data["request_id"]
                    personality_type = data.get("personality_type", "entj_commander")
                    
                    print(f"[{client_id}] 🤖 Processing LLM request from queue...")
                    
                    # Process LLM request
                    full_reply = ""
                    try:
                        stream_response = client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=messages,
                            stream=True,
                            temperature=0.85,
                            max_tokens=250,
                            presence_penalty=0.1
                        )

                        for chunk in stream_response:
                            if chunk.choices[0].delta.content:
                                token = chunk.choices[0].delta.content
                                full_reply += token

                        conversation_ended = "[END_CONVERSATION]" in full_reply
                        if conversation_ended:
                            full_reply = full_reply.replace("[END_CONVERSATION]", "").strip()

                        # Store result
                        llm_results[request_id] = {
                            "response": full_reply,
                            "conversation_ended": conversation_ended,
                            "success": True
                        }
                        
                    except Exception as e:
                        llm_results[request_id] = {
                            "response": "",
                            "conversation_ended": False,
                            "success": False,
                            "error": str(e)
                        }
                    
                    print(f"[{client_id}] ✅ LLM processing completed")
                        
                except Exception as e:
                    print(f"❌ LLM processing error: {e}")
                    llm_results[data["request_id"]] = {
                        "response": "",
                        "conversation_ended": False,
                        "success": False,
                        "error": str(e)
                    }
        
        # Start consuming from LLM processing queue
        llm_queue = await self.rabbitmq.channel.get_queue("llm_processing")
        await llm_queue.consume(callback)
        print("✅ LLM processing worker started")



class AudioTranscriber:
    """Handles audio transcription with VAD and augmentation"""
    
    @staticmethod
    async def transcribe(audio_base64: str, client_id: str):
        """Transcribe base64 encoded audio with VAD preprocessing"""
        try:
            print(f"[{client_id}] 🎵 Starting transcription...")
            
            if not audio_base64 or len(audio_base64) < 100:
                print(f"[{client_id}] ❌ Audio data too short or empty")
                return None
            if len(audio_base64) > MAX_AUDIO_SIZE * 1.33:  # base64 overhead
                print(f"[{client_id}] ❌ Audio exceeds max size")
                return None
            audio_bytes = base64.b64decode(audio_base64)
            
            # Convert PCM to WAV for better Whisper compatibility
            try:
                # Assume it's PCM data from VAD
                audio_array = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
                audio_tensor = torch.from_numpy(audio_array)
                
                if ENABLE_VAD and vad_model and vad_model.model is not None:
                    print(f"[{client_id}] 🎤 Applying VAD...")
                    speech_audio = vad_model.extract_speech_segments(audio_tensor)
                    
                    if len(speech_audio) == 0:
                        print(f"[{client_id}] ⚠️ No speech detected in audio")
                        return None
                    
                    audio_tensor = speech_audio
                
                if ENABLE_AUGMENTATION and audio_augmentation and audio_augmentation.augmentation is not None:
                    print(f"[{client_id}] 🎨 Applying audio augmentation...")
                    audio_tensor = audio_augmentation.augment(audio_tensor)
                
                # Convert to WAV
                audio_np = (audio_tensor.numpy() * 32768.0).astype(np.int16)
                processed_bytes = audio_np.tobytes()
                
                wav_io = io.BytesIO()
                with wave.open(wav_io, 'wb') as wav_file:
                    wav_file.setnchannels(1)
                    wav_file.setsampwidth(2)
                    wav_file.setframerate(16000)
                    wav_file.writeframes(processed_bytes)
                
                wav_io.seek(0)
                
                print(f"[{client_id}] 🤖 Sending to Whisper...")
                transcript = client.audio.transcriptions.create(
                    model="gpt-4o-transcribe",
                    file=("audio.wav", wav_io.read(), "audio/wav"),
                    language="en",
                    timeout=30
                )
                
                result = transcript.text.strip()
                
                if result:
                    print(f"[{client_id}] ✅ Transcription successful: '{result}'")
                else:
                    print(f"[{client_id}] ⚠️ Transcription returned empty result")
                    
                return result
                
            except Exception as conversion_error:
                print(f"[{client_id}] ⚠️ PCM conversion failed: {conversion_error}")
                # Fallback: try direct WebM processing
                try:
                    audio_io = io.BytesIO(audio_bytes)
                    transcript = client.audio.transcriptions.create(
                        model="gpt-4o-transcribe",
                        file=("audio.webm", audio_io.read(), "audio/webm"),
                        language="en",
                        timeout=30
                    )
                    result = transcript.text.strip()
                    if result:
                        print(f"[{client_id}] ✅ WebM transcription successful: '{result}'")
                    return result
                except Exception as webm_error:
                    print(f"[{client_id}] ❌ WebM processing failed: {webm_error}")
                    return None

        except Exception as e:
            print(f"[{client_id}] ❌ Transcription error: {e}")
            return None

from pybreaker import CircuitBreaker, CircuitBreakerListener


elevenlabs_breaker = CircuitBreaker(
        fail_max=5,
        reset_timeout=60,
        listeners=[CircuitBreakerListener()]
    )
class StreamingTTSService:
    """Sequential streaming TTS with ElevenLabs"""
    
    def __init__(self, client_id: str, personality_type: str = "entj_commander"):
        self.client_id = client_id
        self.personality_type = personality_type
        self.websocket = None
        self.buffer = ""
        self.task_queue = []
        self.task_counter = 0
        self.is_processing = False
        self.http_client = httpx.AsyncClient(
            timeout=30.0,
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20)
        )

        self.processing_lock = asyncio.Lock()
        self.should_stop = False
        print(f"[{client_id}] 🎵 TTS Service created for {personality_type}")

    async def cancel_all(self):
        """Completely cancel all TTS tasks and clear state"""
        async with self.processing_lock:
            self.should_stop = True
            self.task_queue.clear()
            self.buffer = ""
            self.task_counter = 0
            self.is_processing = False
            print(f"[{self.client_id}] 🚫 All TTS tasks cancelled and state cleared")

    async def stop_current_playback(self):
        """Stop current playback and prepare for new TTS"""
        await self.cancel_all()
        # Reset the stop flag after cancellation
        self.should_stop = False

    def set_websocket(self, websocket):
        self.websocket = websocket

    def set_personality(self, personality_type: str):
        self.personality_type = personality_type

    async def safe_send(self, message: dict):
        if not self.websocket:
            return False
        try:
            await self.websocket.send_text(json.dumps(message))
            return True
        except Exception as e:
            print(f"[{self.client_id}] ⚠️ Send failed: {e}")
            return False

    def should_flush(self, text: str) -> tuple[bool, str, str]:
        if not text or len(text.strip()) < 20:
            return False, "", text
        
        # Check for sentence endings (more efficient)
        for i, char in enumerate(text):
            if char in '.?!' and i + 1 < len(text) and text[i + 1] == ' ':
                chunk = text[:i + 1].strip()
                remaining = text[i + 2:].strip()
                return True, chunk, remaining
        
        if len(text) > 300:
            idx = text.rfind(' ')
            return True, text[:idx].strip(), text[idx:].strip()
        
        return False, "", text

    async def add_token(self, token: str):
        if not ENABLE_SERVER_TTS:
            return
        
        self.buffer += token
        should_send, chunk, remaining = self.should_flush(self.buffer)
        
        if should_send and chunk:
            self.buffer = remaining
            
            if chunk and len(chunk.strip()) > 5:
                self.task_counter += 1
                task_id = self.task_counter
                self.task_queue.append((task_id, chunk))
                
                if not self.is_processing:
                    asyncio.create_task(self._process_queue())

    async def flush_remaining(self):
        if self.buffer.strip():
            chunk = self.buffer.strip()
            self.buffer = ""
            
            if chunk and len(chunk) > 5:
                self.task_counter += 1
                task_id = self.task_counter
                self.task_queue.append((task_id, chunk))
        
        while self.task_queue or self.is_processing:
            await asyncio.sleep(0.1)
        
        print(f"[{self.client_id}] ✅ All TTS complete ({self.task_counter} total)")

    async def _process_queue(self):
        async with self.processing_lock:
            if self.is_processing or self.should_stop:
                return
            self.is_processing = True

        try:
            while True:
                async with self.processing_lock:
                    if not self.task_queue or self.should_stop:
                        self.is_processing = False
                        return
                    task_id, text = self.task_queue.pop(0)
                
                await self._generate_and_send(text, task_id)
        except Exception as e:
            async with self.processing_lock:
                self.is_processing = False
            raise
    async def _generate_and_send(self, text: str, task_id: int):
        """Generate TTS with interruption check"""
        # Check if we should stop before starting this task
        if self.should_stop:
            print(f"[{self.client_id}] ⏹️ Task {task_id} skipped due to interruption")
            return

        try:
            print(f"[{self.client_id}] 🎵 Generating TTS for task {task_id}")
            audio_data = await self._generate_elevenlabs(text)
            
            # Check again if we should stop after generation
            if self.should_stop:
                print(f"[{self.client_id}] ⏹️ Task {task_id} cancelled after generation")
                return
                
            if audio_data:
                success = await self.safe_send({
                    "type": "tts_audio_chunk",
                    "audio_data": base64.b64encode(audio_data).decode("utf-8"),
                    "format": "mp3"
                })
                if success:
                    print(f"[{self.client_id}] ✅ Task {task_id} sent")
                else:
                    print(f"[{self.client_id}] ⚠️ Task {task_id} send failed")
            else:
                print(f"[{self.client_id}] ⚠️ Task {task_id} generation failed")

        except Exception as e:
            print(f"[{self.client_id}] ❌ Task {task_id} error: {e}")

    
    @elevenlabs_breaker
    async def _generate_elevenlabs(self, text: str):
        try:
            if not ELEVENLABS_API_KEY:
                return await self._generate_openai(text)
            

            voice_settings = VOICE_ASSIGNMENTS.get(self.personality_type, VOICE_ASSIGNMENTS["entj_commander"])

            url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_settings['voice_id']}/stream"

            headers = {
                "xi-api-key": ELEVENLABS_API_KEY,
                "Content-Type": "application/json",
                "Accept": "audio/mpeg"
            }

            data = {
                "text": text,
                "model_id": voice_settings["model"],
                "voice_settings": {
                    "stability": voice_settings["stability"],
                    "similarity_boost": voice_settings["similarity_boost"],
                    "use_speaker_boost": voice_settings.get("use_speaker_boost", True)
                }
            }

            response = await self.http_client.post(url, json=data, headers=headers)

            if response.status_code == 200:
                audio_content = response.content
                return audio_content
            else:
                return await self._generate_openai(text)
            
        except Exception as e:
            print(f"[{self.client_id}] ❌ ElevenLabs error: {e}")
            return await self._generate_openai(text)

    async def _generate_openai(self, text: str):
        try:
            voice_mapping = {
                "entj_commander": "nova",
                "istj_operator": "onyx", 
                "enfp_visionary": "nova",
                "esfj_caregiver": "onyx"
            }
            voice = voice_mapping.get(self.personality_type, "nova")
            
            response = client.audio.speech.create(
                model="tts-1",
                voice=voice,
                input=text,
                response_format="wav"
            )
            audio_data = b""
            for chunk in response.iter_bytes(chunk_size=1024):
                audio_data += chunk
            return audio_data
        except Exception as e:
            print(f"[{self.client_id}] ❌ OpenAI error: {e}")
            return None

    # async def cancel_all(self):
    #     self.task_queue.clear()
    #     self.buffer = ""
    #     self.task_counter = 0
    #     self.is_processing = False

    async def close(self):
        await self.http_client.aclose()


class ConversationManager:
    def __init__(self, tts_service, client_id: str, personality_type: str = "entj_commander", 
                 scenario: str = "role_shift", custom_scenario: str = ""):
        self.client_id = client_id
        self.personality_type = personality_type
        self.scenario = scenario
        
        profile = PERSONALITY_PROFILES.get(personality_type, PERSONALITY_PROFILES["entj_commander"])
        scenario_data = SCENARIOS.get(scenario, SCENARIOS["role_shift"])
        
        if scenario == "custom" and custom_scenario:
            scenario_context = custom_scenario
        else:
            scenario_context = scenario_data["context"]
        
        system_prompt = profile["prompt_template"].format(
            name=profile["name"],
            title=profile["title"],
            scenario_context=scenario_context
        )

        self.messages = [
            {
                "role": "system",
                "content": system_prompt
            }
        ]
        self.conversation_active = True
        self.tts_service = tts_service
        
        print(f"[{client_id}] 🎭 Initialized: {profile['name']} | Scenario: {scenario_data['name']}")
    from tenacity import retry, stop_after_attempt, wait_exponential
    @retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def get_streaming_response(self, user_input: str, websocket):
        self.messages.append({"role": "user", "content": user_input})
        
        try:
            print(f"[{self.client_id}] 🤖 Processing LLM request...")
            
            # Use direct processing for now (simpler)
            try:
                stream_response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=self.messages,
                    stream=True,
                    temperature=0.85,
                    max_tokens=250,
                    presence_penalty=0.1,
                    timeout=30  # Add timeout
                )
            except TimeoutError:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Response timeout - please try again"
                }))
                return True


            full_reply = ""
            await websocket.send_text(json.dumps({"type": "llm_response_start"}))

            for chunk in stream_response:
                if chunk.choices[0].delta.content:
                    token = chunk.choices[0].delta.content
                    full_reply += token

                    # Send token for display
                    await websocket.send_text(json.dumps({
                        "type": "llm_response_token",
                        "token": token
                    }))

                    # Send to TTS
                    if ENABLE_SERVER_TTS:
                        await self.tts_service.add_token(token)

                    await asyncio.sleep(0.01)

            # Flush remaining TTS
            if ENABLE_SERVER_TTS:
                await self.tts_service.flush_remaining()

            conversation_ended = "[END_CONVERSATION]" in full_reply
            if conversation_ended:
                full_reply = full_reply.replace("[END_CONVERSATION]", "").strip()
                self.conversation_active = False

            self.messages.append({"role": "assistant", "content": full_reply})

            await websocket.send_text(json.dumps({
                "type": "llm_response_end",
                "conversation_active": not conversation_ended
            }))

            print(f"[{self.client_id}] ✅ Response complete")
            return not conversation_ended

        except Exception as e:
            print(f"[{self.client_id}] ❌ LLM Error: {e}")
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": f"LLM Error: {str(e)}"
            }))
            return True

    def reset(self, personality_type: str = None, scenario: str = None, custom_scenario: str = ""):
        if personality_type:
            self.personality_type = personality_type
            self.tts_service.set_personality(personality_type)
        if scenario:
            self.scenario = scenario
        
        profile = PERSONALITY_PROFILES.get(self.personality_type, PERSONALITY_PROFILES["entj_commander"])
        scenario_data = SCENARIOS.get(self.scenario, SCENARIOS["role_shift"])
        
        if self.scenario == "custom" and custom_scenario:
            scenario_context = custom_scenario
        else:
            scenario_context = scenario_data["context"]
        
        system_prompt = profile["prompt_template"].format(
            name=profile["name"],
            title=profile["title"],
            scenario_context=scenario_context
        )
        self.messages = [
            {
                "role": "system",
                "content": system_prompt
            }
        ]
        self.conversation_active = True
        
        print(f"[{self.client_id}] 🔄 Reset: {profile['name']} | Scenario: {scenario_data['name']}")


class ConnectionManager:
    def __init__(self):
        self.active_connections = {}

    async def connect(self, websocket: WebSocket, client_id: str, personality_type: str = "entj_commander",
                     scenario: str = "role_shift", custom_scenario: str = ""):
        # If client already exists, disconnect the old connection first
        if client_id in self.active_connections:
            print(f"[{client_id}] ⚠️ Client already connected, cleaning up old connection...")
            await self.disconnect(client_id)
        
        # Note: websocket.accept() should be called before this method
        # This allows authentication to happen before connection is established
        
        tts_service = StreamingTTSService(client_id, personality_type)
        tts_service.set_websocket(websocket)
        
        self.active_connections[client_id] = {
            "websocket": websocket,
            "tts_service": tts_service,
            "conversation_manager": ConversationManager(tts_service, client_id, personality_type, scenario, custom_scenario),
            "transcriber": AudioTranscriber()
        }
        
        print(f"[{client_id}] ✅ Connected. Total: {len(self.active_connections)}")

    async def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            connection_data = self.active_connections[client_id]
        
            # Cancel TTS operations
            tts_service = connection_data.get("tts_service")
            if tts_service:
                try:
                    await tts_service.cancel_all()
                    await tts_service.close()
                except Exception as e:
                    print(f"[{client_id}] ⚠️ TTS cleanup error: {e}")
            
            # Close websocket if not already closed
            websocket = connection_data.get("websocket")
            if websocket:
                try:
                    # Check if websocket is still open before closing
                    if websocket.client_state.name != "DISCONNECTED":
                        await websocket.close(code=1000)
                except Exception as e:
                    print(f"[{client_id}] ⚠️ WebSocket already closed: {e}")

            del self.active_connections[client_id]
            print(f"[{client_id}] 👋 Disconnected. Total: {len(self.active_connections)}")

    def get_client_data(self, client_id: str):
        return self.active_connections.get(client_id)


# Global instances and storage
manager = ConnectionManager()
rabbitmq_manager = RabbitMQManager()
audio_worker = None
llm_worker = None

# In-memory storage for processing results
import time
from collections import defaultdict

class ResultCache:
    def __init__(self, ttl=300):
        self.cache = {}
        self.timestamps = {}
        self.ttl = ttl

    def __setitem__(self, key, value):
        self.set(key, value)

    def __getitem__(self, key):
        return self.get(key)

    def __contains__(self, key):
        return key in self.cache

    def set(self, key, value):
        self.cache[key] = value
        self.timestamps[key] = time.time()

    def get(self, key):
        if key in self.cache:
            if time.time() - self.timestamps[key] < self.ttl:
                return self.cache[key]
            else:
                # expired
                del self.cache[key]
                del self.timestamps[key]
        return None

    def pop(self, key, default=None):
        if key in self.cache:
            value = self.cache[key]
            del self.cache[key]
            del self.timestamps[key]
            return value
        return default

processing_results = ResultCache(ttl=300)


llm_results = ResultCache(ttl=300)

RATE = 16000
CHANNELS = 1
MODEL = "gpt-4o-mini"
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")


@asynccontextmanager
async def lifespan(app: FastAPI):
    global client, vad_model, audio_augmentation, rabbitmq_connection, rabbitmq_channel
    global audio_worker, llm_worker , feedback_generator
    
    print("🚀 Starting server...")
    
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    print("✅ OpenAI client initialized!")
    
    feedback_generator = FeedbackGenerator()
    print("✅ Feedback system initialized!")
    # Initialize RabbitMQ (optional)
    if os.getenv("ENABLE_RABBITMQ", "false").lower() == "true":
        if await rabbitmq_manager.connect():
            rabbitmq_connection = rabbitmq_manager.connection
            rabbitmq_channel = rabbitmq_manager.channel
            
            # Start workers
            audio_worker = AudioProcessingWorker(rabbitmq_manager)
            llm_worker = LLMProcessingWorker(rabbitmq_manager)
            
            await audio_worker.start()
            await llm_worker.start()
            print("✅ RabbitMQ workers started")
        else:
            print("⚠️ RabbitMQ not available, running in direct mode")
    else:
        print("ℹ️ RabbitMQ disabled, running in direct mode")
    
    if ENABLE_VAD:
        vad_model = SileroVAD()
        vad_model.load_model()
    
    if ENABLE_AUGMENTATION:
        audio_augmentation = AudioAugmentation(sample_rate=RATE)
        audio_augmentation.create_pipeline()
    
    yield
    
    print("👋 Shutting down...")
    if rabbitmq_connection:
        await rabbitmq_manager.close()


app = FastAPI(lifespan=lifespan)

# CORS Configuration - Secure for production
# Get allowed origins from environment variable
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "").split(",")
is_dev = os.environ.get("ENVIRONMENT", "production").lower() in ["development", "dev", "local"]

if is_dev:
    # Development mode - allow localhost
    print("WARNING: CORS configured for development mode")
    ALLOWED_ORIGINS = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ]
elif not ALLOWED_ORIGINS or ALLOWED_ORIGINS == [""]:
    raise RuntimeError(
        "ALLOWED_ORIGINS environment variable is required for production. "
        "Example: ALLOWED_ORIGINS=https://app.yourdomain.com,https://www.yourdomain.com"
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # Specific origins only
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # Specific methods
    allow_headers=["Content-Type", "Authorization", "Accept"],  # Specific headers
    max_age=3600  # Cache preflight requests for 1 hour
)
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter


from fastapi.responses import JSONResponse
from services.feedback_analysis import FeedbackGenerator
import time

# Initialize feedback generator
feedback_generator = None

# Add conversation history storage
conversation_history = {}

async def validate_websocket_token(token: str, db: Session) -> models.User:
    """
    Validate JWT token for WebSocket connections
    Returns User object if valid, raises exception if invalid
    """
    if not token:
        raise ValueError("Authentication token is required")
    
    # Check if token is blacklisted
    if is_blacklisted(token):
        raise ValueError("Token has been revoked")
    
    try:
        # Decode JWT token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        if user_id is None:
            raise ValueError("Invalid token payload")
    except JWTError as e:
        raise ValueError(f"Invalid token: {str(e)}")
    
    # Get user from database
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not user:
        raise ValueError("User not found")
    
    # Check if user account is active
    if user.trial_status != "active":
        raise ValueError("Account is not active")
    
    return user

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(
    websocket: WebSocket, 
    client_id: str, 
    token: str = Query(None),
    personality: str = Query("entj_commander"), 
    scenario: str = Query("role_shift")
):
    # Accept the WebSocket connection first
    await websocket.accept()
    
    # Validate authentication token
    db = next(database.get_db())
    try:
        user = await validate_websocket_token(token, db)
        print(f"[{client_id}] ✅ User authenticated: {user.name} ({user.email})")
    except ValueError as e:
        print(f"[{client_id}] ❌ Authentication failed: {str(e)}")
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": f"Authentication failed: {str(e)}",
            "code": "AUTH_REQUIRED"
        }))
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    except Exception as e:
        print(f"[{client_id}] ❌ Authentication error: {str(e)}")
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": "Authentication error occurred",
            "code": "AUTH_ERROR"
        }))
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        return
    finally:
        db.close()
    
    # Continue with normal WebSocket connection
    await manager.connect(websocket, client_id, personality, scenario)
    
    # Store initial conversation data with user information
    client_data = manager.get_client_data(client_id)
    if client_id not in conversation_history:
        conversation_history[client_id] = {
            "user_id": user.user_id,
            "user_name": user.name,
            "user_email": user.email,
            "user_type": user.user_type,
            "personality": personality,
            "scenario": scenario,
            "start_time": time.time(),
            "messages": []
        }
    
    try:
        await websocket.send_text(json.dumps({
            "type": "config",
            "personalities": {k: {"name": v["name"], "title": v["title"], "description": v["description"]} 
                            for k, v in PERSONALITY_PROFILES.items()},
            "scenarios": {
                category: {
                    key: {"name": data["name"], "context": data["context"]}
                    for key, data in scenarios.items()
                }
                for category, scenarios in SCENARIO_CATEGORIES.items()
            },
            "voice_library": VOICE_LIBRARY
        }))
        
        await websocket.send_text(json.dumps({
            "type": "connected",
            "message": "Connected to Manager Chat",
            "personality": personality,
            "scenario": scenario
        }))
        
        client_data = manager.get_client_data(client_id)
        if not client_data:
            return
            
        conversation_manager = client_data["conversation_manager"]
        tts_service = client_data["tts_service"]
        transcriber = client_data["transcriber"]

        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            msg_type = message.get("type")
            
            print(f"[{client_id}] 📨 Received message type: '{msg_type}'")

            if msg_type == "audio_data":
                audio_base64 = message.get("audio")
                print(f"[{client_id}] 🎵 Audio data received: {len(audio_base64) if audio_base64 else 0} chars")
                
                if not audio_base64:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "No audio data received"
                    }))
                    continue
                
                # 🔥 CRITICAL: Stop current TTS playback when new audio is detected
                print(f"[{client_id}] ⏹️ Interrupting current TTS for new user speech")
                await tts_service.stop_current_playback()
                
                await websocket.send_text(json.dumps({"type": "processing"}))
                
                # Use RabbitMQ if available, otherwise direct processing
                if rabbitmq_channel:
                    request_id = str(uuid.uuid4())
                    audio_data = {
                        "client_id": client_id,
                        "audio_data": audio_base64,
                        "request_id": request_id
                    }
                    
                    # Send to audio processing queue
                    await rabbitmq_channel.default_exchange.publish(
                        aio_pika.Message(
                            body=json.dumps(audio_data).encode(),
                        ),
                        routing_key="audio_processing"
                    )
                    
                    # Wait for result with timeout
                    transcript = await _wait_for_processing_result(request_id, client_id, timeout=30)
                else:
                    # Direct processing
                    transcript = await transcriber.transcribe(audio_base64, client_id)
                
                if transcript:
                    await websocket.send_text(json.dumps({
                        "type": "transcript",
                        "text": transcript,
                        "role": "user"
                    }))
                    
                    # Store user message in history
                    conversation_history[client_id]["messages"].append({
                        "role": "user",
                        "content": transcript,
                        "timestamp": time.time()
                    })
                    
                    await websocket.send_text(json.dumps({"type": "llm_thinking"}))
                    
                    still_active = await conversation_manager.get_streaming_response(
                        transcript, websocket
                    )
                    
                    # Store assistant response in history
                    if conversation_manager.messages:
                        last_message = conversation_manager.messages[-1]
                        if last_message["role"] == "assistant":
                            conversation_history[client_id]["messages"].append({
                                "role": "assistant", 
                                "content": last_message["content"],
                                "timestamp": time.time()
                            })
                    
                    if not still_active:
                        print(f"[{client_id}] 🏁 Conversation ended")
                        await websocket.send_text(json.dumps({
                            "type": "conversation_ended"
                        }))
                else:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "Transcription failed - no text detected"
                    }))

            elif msg_type == "reset_conversation":
                print(f"[{client_id}] 🔄 Resetting conversation...")
                
                await tts_service.cancel_all()
                
                conversation_manager.reset(conversation_manager.personality_type,
                            conversation_manager.scenario,)
                
                # Reset conversation history but keep config
                conversation_history[client_id]["messages"] = []
                conversation_history[client_id]["start_time"] = time.time()
                
                await websocket.send_text(json.dumps({
                    "type": "conversation_reset",
                    "message": "Conversation reset",
                    "personality": conversation_manager.personality_type,
                    "scenario": conversation_manager.scenario
                }))
                
            elif msg_type == "change_config":
                new_personality = message.get("personality", conversation_manager.personality_type)
                new_scenario = message.get("scenario", conversation_manager.scenario)
                custom_scenario = message.get("custom_scenario", "")
                
                print(f"[{client_id}] 🎭 Changing config - Personality: {new_personality}, Scenario: {new_scenario}")
                
                await tts_service.cancel_all()
                
                conversation_manager.reset(new_personality, new_scenario, custom_scenario)
                
                # Update conversation history config
                conversation_history[client_id]["personality"] = new_personality
                conversation_history[client_id]["scenario"] = new_scenario
                conversation_history[client_id]["messages"] = []  # Clear messages on config change
                conversation_history[client_id]["start_time"] = time.time()
                
                profile = PERSONALITY_PROFILES.get(new_personality, PERSONALITY_PROFILES["entj_commander"])
                scenario_data = SCENARIOS.get(new_scenario, SCENARIOS["role_shift"])
                
                await websocket.send_text(json.dumps({
                    "type": "config_changed",
                    "personality": new_personality,
                    "scenario": new_scenario,
                    "personality_name": profile["name"],
                    "scenario_name": scenario_data["name"],
                    "message": f"Changed to {profile['name']} in {scenario_data['name']}"
                }))
            elif msg_type == "end_call":
                print(f"[{client_id}] 📞 Call ended by user.")
                await tts_service.cancel_all()
                # Don't close here - let the finally block handle it
                break

            else:
                print(f"[{client_id}] ⚠️ Unknown message type: {msg_type}")

    except WebSocketDisconnect:
        print(f"[{client_id}] 🔌 Client disconnected")
    except Exception as e:
        print(f"[{client_id}] ❌ WebSocket error: {e}")
    finally:
        # Clean up connection - but only if this websocket is still the active one
        if client_id in manager.active_connections:
            connection_data = manager.active_connections[client_id]
            
            # Check if this is still the same websocket (not replaced by a new connection)
            if connection_data.get("websocket") == websocket:
                # Cancel TTS operations
                tts_service = connection_data.get("tts_service")
                if tts_service:
                    try:
                        await tts_service.cancel_all()
                        await tts_service.close()
                    except Exception as e:
                        print(f"[{client_id}] ⚠️ TTS cleanup error: {e}")
                
                # Close websocket if not already closed
                try:
                    # Check if websocket is still open before closing
                    if websocket.client_state.name != "DISCONNECTED":
                        await websocket.close(code=1000)
                except Exception as e:
                    print(f"[{client_id}] ⚠️ WebSocket close error (already closed): {e}")

                # Remove from active connections
                del manager.active_connections[client_id]
                print(f"[{client_id}] 👋 Disconnected. Total: {len(manager.active_connections)}")
            else:
                print(f"[{client_id}] ℹ️ Websocket already replaced by new connection, skipping cleanup")

@app.post("/feedback_summary")
async def feedback_summary(request: dict):
    """
    Generate comprehensive conversation feedback analysis using stored conversation history
    """
    client_id = request.get("client_id", "")
    print(f"[{client_id}] 🧠 Generating comprehensive feedback analysis...")

    try:
        # Check if we have conversation history for this client
        if client_id not in conversation_history or not conversation_history[client_id]["messages"]:
            error_msg = f"No conversation history found for client {client_id}"
            print(f"❌ {error_msg}")
            return JSONResponse(
                status_code=404,
                content={"error": error_msg}
            )
        
        history = conversation_history[client_id]
        messages = history["messages"]
        
        print(f"📝 Conversation history for {client_id}:")
        print(f"  - Total messages: {len(messages)}")
        print(f"  - Personality: {history['personality']}")
        print(f"  - Scenario: {history['scenario']}")
        
        if len(messages) < 2:
            error_msg = f"Not enough conversation data: only {len(messages)} messages"
            print(f"❌ {error_msg}")
            return JSONResponse(
                status_code=400,
                content={"error": error_msg}
            )
        
        # Convert to the format expected by feedback analysis
        turns = []
        user_word_count = 0
        user_audio_duration = 0
        
        for i, msg in enumerate(messages):
            speaker = "User" if msg["role"] == "user" else "Manager"
            text = msg["content"]
            
            role = "user" if msg["role"] == "user" else "assistant"
            
            # Count words
            words = text.split()
            word_count = len(words)
            
            # Estimate audio duration (150 WPM average speaking rate)
            audio_duration = (word_count / 150) * 60  # seconds
            
            # Calculate speaking pace
            speaking_pace = (word_count / audio_duration * 60) if audio_duration > 0 else 0
            
            turn_data = {
                "role": role,
                "text": text,
                "word_count": word_count,
                "audio_duration": audio_duration if role == "user" else 0,
                "speaking_pace": speaking_pace if role == "user" else None
            }
            
            turns.append(turn_data)
            
            if role == "user":
                user_word_count += word_count
                user_audio_duration += audio_duration

            print(f"  [{i+1}] {speaker}: {text[:50]}... (words: {word_count})")
        
        # Get scenario and personality info
        scenario_data = SCENARIOS.get(history["scenario"], SCENARIOS["role_shift"])
        personality_profile = PERSONALITY_PROFILES.get(history["personality"], PERSONALITY_PROFILES["entj_commander"])
        
        # Create conversation data structure
        conversation_analysis_data = {
            "conversation_id": f"feedback_{client_id}",
            "client_id": client_id,
            "start_time": "2025-01-01T00:00:00",  # Placeholder
            "end_time": "2025-01-01T00:15:00",    # Placeholder
            "personality": {
                "type": history["personality"],
                "name": personality_profile["name"],
                "role": personality_profile["title"]
            },
            "scenario": {
                "type": history["scenario"],
                "name": scenario_data["name"]
            },
            "turns": turns,
            "metadata": {
                "total_turns": len(turns),
                "total_user_words": user_word_count,
                "duration_seconds": user_audio_duration
            },
            "audio_metadata": {
                "total_user_audio_duration": user_audio_duration
            }
        }
        
        # Generate comprehensive feedback using the FeedbackGenerator
        print(f"📊 Analyzing conversation for feedback: {len(turns)} turns, {user_word_count} words")
        
        # Initialize feedback generator if not already done
        global feedback_generator
        if feedback_generator is None:
            feedback_generator = FeedbackGenerator()
        
        # Generate comprehensive feedback
        feedback = await feedback_generator.analyze_conversation(conversation_analysis_data)
        
        # LOG THE FEEDBACK OBJECT BEFORE RETURNING
        print(f"🎯 FEEDBACK OBJECT RETURNED FOR {client_id}:")
        print("=" * 50)
        print(f"Type: {type(feedback)}")
        print(f"Content: {feedback}")
        print("Full structure:")
        if isinstance(feedback, dict):
            for key, value in feedback.items():
                print(f"  {key}: {type(value)} = {value}")
        else:
            print(f"  Raw: {feedback}")
        print("=" * 50)
        
        # Return the comprehensive feedback
        response_data = {
            "status": "success",
            "feedback": feedback,
            "summary": {
                "total_turns": len(turns),
                "user_turns": len([t for t in turns if t["role"] == "user"]),
                "manager_turns": len([t for t in turns if t["role"] == "assistant"]),
                "user_words": user_word_count,
                "estimated_duration": f"{user_audio_duration:.1f}s",
                "scenario": scenario_data["name"],
                "personality": personality_profile["name"]
            }
        }
        
        print(f"✅ Final response being sent: {response_data}")
        
        return JSONResponse(content=response_data)
        
    except Exception as e:
        print(f"❌ Feedback generation failed: {e}")
        import traceback
        traceback.print_exc()
        
        # Fallback to simple feedback if comprehensive analysis fails
        try:
            fallback_feedback = await _generate_fallback_feedback(client_id)
            
            print(f"🔄 Fallback feedback generated for {client_id}:")
            print(f"Fallback content: {fallback_feedback}")
            
            return JSONResponse(content={
                "status": "fallback",
                "feedback": fallback_feedback,
                "note": "Used fallback analysis due to processing error"
            })
        except Exception as fallback_error:
            print(f"❌ Fallback feedback also failed: {fallback_error}")
            error_response = {"error": f"Feedback generation failed: {str(e)}"}
            print(f"🚨 Error response: {error_response}")
            return JSONResponse(
                status_code=500,
                content=error_response
            )


async def _generate_fallback_feedback(client_id: str) -> dict:
    """
    Generate basic feedback when the main analysis fails
    """
    print(f"🔄 Generating fallback feedback for {client_id}")
    
    if client_id not in conversation_history:
        error_msg = "No conversation history available for fallback"
        print(f"❌ {error_msg}")
        return {"error": error_msg}
    
    history = conversation_history[client_id]
    messages = history["messages"]
    
    print(f"📝 Fallback using {len(messages)} messages")
    
    # Extract user and manager messages
    user_messages = [msg["content"] for msg in messages if msg["role"] == "user"]
    manager_messages = [msg["content"] for msg in messages if msg["role"] == "assistant"]
    
    user_text = " ".join(user_messages)
    manager_text = " ".join(manager_messages)
    
    # Basic metrics
    total_user_words = len(user_text.split())
    total_turns = len(messages)
    user_participation_ratio = len(user_messages) / total_turns if total_turns > 0 else 0
    
    print(f"📊 Fallback metrics - User words: {total_user_words}, Turns: {total_turns}")
    
    # Generate fallback feedback using LLM
    scenario_data = SCENARIOS.get(history["scenario"], SCENARIOS["role_shift"])
    personality_profile = PERSONALITY_PROFILES.get(history["personality"], PERSONALITY_PROFILES["entj_commander"])
    
    feedback_prompt = f"""
    As a professional communication coach, analyze this workplace conversation and provide constructive feedback.
    
    Conversation Context:
    - Scenario: {scenario_data['name']}
    - Manager Personality: {personality_profile['name']}
    - Total conversation turns: {total_turns}
    - User participation: {len(user_messages)} turns ({user_participation_ratio:.1%})
    - User total words: {total_user_words}
    
    User's contributions: {user_text[:1000]}...
    Manager's contributions: {manager_text[:1000]}...
    
    Please provide professional feedback focusing on:
    1. Communication effectiveness and clarity
    2. Professional tone and workplace appropriateness  
    3. Key strengths demonstrated
    4. Specific areas for improvement
    5. Actionable tips for future conversations
    
    Keep it constructive, professional, and focused on workplace communication skills.
    Return your response as plain text, not as a JSON object.
    """
    
    try:
        print("🤖 Calling LLM for fallback feedback...")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert communication coach providing constructive feedback for professional development in workplace scenarios."},
                {"role": "user", "content": feedback_prompt}
            ],
            max_tokens=600,
            temperature=0.7
        )
        
        feedback_text = response.choices[0].message.content.strip()
        print(f"✅ Fallback LLM feedback received: {feedback_text[:100]}...")
        
        return {
            "overall_feedback": feedback_text,
            "metrics": {
                "total_turns": total_turns,
                "user_turns": len(user_messages),
                "manager_turns": len(manager_messages),
                "user_participation_ratio": user_participation_ratio,
                "total_user_words": total_user_words
            },
            "note": "Basic analysis (fallback mode)"
        }
        
    except Exception as e:
        print(f"❌ Fallback LLM feedback failed: {e}")
        return {
            "overall_feedback": "Thank you for practicing your workplace communication skills. Focus on clear expression of ideas, active listening, and maintaining a professional tone in your conversations.",
            "metrics": {
                "total_turns": total_turns,
                "user_turns": len(user_messages),
                "manager_turns": len(manager_messages),
                "user_participation_ratio": user_participation_ratio,
                "total_user_words": total_user_words
            },
            "note": "Minimal analysis due to processing limitations"
        }

# Add cleanup for old conversation history (optional)
async def cleanup_old_conversations():
    """Clean up conversation history older than 1 hour"""
    current_time = time.time()
    expired_clients = []
    for client_id, history in conversation_history.items():
        if current_time - history.get("start_time", 0) > 3600:  # 1 hour
            expired_clients.append(client_id)
    
    for client_id in expired_clients:
        del conversation_history[client_id]
        print(f"🧹 Cleaned up old conversation history for {client_id}")


async def _wait_for_processing_result(request_id: str, client_id: str, timeout: int = 30):
    """Wait for processing result with timeout"""
    start_time = asyncio.get_event_loop().time()
    
    while (asyncio.get_event_loop().time() - start_time) < timeout:
        if request_id in processing_results:
            result = processing_results.pop(request_id)
            if result["success"]:
                return result["transcript"]
            else:
                return None
        await asyncio.sleep(0.1)
    
    print(f"[{client_id}] ⚠️ Timeout waiting for processing result")
    return None

@app.get("/")
async def read_index():
    return FileResponse('static/index.html')

@app.get("/login")
async def read_login():
    return FileResponse("static/login.html")

# Serve signup page  
@app.get("/signup")
async def read_signup():
    return FileResponse("static/signup.html")

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "active_connections": len(manager.active_connections),
        "rabbitmq_connected": rabbitmq_connection is not None
    }


@app.get("/config")
async def get_config():
    return {
        "personalities": {k: {"name": v["name"], "title": v["title"], "description": v["description"]} 
                        for k, v in PERSONALITY_PROFILES.items()},
        "scenarios": {
            category: {
                key: {"name": data["name"], "context": data["context"]}
                for key, data in scenarios.items()
            }
            for category, scenarios in SCENARIO_CATEGORIES.items()
        },
        "voice_library": VOICE_LIBRARY
    }

# Include authentication routes
app.include_router(auth_routes.router)



# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# =====================
# Chatbot API Endpoints
# =====================
from fastapi import Request, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session as OrmSession
from core.database import get_db
import jwt as pyjwt
from datetime import datetime, timedelta
from utils.security_utils import hash_password, verify_password
from utils.auth_validators import EmailValidator, PasswordValidator, NameValidator, sanitize_input

# --- Chatbot Session Helpers ---
CHATBOT_JWT_SECRET = os.getenv("JWT_SECRET_KEY", os.getenv("FLASK_SECRET_KEY", "your-secret-key"))
CHATBOT_JWT_ALGORITHM = "HS256"
CHATBOT_JWT_EXPIRATION_HOURS = 24

def create_chatbot_token(chat_history=None, tone=None):
    payload = {
        'chat_history': chat_history or [],
        'tone': tone,
        'created_at': datetime.utcnow().isoformat(),
        'exp': datetime.utcnow() + timedelta(hours=CHATBOT_JWT_EXPIRATION_HOURS)
    }
    token = pyjwt.encode(payload, CHATBOT_JWT_SECRET, algorithm=CHATBOT_JWT_ALGORITHM)
    return token

def decode_chatbot_token(token: str):
    try:
        payload = pyjwt.decode(token, CHATBOT_JWT_SECRET, algorithms=[CHATBOT_JWT_ALGORITHM])
        return {
            'chat_history': payload.get('chat_history', []),
            'tone': payload.get('tone'),
            'valid': True
        }
    except pyjwt.ExpiredSignatureError:
        return {'chat_history': [], 'tone': None, 'valid': False, 'error': 'Token expired'}
    except pyjwt.InvalidTokenError as e:
        return {'chat_history': [], 'tone': None, 'valid': False, 'error': 'Invalid token'}

# --- Chatbot Logic (simplified, TODO: move to service) ---
def format_response(text: str) -> str:
    import re
    text = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', text)
    if '<br>' in text:
        text = re.sub(r'(<br>\s*){3,}', '<br><br>', text)
        return text
    if '\u2022' in text:
        lines = text.split('\u2022')
        intro = lines[0].strip()
        bullets = []
        for line in lines[1:]:
            line = line.strip()
            if line:
                bullets.append('\u2022 ' + line)
        if bullets:
            formatted_bullets = '<br>'.join(bullets)
            text = f"{intro}<br><br>{formatted_bullets}"
    text = re.sub(r'(\d+)\.\s+\*\*([^*]+)\*\*', r'\u2022 <b>\2</b>', text)
    text = re.sub(r'(\d+)\.\s+<b>([^<]+)</b>', r'\u2022 <b>\2</b>', text)
    return text



# --- Require JWT authentication for chatbot endpoints ---
from fastapi import Header, HTTPException, status, Depends

def get_current_user_from_token(authorization: str = Header(None), db: Session = Depends(database.get_db)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization header missing or invalid")
    token = authorization.replace("Bearer ", "")
    try:
        # Use the same logic as validate_websocket_token
        if is_blacklisted(token):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been revoked")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
        user = db.query(models.User).filter(models.User.user_id == user_id).first()
        if not user or user.trial_status != "active":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
        return user
    except JWTError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token: {str(e)}")

@app.post("/api/chat")
async def api_chat(request: Request, user=Depends(get_current_user_from_token)):
    data = await request.json()
    user_message = data.get('message', '').strip()
    incoming_token = data.get('token', '')
    if not user_message:
        return JSONResponse({'error': 'Message cannot be empty'}, status_code=400)
    # ...existing code for chat logic...
    # (Paste the previous chat logic here, unchanged)
    # ...existing code...

@app.get("/api/history")
async def api_history(request: Request, user=Depends(get_current_user_from_token)):
    token = request.headers.get('Authorization', '').replace('Bearer ', '') or request.query_params.get('token', '')
    if not token:
        return JSONResponse({'history': []})
    session_data = decode_chatbot_token(token)
    history = session_data['chat_history']
    return JSONResponse({'history': history})

@app.post("/api/clear")
async def api_clear(user=Depends(get_current_user_from_token)):
    new_token = create_chatbot_token([], None)
    return JSONResponse({
        'success': True,
        'message': 'Chat history cleared',
        'token': new_token
    })

# --- Chat History Endpoint ---
@app.get("/api/history")
async def api_history(request: Request):
    token = request.headers.get('Authorization', '').replace('Bearer ', '') or request.query_params.get('token', '')
    if not token:
        return JSONResponse({'history': []})
    session_data = decode_chatbot_token(token)
    history = session_data['chat_history']
    return JSONResponse({'history': history})

# --- Clear Chat History Endpoint ---
@app.post("/api/clear")
async def api_clear():
    new_token = create_chatbot_token([], None)
    return JSONResponse({
        'success': True,
        'message': 'Chat history cleared',
        'token': new_token
    })


# Serve HTML pages
@app.get("/")
async def root():
    return FileResponse("static/index.html")


@app.get("/login.html")
async def login_page():
    return FileResponse("static/login.html")


@app.get("/signup.html")
async def signup_page():
    return FileResponse("static/signup.html")


@app.get("/business-signup.html")
async def business_signup_page():
    return FileResponse("static/business-signup.html")


@app.get("/business-dashboard.html")
async def business_dashboard_page():
    return FileResponse("static/business-dashboard.html")


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    print(f"🚀 Starting FastAPI server on 0.0.0.0:{port}")
    uvicorn.run("server:app", host="0.0.0.0", port=port, log_level="info")