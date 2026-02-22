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