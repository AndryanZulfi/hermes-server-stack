document.getElementById("btnSync").addEventListener("click", () => {
  const statusEl = document.getElementById("status");
  statusEl.style.display = "block";
  statusEl.className = "";
  statusEl.innerText = "Mengirim...";

  chrome.runtime.sendMessage({ action: "sync_now" }, (res) => {
    if (chrome.runtime.lastError) {
      statusEl.className = "error";
      statusEl.innerText = "Error: " + chrome.runtime.lastError.message;
      return;
    }

    if (res && res.success) {
      statusEl.className = "success";
      statusEl.innerText = `✓ Berhasil! ${res.count} cookie terkirim ke server deb-zlf.`;
    } else {
      statusEl.className = "error";
      statusEl.innerText = `✗ Gagal: ${res?.error || res?.message || "Status " + res?.status}`;
    }
  });
});
