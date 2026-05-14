# Meeting routes — WebRTC signaling, meeting management, minutes generation
# POST /meetings/              — create meeting
# GET  /meetings/              — list meetings
# GET  /meetings/{room_code}   — get meeting by room code
# POST /meetings/{id}/end      — end meeting and trigger minutes
# GET  /meetings/{id}/minutes  — get generated minutes
# WS   /meetings/ws/{room_code}/{user_id} — WebRTC signaling

import os
import uuid
import json
import asyncio
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi import UploadFile, File
import tempfile
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from models.meeting import Meeting, MeetingParticipant
from schemas.meeting import MeetingCreate, MeetingResponse, MinutesResponse
from auth.dependencies import get_current_user
from services.audit_services import log_action
from groq import Groq
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

router = APIRouter(prefix="/meetings", tags=["Meetings"])
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# ── WebRTC Connection Manager ─────────────────────────────────────────────
class MeetingConnectionManager:
    def __init__(self):
        # room_code -> {user_id: websocket}
        self.rooms: dict = {}

    async def connect(self, room_code: str, user_id: int,
                      websocket: WebSocket):
        await websocket.accept()
        if room_code not in self.rooms:
            self.rooms[room_code] = {}
        self.rooms[room_code][user_id] = websocket
        print(f"[MEETING] User {user_id} joined room {room_code}")

    def disconnect(self, room_code: str, user_id: int):
        if room_code in self.rooms:
            self.rooms[room_code].pop(user_id, None)
            if not self.rooms[room_code]:
                del self.rooms[room_code]

    async def send_to_user(self, room_code: str, user_id: int,
                           message: dict):
        if room_code in self.rooms and user_id in self.rooms[room_code]:
            ws = self.rooms[room_code][user_id]
            await ws.send_text(json.dumps(message))

    async def broadcast_to_room(self, room_code: str, message: dict,
                                exclude_user: int = None):
        if room_code in self.rooms:
            for uid, ws in self.rooms[room_code].items():
                if uid != exclude_user:
                    try:
                        await ws.send_text(json.dumps(message))
                    except:
                        pass

    def get_participants(self, room_code: str) -> list:
        if room_code in self.rooms:
            return list(self.rooms[room_code].keys())
        return []


manager = MeetingConnectionManager()


# ── REST Endpoints ────────────────────────────────────────────────────────

@router.post("/", response_model=MeetingResponse)
def create_meeting(
    data: MeetingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    room_code = str(uuid.uuid4())[:8].upper()
    meeting = Meeting(
        title=data.title,
        room_code=room_code,
        created_by=current_user.id,
        status="waiting"
    )
    db.add(meeting)
    db.commit()
    db.refresh(meeting)

    log_action(db=db, action="meeting.create", user_id=current_user.id,
               resource_type="meeting", resource_id=meeting.id,
               details={"title": data.title, "room_code": room_code})
    return meeting


@router.get("/", response_model=list[MeetingResponse])
def list_meetings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Meeting).order_by(
        Meeting.created_at.desc()).limit(20).all()


