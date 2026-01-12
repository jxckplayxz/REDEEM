from flask import Flask, request, render_template_string
from flask_socketio import SocketIO, join_room, emit
import uuid

app = Flask(__name__)
app.config["SECRET_KEY"] = "vc"
socketio = SocketIO(app, cors_allowed_origins="*")

rooms = {}

HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Web Voice Chat</title>
<style>
body {
    margin:0;
    font-family: Arial, sans-serif;
    background:#0b0d13;
    color:white;
}
#app { display:flex; height:100vh; }
#sidebar {
    width:260px;
    background:#111827;
    padding:15px;
}
#main {
    flex:1;
    padding:20px;
}
input, button {
    width:100%;
    padding:10px;
    margin-top:8px;
    border-radius:6px;
    border:none;
}
button {
    background:#5865f2;
    color:white;
    cursor:pointer;
}
button:hover { opacity:.9; }
.room {
    background:#1f2937;
    padding:10px;
    border-radius:6px;
    margin-top:8px;
    cursor:pointer;
}
.hidden { display:none; }
#mute { background:#ef4444; }
</style>
</head>
<body>

<div id="app">
    <div id="sidebar">
        <h3>Create VC</h3>
        <input id="rname" placeholder="Room name">
        <label><input type="checkbox" id="public"> Public</label>
        <button onclick="createRoom()">Create</button>

        <h3 style="margin-top:20px">Public Rooms</h3>
        <div id="rooms"></div>
    </div>

    <div id="main">
        <h2 id="status">Not connected</h2>
        <button id="mute" class="hidden" onclick="toggleMute()">Mute</button>
    </div>
</div>

<script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>
<script>
const socket = io();
let pc, stream, currentRoom, muted=false;

async function createRoom(){
    const res = await fetch("/create",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({
            name:rname.value,
            public:public.checked
        })
    });
    const data = await res.json();
    joinRoom(data.id, data.code);
}

async function joinRoom(id, code=null){
    const res = await fetch("/join",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({room:id, code})
    });
    if(!res.ok){ alert("Join failed"); return; }

    currentRoom = id;
    status.innerText = "Connected to room: " + id;
    mute.classList.remove("hidden");

    socket.emit("join", {room:id});
    startVoice();
}

async function startVoice(){
    stream = await navigator.mediaDevices.getUserMedia({audio:true});
    pc = new RTCPeerConnection({
        iceServers:[{urls:"stun:stun.l.google.com:19302"}]
    });

    stream.getTracks().forEach(t=>pc.addTrack(t,stream));

    pc.ontrack = e=>{
        const a=document.createElement("audio");
        a.srcObject=e.streams[0];
        a.autoplay=true;
    };

    pc.onicecandidate = e=>{
        if(e.candidate){
            socket.emit("ice",{room:currentRoom,c:e.candidate});
        }
    };

    const offer = await pc.createOffer();
    await pc.setLocalDescription(offer);
    socket.emit("offer",{room:currentRoom,sdp:offer});
}

function toggleMute(){
    muted=!muted;
    stream.getAudioTracks()[0].enabled=!muted;
    mute.innerText = muted ? "Unmute" : "Mute";
}

socket.on("offer",async d=>{
    if(!pc) await startVoice();
    await pc.setRemoteDescription(d.sdp);
    const ans = await pc.createAnswer();
    await pc.setLocalDescription(ans);
    socket.emit("answer",{room:currentRoom,sdp:ans});
});

socket.on("answer",d=>pc.setRemoteDescription(d.sdp));
socket.on("ice",d=>pc.addIceCandidate(d.c));

async function loadRooms(){
    const r = await fetch("/rooms");
    const data = await r.json();
    rooms.innerHTML="";
    Object.entries(data).forEach(([id,r])=>{
        const div=document.createElement("div");
        div.className="room";
        div.innerText=r.name;
        div.onclick=()=>joinRoom(id);
        rooms.appendChild(div);
    });
}
loadRooms();
</script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/create", methods=["POST"])
def create():
    d=request.json
    rid=str(uuid.uuid4())[:8]
    rooms[rid]={
        "name":d["name"],
        "public":d["public"],
        "code":str(uuid.uuid4())[:6] if not d["public"] else None
    }
    return {"id":rid,"code":rooms[rid]["code"]}

@app.route("/rooms")
def public_rooms():
    return {k:v for k,v in rooms.items() if v["public"]}

@app.route("/join", methods=["POST"])
def join():
    d=request.json
    r=rooms.get(d["room"])
    if not r: return {},404
    if not r["public"] and d.get("code")!=r["code"]:
        return {},403
    return {"ok":True}

@socketio.on("join")
def on_join(d):
    join_room(d["room"])

@socketio.on("offer")
def offer(d):
    emit("offer",d,room=d["room"],include_self=False)

@socketio.on("answer")
def answer(d):
    emit("answer",d,room=d["room"],include_self=False)

@socketio.on("ice")
def ice(d):
    emit("ice",d,room=d["room"],include_self=False)

socketio.run(app, host="0.0.0.0", port=5060)