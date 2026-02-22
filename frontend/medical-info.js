window.onload = () => {
  const mode = sessionStorage.getItem("mode");

  if (!mode) {
    alert("No prescription found.");
    return;
  }

  if (mode === "text") {
    explainText(sessionStorage.getItem("prescriptionText"));
  } else {
    explainImage();
  }
};

//Typed text
function explainText(text) {
  fetch("http://localhost:5000/api/explain", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text })
  })
    .then(res => res.json())
    .then(fillCards)
    .catch(() => alert("Error explaining prescription"));
}

//Image upload
function explainImage() {
  const input = document.getElementById("image"); // OR re-select if needed
  const formData = new FormData();
  formData.append("image", input.files[0]);

  fetch("http://localhost:5000/api/explain", {
    method: "POST",
    body: formData
  })
    .then(res => res.json())
    .then(fillCards)
    .catch(() => alert("Error explaining prescription"));
}

//Fill the cards
function fillCards(data) {
  document.getElementById("use").innerHTML =
    `<p>${data.purpose}</p>`;

  document.getElementById("dosages").innerHTML =
    `<p>${data.usage}</p>`;

  document.getElementById("side-effects").innerHTML =
    data.side_effects.map(e => `<p>• ${e}</p>`).join("");

  document.getElementById("seek-help").innerHTML =
    data.warnings.map(w => `<p>• ${w}</p>`).join("");

  document.getElementById("disclaimer").innerText =
    data.disclaimer;
}

//Reminder
function addReminder() {
  const medicine = document.getElementById("medicine").value;
  const time = document.getElementById("time").value;

  if (!medicine || !time) {
    alert("Fill in all fields");
    return;
  }

  // Get today’s date
  const now = new Date();
  const [hours, minutes] = time.split(":");

  now.setHours(hours);
  now.setMinutes(minutes);
  now.setSeconds(0);

  // End time is 10 minutes later
  const end = new Date(now.getTime() + 10 * 60000);

  function format(date) {
    return date.toISOString().replace(/[-:]|\.\d{3}/g, "");
  }

  const startStr = format(now);
  const endStr = format(end);

  const title = `Take ${medicine}`;
  const details = "Medicine reminder";

  const url =
    "https://calendar.google.com/calendar/render?action=TEMPLATE" +
    "&text=" + encodeURIComponent(title) +
    "&details=" + encodeURIComponent(details) +
    "&dates=" + startStr + "/" + endStr;

  window.open(url, "_blank");
}