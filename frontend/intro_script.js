function nextPage() {
  const imageInput = document.getElementById("image");
  const textInput = document.getElementById("text");

  const hasImage = imageInput.files.length > 0;
  const hasText = textInput.value.trim() !== "";

  if (hasImage && hasText) {
    alert("Please upload an image OR type the prescription, not both.");
    return;
  }

  if (!hasImage && !hasText) {
    alert("Please provide a prescription.");
    return;
  }

  // Save choice temporarily
  if (hasText) {
    sessionStorage.setItem("mode", "text");
    sessionStorage.setItem("prescriptionText", textInput.value.trim());
  } else {
    sessionStorage.setItem("mode", "image");
    sessionStorage.setItem("prescriptionImage", imageInput.files[0].name);
  }

  window.location.href = "medical-info.html";

}



