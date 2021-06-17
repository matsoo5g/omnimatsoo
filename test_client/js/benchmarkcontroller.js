function prepareStatPayloadFromQueryParameters() {
  source = {
    1: window.location.origin,
    2: "https://matsoo5gclient.s3.amazonaws.com",
    3: "https://d3ovjicgaozkeh.cloudfront.net",
  };
  vid = {
    1: "/vid/short.mp4",
    2: "/vid/bitmovin_6M_137s_hd.mp4",
    3: "/vid/Dunkerque_2M_276s_fhd.mp4",
    4: "/vid/Klyuchevskoy_10M_147s_4k.mp4",
    5: "/vid/Dam_20M_24s_6k.mp4",
    6: "/vid/Dam_10M_24s_6k.webm",
  };
  const qparams = Object.fromEntries(
    new URLSearchParams(window.location.search).entries()
  );
  let source_string = source[qparams["s"] || 1];
  if ("so" in qparams) {
    source_string = qparams["so"];
  }
  return {
    videoRoot: source_string + (vid[qparams["v"] || 1] || vid[1]),
    deviceTag: qparams["dtag"] || "unknown_device",
    postBackend: qparams["post"] || "http://localhost:5000/collect/",
  };
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

window.addEventListener("DOMContentLoaded", () => {
  video = document.querySelector("#video");
  qpvars = prepareStatPayloadFromQueryParameters();
  video.setAttribute("src", qpvars.videoRoot);
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

  video.addEventListener("ended", () => {
    pqEvents.samples = pqEvents.creationTimes.length;
    postData(qpvars.postBackend, {
      id:
        Math.floor(performance.now() % 0x10000).toString(16) +
        Math.floor((1 + Math.random()) * 0x1000000)
          .toString(16)
          .substring(1),
      timestamp: Date.now(),
      target: video.src,
      duration: video.duration,
      events: events,
      device_tag: qpvars.deviceTag,
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
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}
