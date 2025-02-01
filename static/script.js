document.addEventListener("DOMContentLoaded", () => {
    const video = document.getElementById("camera-feed");
    const liveSection = document.getElementById("live-section");
    const historySection = document.getElementById("history-section");
    const navLive = document.getElementById("nav-live");
    const navHistory = document.getElementById("nav-history");
    const eventList = document.getElementById("event-list");

    let currentPage = 0;
    const pageSize = 30;
    let loading = false;
    let allDataLoaded = false;

    // Initialize HLS stream
    if (Hls.isSupported()) {
        const hls = new Hls();
        hls.loadSource("/static/video/live.m3u8");
        hls.attachMedia(video);
        hls.on(Hls.Events.MANIFEST_PARSED, () => {
            video.play();
        });
    } else if (video.canPlayType("application/vnd.apple.mpegurl")) {
        video.src = "/static/video/live.m3u8";
        video.addEventListener("loadedmetadata", () => {
            video.play();
        });
    }

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
                    <p><strong>Timestamp:</strong> ${event.created_date}</p>
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
});
