const API_BASE = "http://localhost:8000";

// ---------- LinkedIn connection ----------

async function checkAuthStatus() {
  const res = await fetch(`${API_BASE}/auth/status`);
  const data = await res.json();
  const statusDiv = document.getElementById("authStatus");
  const connectBtn = document.getElementById("connectLinkedInBtn");

  if (data.connected) {
    statusDiv.innerHTML = `✅ Connected to LinkedIn (${data.person_urn})`;
    connectBtn.style.display = "none";
  } else {
    statusDiv.innerHTML = "❌ Not connected to LinkedIn";
    connectBtn.style.display = "inline-block";
  }
}

document.getElementById("connectLinkedInBtn").addEventListener("click", () => {
  window.location.href = `${API_BASE}/auth/linkedin`;
});

// ---------- Event config ----------

document.getElementById("eventConfigForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const payload = {
    event_name: document.getElementById("eventName").value,
    tagline: document.getElementById("eventTagline").value,
    audience: document.getElementById("eventAudience").value,
    tone: document.getElementById("eventTone").value,
    default_hashtags: document.getElementById("eventHashtags").value.split(",").map(s => s.trim()),
  };
  const res = await fetch(`${API_BASE}/event/config`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await res.json();
  alert("Event config saved: " + JSON.stringify(data));
});

// ---------- Inputs ----------

document.getElementById("inputForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const payload = {
    type: document.getElementById("inputType").value,
    title: document.getElementById("inputTitle").value,
    text: document.getElementById("inputText").value,
    image_url: null,
    priority: document.getElementById("inputPriority").value,
  };
  const res = await fetch(`${API_BASE}/inputs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await res.json();

  const fileInput = document.getElementById("inputImageFile");
  if (fileInput.files.length > 0) {
    const formData = new FormData();
    formData.append("file", fileInput.files[0]);
    const uploadRes = await fetch(`${API_BASE}/inputs/${data.id}/image`, {
      method: "POST",
      body: formData,
    });
    if (!uploadRes.ok) {
      const err = await uploadRes.json();
      alert("Input created, but image upload failed: " + JSON.stringify(err));
    }
  }

  alert("Input created: " + data.id);
  document.getElementById("inputForm").reset();
  loadPendingInputs();
});

async function loadPendingInputs() {
  const res = await fetch(`${API_BASE}/inputs/pending`);
  const inputs = await res.json();
  const container = document.getElementById("pendingList");
  container.innerHTML = "";
  for (const inp of inputs) {
    const div = document.createElement("div");
    div.className = "item";
    const imageBadge = inp.image_url ? " 📷" : "";
    div.innerHTML = `
      <h3>${inp.title} (${inp.type})${imageBadge}</h3>
      <p>${inp.text}</p>
      <p class="small">ID: ${inp.id} | Priority: ${inp.priority}</p>
      <button onclick="generatePreview('${inp.id}')">Generate Preview</button>
      <div id="preview-${inp.id}" style="margin-top:8px;"></div>
    `;
    container.appendChild(div);
  }
}

async function generatePreview(inputId) {
  const res = await fetch(`${API_BASE}/inputs/${inputId}/generate`, { method: "POST" });
  const data = await res.json();
  const previewDiv = document.getElementById(`preview-${inputId}`);
  previewDiv.innerHTML = `
    <p><strong>Generated:</strong></p>
    <textarea id="gen-text-${inputId}" style="width:100%;min-height:120px;">${escapeHtml(data.generated_text)}</textarea>
    <button onclick="approveAndPost('${inputId}')">Approve & Post</button>
  `;
}

async function approveAndPost(inputId) {
  const genText = document.getElementById(`gen-text-${inputId}`).value;
  const res = await fetch(`${API_BASE}/inputs/${inputId}/approve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ generated_text: genText }),
  });
  if (!res.ok) {
    const err = await res.json();
    alert("Failed: " + JSON.stringify(err));
    return;
  }
  const data = await res.json();
  alert("Posted: " + JSON.stringify(data));
  loadPendingInputs();
  loadPosts();
}

async function loadPosts() {
  const res = await fetch(`${API_BASE}/posts`);
  const posts = await res.json();
  const container = document.getElementById("postsList");
  container.innerHTML = "";
  for (const post of posts) {
    const div = document.createElement("div");
    div.className = "item";
    div.innerHTML = `
      <h3>Post ${post.id}</h3>
      <p>${escapeHtml(post.text)}</p>
      <p class="small">Input: ${post.input_id} | Status: ${post.status}</p>
    `;
    container.appendChild(div);
  }
}

function escapeHtml(str) {
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

checkAuthStatus();
loadPendingInputs();
loadPosts();