document.addEventListener("DOMContentLoaded", () => {
    const video = document.getElementById("camera-feed");

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
});
