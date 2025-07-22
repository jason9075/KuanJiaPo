document.addEventListener("DOMContentLoaded", () => {
    const liveSection = document.getElementById("live-section");
    const historySection = document.getElementById("history-section");
    const navLive = document.getElementById("nav-live");
    const navHistory = document.getElementById("nav-history");
    const eventList = document.getElementById("event-list");
    const liveImage = document.getElementById("live-image");
    const callBtn = document.getElementById("call-btn");
    const remoteAudio = document.getElementById("remote-audio");
    const params = new URLSearchParams(window.location.search);
    const autoCall = ["1", "true"].includes(params.get("autocall"));

    let ws;
    let pc;
    let localStream;
    let isCalling = false;

    let currentPage = 0;
    const pageSize = 30;
    let loading = false;
    let allDataLoaded = false;

    function updateLiveImage() {
        liveImage.src = "/static/screenshot/frame.jpg?" + new Date().getTime(); // Add timestamp to prevent caching
    }

    // Update live image at regular intervals
    setInterval(updateLiveImage, 1000); // Update every second

    // Navigation logic
    navLive.addEventListener("click", () => {
        liveSection.style.display = "block";
        historySection.style.display = "none";
        navLive.classList.add("active");
        navHistory.classList.remove("active");
    });

    navHistory.addEventListener("click", async () => {
        liveSection.style.display = "none";
        historySection.style.display = "block";
        navLive.classList.remove("active");
        navHistory.classList.add("active");

        // Load the first batch of events
        currentPage = 0;
        allDataLoaded = false;
        eventList.innerHTML = "";
        await loadEvents();
    });

    // Helper function to calculate time difference
    function timeAgo(timestamp) {
        const eventTime = new Date(timestamp);
        const now = new Date();
        const diffMs = now - eventTime;
        const diffMinutes = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMinutes / 60);
        const diffDays = Math.floor(diffHours / 24);

        if (diffDays > 0) return `${diffDays} days ago`;
        if (diffHours > 0) return `${diffHours} hours ago`;
        if (diffMinutes > 0) return `${diffMinutes} mins ago`;
        return "just now";
    }

    // Function to load events with pagination
    async function loadEvents() {
        if (loading || allDataLoaded) return;
        loading = true;

        const response = await fetch(
            `/api/events?page=${currentPage}&size=${pageSize}`,
        );
        const events = await response.json();
        loading = false;

        if (events.length === 0) {
            allDataLoaded = true;
            return;
        }

        events.forEach((event) => {
            const eventItem = document.createElement("div");
            eventItem.className = "event-item";

            // Create a canvas element for cropped and resized face
            const canvas = document.createElement("canvas");
            const ctx = canvas.getContext("2d");

            // Set the target size for the cropped and resized image
            const TARGET_SIZE = 100;
            canvas.width = TARGET_SIZE;
            canvas.height = TARGET_SIZE;

            // Load the original image and crop it
            const img = new Image();
            img.src = event.screenshot_path;
            img.onload = () => {
                const { bbox_x, bbox_y, bbox_w, bbox_h } = event;

                // Draw the cropped region onto the canvas, scaled to the target size
                ctx.drawImage(
                    img,
                    bbox_x,
                    bbox_y,
                    bbox_w,
                    bbox_h, // Source rectangle
                    0,
                    0,
                    TARGET_SIZE,
                    TARGET_SIZE, // Destination rectangle
                );
            };

            eventItem.innerHTML = `
                <div class="event-details">
                    <p><strong>UUID:</strong> ${event.id}</p>
                    <p><strong>Confidence:</strong> ${event.confidence}</p>
                    <p><strong>Timestamp:</strong> ${event.created_date} (${timeAgo(event.created_date)})</p>
                </div>
            `;

            eventItem.prepend(canvas);
            eventItem.addEventListener("click", () => {
                window.open(event.screenshot_path, "_blank");
            });
            eventList.appendChild(eventItem);
        });

        currentPage++;
    }

    // Infinite scrolling logic
    window.addEventListener("scroll", () => {
        if (
            window.innerHeight + window.scrollY >=
            document.body.scrollHeight - 100
        ) {
            loadEvents();
        }
    });

    async function createPeer() {
        pc = new RTCPeerConnection();
        pc.onicecandidate = (e) => {
            if (e.candidate) {
                ws.send(
                    JSON.stringify({ type: "candidate", candidate: e.candidate })
                );
            }
        };
        pc.ontrack = (e) => {
            remoteAudio.srcObject = e.streams[0];
        };
    }

    function cleanupCall() {
        if (localStream) {
            localStream.getTracks().forEach((t) => t.stop());
            localStream = null;
        }
        if (pc) {
            pc.close();
            pc = null;
        }
        if (ws) {
            ws.close();
            ws = null;
        }
        remoteAudio.srcObject = null;
        callBtn.textContent = "📞";
        callBtn.disabled = false;
        isCalling = false;
    }

    callBtn.addEventListener("click", async () => {
        if (isCalling) {
            cleanupCall();
            return;
        }

        callBtn.disabled = true;
        const protocol = location.protocol === "https:" ? "wss" : "ws";
        ws = new WebSocket(`${protocol}://${location.host}/ws`);

        ws.onmessage = async (evt) => {
            const msg = JSON.parse(evt.data);
            if (msg.type === "offer") {
                await createPeer();
                await pc.setRemoteDescription(msg.sdp);
                localStream = await navigator.mediaDevices.getUserMedia({
                    audio: true,
                });
                localStream.getTracks().forEach((t) => pc.addTrack(t, localStream));
                const ans = await pc.createAnswer();
                await pc.setLocalDescription(ans);
                ws.send(
                    JSON.stringify({ type: "answer", sdp: pc.localDescription })
                );
            } else if (msg.type === "answer") {
                await pc.setRemoteDescription(msg.sdp);
            } else if (msg.type === "candidate") {
                try {
                    await pc.addIceCandidate(msg.candidate);
                } catch (err) {
                    console.error(err);
                }
            }
        };

        ws.onopen = async () => {
            await createPeer();
            localStream = await navigator.mediaDevices.getUserMedia({ audio: true });
            localStream.getTracks().forEach((t) => pc.addTrack(t, localStream));
            const offer = await pc.createOffer();
            await pc.setLocalDescription(offer);
            ws.send(
                JSON.stringify({ type: "offer", sdp: pc.localDescription })
            );
            callBtn.disabled = false;
            callBtn.textContent = "📴";
            isCalling = true;
        };

        ws.onclose = cleanupCall;
    });

    // Automatically initiate the call based on the URL parameter
    if (autoCall) {
        callBtn.click();
    }
});
