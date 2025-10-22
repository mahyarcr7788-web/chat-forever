
const socket = io();
let currentRoom = "global";

function scrollChatToBottom() {
    const chatBox = document.getElementById("chatBox");
    chatBox.scrollTop = chatBox.scrollHeight;
}

function addMessage(msg) {
    const chatBox = document.getElementById("chatBox");
    const div = document.createElement("div");
    if(msg.user && msg.text) {
        div.innerHTML = `<b>${msg.user}:</b> ${msg.text}`;
    } else {
        div.innerHTML = `<i>${msg}</i>`;
    }
    chatBox.appendChild(div);
    scrollChatToBottom();
}

function joinRoom(room) {
    if (currentRoom) {
        socket.emit("leave", { room: currentRoom });
    }
    currentRoom = room;
    socket.emit("join", { room: currentRoom });
    document.getElementById("chatBox").innerHTML = "";
}

document.getElementById("sendBtn").addEventListener("click", () => {
    const messageInput = document.getElementById("messageInput");
    const message = messageInput.value.trim();
    if (!message) return;
    socket.emit("message", { room: currentRoom, message: message });
    messageInput.value = "";
});

document.getElementById("messageInput").addEventListener("keypress", (e) => {
    if (e.key === "Enter") {
        document.getElementById("sendBtn").click();
    }
});

socket.on("connect", () => {
    joinRoom("global");
});

socket.on("chat_history", (messages) => {
    const chatBox = document.getElementById("chatBox");
    chatBox.innerHTML = "";
    messages.forEach(msg => addMessage(msg));
});

socket.on("message", (msg) => {
    addMessage(msg);
});

socket.on("status", (msg) => {
    addMessage(msg);
});

document.getElementById("logoutBtn").addEventListener("click", () => {
    window.location.href = "/logout";
});

// Private room panel toggle
const privateRoomPanel = document.getElementById("privateRoomPanel");
const toggleBtn = document.getElementById("togglePrivateRooms");
toggleBtn.addEventListener("click", () => {
    if (privateRoomPanel.style.display === "block") {
        privateRoomPanel.style.display = "none";
    } else {
        privateRoomPanel.style.display = "block";
    }
});

// Create room
document.getElementById("createRoomBtn").addEventListener("click", async () => {
    const name = document.getElementById("createRoomName").value.trim();
    const password = document.getElementById("createRoomPassword").value.trim();
    const errorDiv = document.getElementById("privateRoomError");
    errorDiv.textContent = "";
    if (!name || !password) {
        errorDiv.textContent = "Room name and password are required to create.";
        return;
    }
    try {
        const res = await fetch("/create_room", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ room_name: name, password: password })
        });
        const data = await res.json();
        if (data.error) {
            errorDiv.textContent = data.error;
            return;
        }
        joinRoom(name);
        errorDiv.textContent = "";
    } catch(e) {
        errorDiv.textContent = "Error creating room.";
    }
});

// Join room
document.getElementById("joinRoomBtn").addEventListener("click", async () => {
    const name = document.getElementById("joinRoomName").value.trim();
    const password = document.getElementById("joinRoomPassword").value.trim();
    const errorDiv = document.getElementById("privateRoomError");
    errorDiv.textContent = "";
    if (!name || !password) {
        errorDiv.textContent = "Room name and password are required to join.";
        return;
    }
    try {
        const res = await fetch("/join_room", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ room_name: name, password: password })
        });
        const data = await res.json();
        if (data.error) {
            errorDiv.textContent = data.error;
            return;
        }
        joinRoom(name);
        errorDiv.textContent = "";
    } catch(e) {
        errorDiv.textContent = "Error joining room.";
    }
});
