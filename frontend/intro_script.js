function nextPage() {
  const imageInput = document.getElementById("image");
  const text = document.getElementById("text").value.trim();

  const hasImage = imageInput.files.length > 0;
  const hasText = text.length > 0;

  // Enforce exactly one
  if ((hasImage && hasText) || (!hasImage && !hasText)) {
    alert("Please upload an image OR type the prescription (not both).");
    return;
  }

  sessionStorage.clear();

  if (hasText) {
    sessionStorage.setItem("type", "text");
    sessionStorage.setItem("prescriptionText", text);
    window.location.href = "medical-info.html";
    return;
  }

  // Image case
  const reader = new FileReader();
  reader.onload = function () {
    sessionStorage.setItem("type", "image");
    sessionStorage.setItem("prescriptionImage", reader.result);
    window.location.href = "analysis.html";
  };
  reader.readAsDataURL(imageInput.files[0]);
}