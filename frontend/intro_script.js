function upload() {
  const fileInput = document.getElementById("file");

  if (!fileInput.files.length) {
    alert("Select an image");
    return;
  }

  const formData = new FormData();
  formData.append("file", fileInput.files[0]);

  fetch("http://localhost:5000/upload", {
    method: "POST",
    body: formData
  })
  .then(res => res.json())
  .then(data => alert(data.message))
  .catch(() => alert("Upload failed"));
}