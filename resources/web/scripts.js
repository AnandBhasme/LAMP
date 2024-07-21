const currentDate = new Date();
const dateOptions = { day: "numeric", month: "long", year: "numeric" };
document.getElementById("currentDate").textContent =
  currentDate.toLocaleDateString("en-GB", dateOptions);

let hideContentsTimeout;
let prev_time = "";
let i = 0;

setInterval(() => {
  fetch("/data")
    .then((response) => response.json())
    .then((data) => {
      clearTimeout(hideContentsTimeout);
      const audio = document.getElementById("audioPlayer");
      if (data.message) {
        if (data.time != prev_time) {
          audio.src = "resources/sounds/Denied.wav";
          audio.play();
        }
        document.getElementById("lastScanned").textContent = data.message;
      } else if (data.last_scanned) {
        if (data.time != prev_time) {
          i = 0;
        }
        if (i < 10) {
          document.getElementById("lastScanned").textContent = data.last_scanned;
          document.getElementById("lastAction").textContent = data.last_action;
          document.getElementById("name").textContent = data.last_name;
          document.getElementById("time").innerHTML =
            "at<br><u>" + data.time + "</u>";
          if (data.last_action == "Checked In") {
            document.getElementById("lastAction").style.color = "rgb(0, 255, 30)";
            document.getElementById("Greeting").textContent = "Welcome, ";
            if (i == 0) {
              audio.src = "resources/sounds/Approved.wav";
              audio.play();
            }
          } else {
            document.getElementById("lastAction").style.color = "rgb(255,0,0)";
            document.getElementById("Greeting").textContent = "Goodbye, ";
            if (i == 0) {
              audio.src = "resources/sounds/Exit.mp3";
              audio.play();
            }
          }
          i++;
        } else {
          document.getElementById("Greeting").textContent = "";
          document.getElementById("name").textContent = "";
          document.getElementById("lastAction").textContent = "";
          document.getElementById("time").textContent = "";
        }
      }
      document.getElementById("studentCount").textContent = data.current_count;
      prev_time = data.time;

      hideContentsTimeout = setTimeout(() => {
        document.getElementById("Greeting").textContent = "";
        document.getElementById("name").textContent = "";
        document.getElementById("lastAction").textContent = "";
        document.getElementById("time").textContent = "";
      }, 4000);
    })
    .catch(console.error);
}, 500);

document.addEventListener("DOMContentLoaded", function () {
  const audioPlayer = document.getElementById("audioPlayer");
  const muteButton = document.getElementById("muteButton");

  audioPlayer.muted = true;
  muteButton.style.backgroundImage = "url('resources/mute.png')";

  muteButton.addEventListener("click", function () {
    if (audioPlayer.muted) {
      audioPlayer.muted = false;
      muteButton.style.backgroundImage = "url('resources/unmute.png')";
    } else {
      audioPlayer.muted = true;
      muteButton.style.backgroundImage = "url('resources/mute.png')";
    }
  });
});