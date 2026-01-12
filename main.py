from flask import Flask, request, render_template_string
from flask_socketio import SocketIO, join_room, emit
import uuid, random

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

rooms = {}
users = {}

NAMES = [
    "Tiger","Wolf","Fox","Bear","Eagle","Raven","Shark","Panda",
    "Lion","Dragon","Falcon","Cobra","Panther"
]

HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Web VC</title>
<style>
body{margin:0;background:#0b0d13;color:white;font-family:Arial}
#app{display:flex;height:100vh}
#left{width:300px;background:#111827;padding:15px}
#center{flex:1;padding:20px}
#right{width:260px;background:#111827;padding:15px}

input,button{
 width:100%;padding:10px;margin-top:8px;
 border:none;border-radius:6px
}
button{background:#5865f2;color:white;cursor:pointer}
button:hover{opacity:.9}

.room,.user{
 background:#1f2937;
 padding:10px;
 border-radius:6px;
 margin-top:8px;
 cursor:pointer
}

#mute{background:#ef4444}
h3{margin-top:0}
</style>
</head>
<body>

<div id="app">
<div id="left">
<h3>Create Room</h3>
<input id="rname" placeholder="Room name">
<label><input type="checkbox" id="public"> Public</label>
<button onclick="createRoom()">Create</button>

<h3 style="margin-top:20px">Public Rooms</h3>
<div id="rooms"></div>
</div>

<div id="center">
<h2 id="status">Not connected</h2>
<button id="mute" style="display:none" onclick="toggleMute()">Mute</button>
</div>

<div id="right">
<h3>People</h3>
<div id="users"></div>
</div>
</div>

<script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>
<script>
const socket = io();
let localStream;
let peers = {};
let myId = Math.random().toString(36).slice(2);
let myName = "Anon " + ["Tiger","Wolf","Fox","Bear","Eagle","Raven","Shark","Panda"][Math.floor(Math.random()*8)];
let currentRoom;
let muted=false;

async function createRoom(){
 const r = await fetch("/create",{
  method:"POST",
  headers:{"Content-Type":"application/json"},
  body:JSON.stringify({name:rname.value,public:public.checked})
 });
 const d = await r.json();
 joinRoom(d.id,d.code);
}

async function joinRoom(id,code=null){
 const r = await fetch("/join",{
  method:"POST",
  headers:{"Content-Type":"application/json"},
  body:JSON.stringify({room:id,code})
 });
 if(!r.ok){alert("Join failed");return;}

 currentRoom=id;
 status.innerText="Connected to "+id;
 mute.style.display="block";

 localStream = await navigator.mediaDevices.getUserMedia({audio:true});
 socket.emit("join",{room:id,id:myId,name:myName});
}

function createPeer(pid,offerer){
 const pc = new RTCPeerConnection({
  iceServers:[{urls:"stun:stun.l.google.com:19302"}]
 });

 localStream.getTracks().forEach(t=>pc.addTrack(t,localStream));

 pc.ontrack=e=>{
  const a=document.createElement("audio");
  a.srcObject=e.streams[0];
  a.autoplay=true;
 };

 pc.onicecandidate=e=>{
  if(e.candidate){
   socket.emit("ice",{to:pid,from:myId,c:e.candidate});
  }
 };

 if(offerer){
  pc.createOffer().then(o=>{
   pc.setLocalDescription(o);
   socket.emit("offer",{to:pid,from:myId,sdp:o});
  });
 }

 peers[pid]=pc;
}

function toggleMute(){
 muted=!muted;
 localStream.getAudioTracks()[0].enabled=!muted;
 mute.innerText=muted?"Unmute":"Mute";
}

socket.on("users",list=>{
 users.innerHTML="";
 list.forEach(u=>{
  const d=document.createElement("div");
  d.className="user";
  d.innerText=u.name;
  users.appendChild(d);
 });
});

socket.on("new-user",d=>{
 createPeer(d.id,true);
});

socket.on("offer",async d=>{
 const pc=createPeer(d.from,false);
 await pc.setRemoteDescription(d.sdp);
 const ans=await pc.createAnswer();
 await pc.setLocalDescription(ans);
 socket.emit("answer",{to:d.from,from:myId,sdp:ans});
});

socket.on("answer",d=>{
 peers[d.from].setRemoteDescription(d.sdp);
});

socket.on("ice",d=>{
 peers[d.from]?.addIceCandidate(d.c);
});

async function loadRooms(){
 const r=await fetch("/rooms");
 const data=await r.json();
 rooms.innerHTML="";
 Object.entries(data).forEach(([id,r])=>{
  const d=document.createElement("div");
  d.className="room";
  d.innerText=r.name;
  d.onclick=()=>joinRoom(id);
  rooms.appendChild(d);
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
def join_evt(d):
    join_room(d["room"])
    users[d["id"]]={"name":d["name"],"room":d["room"]}
    emit("users",[v for v in users.values() if v["room"]==d["room"]],room=d["room"])
    emit("new-user",d,room=d["room"],include_self=False)

@socketio.on("offer")
def offer(d): emit("offer",d,to=d["to"])

@socketio.on("answer")
def answer(d): emit("answer",d,to=d["to"])

@socketio.on("ice")
def ice(d): emit("ice",d,to=d["to"])

socketio.run(app,host="0.0.0.0",port=5000)