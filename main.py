from flask import Flask, render_template_string, request
from flask_socketio import SocketIO, join_room, emit
import uuid

app = Flask(__name__)
app.config["SECRET_KEY"] = "vc-secret"
socketio = SocketIO(app, cors_allowed_origins="*")

rooms = {}

HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Web VC</title>
<style>
body { background:#0f0f14; color:white; font-family:Arial; }
button, input { padding:10px; margin:5px; border:none; border-radius:6px; }
button { background:#5865f2; color:white; cursor:pointer; }
.card { background:#1c1c28; padding:15px; border-radius:8px; margin:10px; }
</style>
</head>
<body>

<h2>Create Server</h2>
<input id="name" placeholder="Server name">
<label><input type="checkbox" id="public"> Public</label>
<button onclick="create()">Create</button>

<h2>Public Servers</h2>
<div id="servers"></div>

<h2 id="roomTitle"></h2>
<button onclick="toggleMute()">Mute / Unmute</button>

<script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>
<script>
const socket = io();
let pc;
let stream;
let muted = false;
let currentRoom = null;

async function create(){
    const res = await fetch("/create", {
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({
            name: name.value,
            public: public.checked
        })
    });
    const data = await res.json();
    join(data.room_id, data.code);
}

async function join(id, code=null){
    const res = await fetch("/join", {
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({room:id, code})
    });
    if(!res.ok){ alert("Join failed"); return; }

    currentRoom = id;
    roomTitle.innerText = "Room: " + id;
    startVC();
}

async function startVC(){
    stream = await navigator.mediaDevices.getUserMedia({audio:true});
    pc = new RTCPeerConnection();

    stream.getTracks().forEach(t=>pc.addTrack(t,stream));

    pc.ontrack = e=>{
        const a=document.createElement("audio");
        a.srcObject=e.streams[0];
        a.autoplay=true;
    };

    pc.onicecandidate = e=>{
        if(e.candidate){
            socket.emit("ice",{room:currentRoom,candidate:e.candidate});
        }
    };

    const offer = await pc.createOffer();
    await pc.setLocalDescription(offer);
    socket.emit("offer",{room:currentRoom,offer});
}

function toggleMute(){
    muted=!muted;
    stream.getAudioTracks()[0].enabled=!muted;
}

socket.on("offer",async d=>{
    if(!pc) startVC();
    await pc.setRemoteDescription(d.offer);
    const ans=await pc.createAnswer();
    await pc.setLocalDescription(ans);
    socket.emit("answer",{room:currentRoom,answer:ans});
});

socket.on("answer",d=>pc.setRemoteDescription(d.answer));
socket.on("ice",d=>pc.addIceCandidate(d.candidate));

async function load(){
    const res=await fetch("/rooms");
    const data=await res.json();
    servers.innerHTML="";
    Object.entries(data).forEach(([id,r])=>{
        const div=document.createElement("div");
        div.className="card";
        div.innerHTML=`<b>${r.name}</b><br><button onclick="join('${id}')">Join</button>`;
        servers.appendChild(div);
    });
}
load();
</script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/create", methods=["POST"])
def create():
    data=request.json
    rid=str(uuid.uuid4())[:8]
    rooms[rid]={
        "name":data["name"],
        "public":data["public"],
        "code":str(uuid.uuid4())[:6] if not data["public"] else None
    }
    return {"room_id":rid,"code":rooms[rid]["code"]}

@app.route("/rooms")
def public_rooms():
    return {k:v for k,v in rooms.items() if v["public"]}

@app.route("/join", methods=["POST"])
def join():
    d=request.json
    r=rooms.get(d["room"])
    if not r: return {"error":"404"},404
    if not r["public"] and d.get("code")!=r["code"]:
        return {"error":"403"},403
    return {"ok":True}

@socketio.on("offer")
def offer(d):
    join_room(d["room"])
    emit("offer",d,room=d["room"],include_self=False)

@socketio.on("answer")
def answer(d):
    emit("answer",d,room=d["room"],include_self=False)

@socketio.on("ice")
def ice(d):
    emit("ice",d,room=d["room"],include_self=False)

socketio.run(app, host="0.0.0.0", port=5008)