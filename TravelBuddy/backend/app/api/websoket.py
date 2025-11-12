from fastapi import WebSocket, WebSocketDisconnect
import json
import logging
from typing import Dict, Set
import base64
import asyncio

logger = logging.getLogger(_name_)


class ConnectionManager:
    """Manages WebSocket connections"""

    def _init_(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_sessions: Dict[str, Set[str]] = {}

    async def connect(self, websocket: WebSocket, user_id: str, session_id: str):
        """Accept new WebSocket connection"""
        await websocket.accept()
        self.active_connections[session_id] = websocket

        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = set()
        self.user_sessions[user_id].add(session_id)

        logger.info(f"User {user_id} connected (session: {session_id})")

    def disconnect(self, user_id: str, session_id: str):
        """Remove WebSocket connection"""
        if session_id in self.active_connections:
            del self.active_connections[session_id]

        if user_id in self.user_sessions:
            self.user_sessions[user_id].discard(session_id)
            if not self.user_sessions[user_id]:
                del self.user_sessions[user_id]

        logger.info(f"User {user_id} disconnected (session: {session_id})")

    async def send_personal_message(self, message: Dict, session_id: str):
        """Send message to a specific session"""
        if session_id in self.active_connections:
            websocket = self.active_connections[session_id]
            await websocket.send_json(message)

    async def broadcast_to_user(self, message: Dict, user_id: str):
        """Broadcast message to all sessions of a user"""
        if user_id in self.user_sessions:
            for session_id in self.user_sessions[user_id]:
                await self.send_personal_message(message, session_id)


manager = ConnectionManager()


async def handle_websocket_message(websocket: WebSocket, user_id: str, session_id: str, data: Dict):
    """Handle incoming WebSocket messages (text + voice)"""
    message_type = data.get("type")

    try:
        # Import here to avoid circular imports
        from app.main import (
            travel_agent,
            streaming_voice_service,
            voice_service
        )

        # ----------------------------
        # 🎤 1. Start recording
        # ----------------------------
        if message_type == "start_recording":
            if streaming_voice_service:
                await streaming_voice_service.start_recording()
                await manager.send_personal_message({
                    "type": "info",
                    "message": "Recording started"
                }, session_id)
            return

        # ----------------------------
        # 🎧 2. Process audio chunks
        # ----------------------------
        elif message_type == "audio_chunk":
            if streaming_voice_service:
                chunk_bytes = base64.b64decode(data["audio"])
                await streaming_voice_service.process_audio_chunk(chunk_bytes)
            return

        # ----------------------------
        # 🛑 3. Stop recording and process audio
        # ----------------------------
        elif message_type == "stop_recording":
            if streaming_voice_service:
                transcription = await streaming_voice_service.stop_recording()

                # Send transcription back to frontend
                await manager.send_personal_message({
                    "type": "transcription",
                    "text": transcription
                }, session_id)

                # Run main travel agent query
                response = travel_agent.process_query(
                    user_message=transcription,
                    user_id=user_id,
                    context={}
                )

                # Send textual response
                await manager.send_personal_message({
                    "type": "response",
                    "data": response
                }, session_id)

                # 🗣 Optional: Generate TTS voice reply
                try:
                    from pathlib import Path
                    temp_audio_path = Path("temp_reply.mp3")
                    voice_service.synthesize_speech(response["message"], temp_audio_path)
                    audio_b64 = base64.b64encode(temp_audio_path.read_bytes()).decode("utf-8")

                    await manager.send_personal_message({
                        "type": "audio_response",
                        "audio": audio_b64
                    }, session_id)
                except Exception as e:
                    logger.warning(f"TTS generation failed: {e}")
            return

        # ----------------------------
        # 💬 4. Regular chat message
        # ----------------------------
        elif message_type == "chat":
            response = travel_agent.process_query(
                user_message=data.get("message"),
                user_id=user_id,
                context=data.get("context")
            )
            await manager.send_personal_message({
                "type": "chat_response",
                "data": response
            }, session_id)
            return

        # ----------------------------
        # ✍ 5. Typing indicator
        # ----------------------------
        elif message_type == "typing":
            await manager.broadcast_to_user({
                "type": "typing",
                "user_id": user_id
            }, user_id)
            return

        # ----------------------------
        # 🕒 6. Ping / Pong heartbeat
        # ----------------------------
        elif message_type == "ping":
            await manager.send_personal_message({
                "type": "pong",
                "timestamp": data.get("timestamp")
            }, session_id)
            return

        # ----------------------------
        # ⚠ Unknown message
        # ----------------------------
        else:
            logger.warning(f"Unknown message type: {message_type}")
            await manager.send_personal_message({
                "type": "error",
                "message": f"Unknown message type: {message_type}"
            }, session_id)

    except Exception as e:
        logger.exception(f"Error handling WebSocket message: {e}")
        await manager.send_personal_message({
            "type": "error",
            "message": str(e)
        }, session_id)
