const POST_BACKEND = "http://localhost:5000/collect/";
function getVideoSrc() {
  source = { 1: window.location.origin, 2: "http://cdn.dummy.com" };
  vid = {
    1: "/vid/short.mp4",
    // 2: "/vid/pprogressive.mp4",
    // 3: "/vid/out.mp4",
    // 4: "/vid/Dam.webm",
    // 5: "/vid/trans_Klyuchevskoy_NG.mp4",
  };
  const qparams = Object.fromEntries(
    new URLSearchParams(window.location.search).entries()
  );
  return source[qparams["s"] || 1] + vid[qparams["v"] || 1];
}

const MediaEvents = [
  "abort",
  "canplay",
  "canplaythrough",
  "durationchange",
  "complete",
  "emptied",
  "ended",
  "error",
  "loadeddata",
  "loadedmetadata",
  "loadstart",
  "pause",
  "play",
  "playing",
  "ratechange",
  "suspend",
  "seeked",
  "seeking",
  "stalled",
  "volumechange",
  "waiting",
];
// https://developer.mozilla.org/en-US/docs/Web/API/HTMLMediaElement
window.addEventListener("DOMContentLoaded", () => {
  video = document.querySelector("#video");
  video.setAttribute("src", getVideoSrc());
  let events = [];
  let pqEvents = {
    samples: 0,
    creationTimes: [],
    droppedVideoFrames: [],
    totalVideoFrames: [],
  };

  MediaEvents.forEach((evtKey) => {
    video.addEventListener(evtKey, (evt) => {
      events.push([performance.now(), evt.type]);
    });
  });

  video.addEventListener("timeupdate", () => {
    let pq = video.getVideoPlaybackQuality();
    pqEvents.creationTimes.push(pq["creationTime"]);
    pqEvents.totalVideoFrames.push(pq["totalVideoFrames"]);
    pqEvents.droppedVideoFrames.push(pq["droppedVideoFrames"]);
  });

  video.addEventListener("ended", () => {
    pqEvents.samples = pqEvents.creationTimes.length;
    postData(POST_BACKEND, {
      id:
        Math.floor(performance.now() % 0x10000).toString(16) +
        Math.floor((1 + Math.random()) * 0x1000000)
          .toString(16)
          .substring(1),
      timestamp: Date.now(),
      target: video.src,
      events: events,
      playbackquality: pqEvents,
    });
  });

  video.play();
});

async function postData(url = "", data = {}) {
  await fetch(url, {
    method: "POST",
    mode: "no-cors",
    cache: "no-cache",
    credentials: "same-origin",
    headers: { "Content-Type": "application/json" },
    referrerPolicy: "no-referrer",
    body: JSON.stringify(data),
  });
}