@router.get("/{room_code}", response_model=MeetingResponse)
def get_meeting(
    room_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    meeting = db.query(Meeting).filter(
        Meeting.room_code == room_code).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return meeting


@router.post("/{meeting_id}/end")
def end_meeting(
    meeting_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    meeting.status = "ended"
    meeting.ended_at = datetime.now(timezone.utc)
    db.commit()

    # Trigger minutes generation if transcript exists
    if meeting.transcript:
        _generate_minutes(meeting_id, db)

    log_action(db=db, action="meeting.end", user_id=current_user.id,
               resource_type="meeting", resource_id=meeting_id)
    return {"message": "Meeting ended", "meeting_id": meeting_id}


@router.post("/{meeting_id}/transcript")
def save_transcript(
    meeting_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Save transcript chunk from frontend Whisper transcription"""
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    existing = meeting.transcript or ""
    meeting.transcript = existing + "\n" + payload.get("text", "")
    db.commit()
    return {"message": "Transcript updated"}

"""
@router.post("/{meeting_id}/transcript")
async def save_transcript(
    meeting_id: int,
    text: str = None,
    audio: UploadFile = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ......
    Save transcript from:
    1. direct text
    2. audio file -> Groq Whisper transcription
    ......

    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()

    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    final_text = text

    # ── AUDIO → GROQ WHISPER ─────────────────────────────
    if audio:

        # Save temporary audio file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
            tmp.write(await audio.read())
            tmp_path = tmp.name

        # Send to Groq Whisper
        with open(tmp_path, "rb") as audio_file:

            whisper_response = groq_client.audio.transcriptions.create(
                file=audio_file,
                model="whisper-large-v3"
            )

        final_text = whisper_response.text

        # Remove temp file
        os.remove(tmp_path)

    # ── SAVE TRANSCRIPT ─────────────────────────────────
    if final_text:

        existing = meeting.transcript or ""

        meeting.transcript = (
            existing + "\n" + final_text
        )

        db.commit()

    return {
        "message": "Transcript updated",
        "text": final_text
    }
"""
@router.get("/{meeting_id}/minutes", response_model=MinutesResponse)
def get_minutes(
    meeting_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return MinutesResponse(
        meeting_id=meeting.id,
        title=meeting.title,
        transcript=meeting.transcript,
        minutes=meeting.minutes,
        minutes_pdf_path=meeting.minutes_pdf_path
    )


@router.post("/{meeting_id}/generate-minutes")
def generate_minutes_endpoint(
    meeting_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Manually trigger minutes generation."""
    result = _generate_minutes(meeting_id, db)
    return result


# ── Minutes Generation ────────────────────────────────────────────────────

def _generate_minutes(meeting_id: int, db: Session) -> dict:
    """Uses Groq AI to generate structured minutes from transcript."""
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting or not meeting.transcript:
        return {"error": "No transcript available"}

    participants = db.query(MeetingParticipant).filter(
        MeetingParticipant.meeting_id == meeting_id
    ).all()
    participant_names = [p.user.full_name for p in participants if p.user]

    prompt = f"""You are a professional meeting secretary. Generate structured meeting minutes from this transcript.

Meeting Title: {meeting.title}
Date: {meeting.created_at.strftime('%d %B %Y') if meeting.created_at else 'Unknown'}
Participants: {', '.join(participant_names) if participant_names else 'Unknown'}

Transcript:
{meeting.transcript}

Generate minutes in this exact format:
MEETING MINUTES

Title: {meeting.title}
Date: [date]
Duration: [estimated duration]
Participants: [list]

1. AGENDA ITEMS DISCUSSED
[bullet points of main topics]

2. KEY DECISIONS MADE
[bullet points of decisions]

3. ACTION ITEMS
[bullet points with responsible person and deadline if mentioned]

4. NEXT STEPS
[bullet points]

5. SUMMARY
[2-3 sentence summary]"""

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=1500
        )
        minutes_text = response.choices[0].message.content

        # Save minutes to DB
        meeting.minutes = minutes_text
        db.commit()

        # Generate PDF
        pdf_path = _generate_minutes_pdf(meeting, minutes_text, db)
        meeting.minutes_pdf_path = pdf_path
        db.commit()

        return {
            "message": "Minutes generated successfully",
            "minutes": minutes_text,
            "pdf_path": pdf_path
        }
    except Exception as e:
        print(f"[MINUTES ERROR] {e}")
        return {"error": str(e)}


def _generate_minutes_pdf(meeting: Meeting, minutes_text: str,
                           db: Session) -> str:
    """Generates a PDF of the meeting minutes using ReportLab."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.platypus import (SimpleDocTemplate, Paragraph,
                                     Spacer, HRFlowable)
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    import os

    os.makedirs("meeting_minutes", exist_ok=True)
    filename = f"meeting_minutes/minutes_{meeting.id}_{meeting.room_code}.pdf"

    doc = SimpleDocTemplate(filename, pagesize=A4,
                            rightMargin=2*cm, leftMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)

    NAVY = colors.HexColor('#0A0E1A')
    CYAN = colors.HexColor('#00B8D9')
    MUTED = colors.HexColor('#6B778C')

    story = []

    # Header
    story.append(Paragraph("⚡ AUDITSYS", ParagraphStyle('h',
        fontSize=22, fontName='Helvetica-Bold', textColor=CYAN,
        alignment=TA_CENTER)))
    story.append(Paragraph("MEETING MINUTES", ParagraphStyle('s',
        fontSize=13, fontName='Helvetica-Bold', textColor=NAVY,
        alignment=TA_CENTER, spaceAfter=6)))
    story.append(HRFlowable(width="100%", thickness=1.5, color=NAVY,
                             spaceAfter=16))

    # Meta
    story.append(Paragraph(f"<b>Meeting:</b> {meeting.title}",
        ParagraphStyle('m', fontSize=10, fontName='Helvetica',
                       textColor=colors.HexColor('#2D3748'), spaceAfter=4)))
    story.append(Paragraph(
        f"<b>Room Code:</b> {meeting.room_code}",
        ParagraphStyle('m2', fontSize=10, fontName='Helvetica',
                       textColor=colors.HexColor('#2D3748'), spaceAfter=4)))
    if meeting.ended_at:
        story.append(Paragraph(
            f"<b>Date:</b> {meeting.created_at.strftime('%d %B %Y %H:%M')}",
            ParagraphStyle('m3', fontSize=10, fontName='Helvetica',
                           textColor=colors.HexColor('#2D3748'), spaceAfter=4)))
    story.append(HRFlowable(width="100%", thickness=0.5,
                             color=colors.HexColor('#DFE1E6'),
                             spaceAfter=12, spaceBefore=8))

    # Minutes content
    for line in minutes_text.split('\n'):
        line = line.strip()
        if not line:
            story.append(Spacer(1, 0.2*cm))
            continue
        if line.startswith('#') or line.isupper():
            story.append(Paragraph(line.replace('#', '').strip(),
                ParagraphStyle('sec', fontSize=11, fontName='Helvetica-Bold',
                               textColor=NAVY, spaceBefore=10, spaceAfter=4)))
        elif line.startswith('-') or line.startswith('•'):
            story.append(Paragraph(f"  {line}",
                ParagraphStyle('b', fontSize=9.5, fontName='Helvetica',
                               textColor=colors.HexColor('#2D3748'),
                               leftIndent=12, spaceAfter=3, leading=14)))
        else:
            story.append(Paragraph(line,
                ParagraphStyle('body', fontSize=9.5, fontName='Helvetica',
                               textColor=colors.HexColor('#2D3748'),
                               spaceAfter=4, leading=14)))

    story.append(HRFlowable(width="100%", thickness=1, color=NAVY,
                             spaceBefore=16, spaceAfter=8))
    story.append(Paragraph(
        f"Generated by AuditSys  ·  {datetime.now().strftime('%d %B %Y %H:%M')}  ·  CONFIDENTIAL",
        ParagraphStyle('ft', fontSize=7.5, fontName='Helvetica',
                       textColor=MUTED, alignment=TA_CENTER)))

    doc.build(story)
    print(f"[MINUTES PDF] Saved to {filename}")
    return filename


# ── WebSocket Signaling ───────────────────────────────────────────────────

@router.websocket("/ws/{room_code}/{user_id}")
async def meeting_websocket(
    websocket: WebSocket,
    room_code: str,
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    WebRTC signaling server via WebSocket.
    Handles: join, offer, answer, ice-candidate, leave, chat
    """
    await manager.connect(room_code, user_id, websocket)

    # Get user name
    user = db.query(User).filter(User.id == user_id).first()
    user_name = user.full_name if user else f"User {user_id}"

    # Save participant to DB
    meeting = db.query(Meeting).filter(
        Meeting.room_code == room_code).first()
    if meeting:
        if meeting.status == "waiting":
            meeting.status = "active"
            meeting.started_at = datetime.now(timezone.utc)
            db.commit()

        participant = MeetingParticipant(
            meeting_id=meeting.id, user_id=user_id)
        db.add(participant)
        db.commit()

    # Notify others that user joined
    await manager.broadcast_to_room(room_code, {
        "type": "user_joined",
        "user_id": user_id,
        "user_name": user_name,
        "participants": manager.get_participants(room_code)
    }, exclude_user=user_id)

    # Send current participants to the new user
    await manager.send_to_user(room_code, user_id, {
        "type": "room_info",
        "participants": manager.get_participants(room_code),
        "user_id": user_id,
        "user_name": user_name
    })

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            msg_type = message.get("type")

            if msg_type == "offer":
                # Forward WebRTC offer to target peer
                await manager.send_to_user(
                    room_code,
                    message["target_user_id"],
                    {"type": "offer", "sdp": message["sdp"],
                     "from_user_id": user_id,
                     "from_user_name": user_name}
                )

            elif msg_type == "answer":
                # Forward WebRTC answer to target peer
                await manager.send_to_user(
                    room_code,
                    message["target_user_id"],
                    {"type": "answer", "sdp": message["sdp"],
                     "from_user_id": user_id}
                )

            elif msg_type == "ice_candidate":
                # Forward ICE candidate to target peer
                await manager.send_to_user(
                    room_code,
                    message["target_user_id"],
                    {"type": "ice_candidate",
                     "candidate": message["candidate"],
                     "from_user_id": user_id}
                )

            elif msg_type == "chat":
                # Broadcast chat message to all in room
                await manager.broadcast_to_room(room_code, {
                    "type": "chat",
                    "user_id": user_id,
                    "user_name": user_name,
                    "message": message.get("message", ""),
                    "timestamp": datetime.now().strftime('%H:%M')
                })

            elif msg_type == "mute_toggle":
                await manager.broadcast_to_room(room_code, {
                    "type": "mute_toggle",
                    "user_id": user_id,
                    "muted": message.get("muted", True)
                }, exclude_user=user_id)

            elif msg_type == "camera_toggle":
                await manager.broadcast_to_room(room_code, {
                    "type": "camera_toggle",
                    "user_id": user_id,
                    "camera_off": message.get("camera_off", True)
                }, exclude_user=user_id)
            
            elif msg_type == "meeting_ended":
                # Broadcast to all participants that meeting has ended
                await manager.broadcast_to_room(room_code, {
                    "type": "meeting_ended"
                }, exclude_user=user_id)

    except WebSocketDisconnect:
        manager.disconnect(room_code, user_id)

        # Update participant left_at
        if meeting:
            p = db.query(MeetingParticipant).filter(
                MeetingParticipant.meeting_id == meeting.id,
                MeetingParticipant.user_id == user_id
            ).first()
            if p:
                p.left_at = datetime.now(timezone.utc)
                db.commit()

        await manager.broadcast_to_room(room_code, {
            "type": "user_left",
            "user_id": user_id,
            "user_name": user_name,
            "participants": manager.get_participants(room_code)
        })
        print(f"[MEETING] User {user_id} left room {room_code}")






