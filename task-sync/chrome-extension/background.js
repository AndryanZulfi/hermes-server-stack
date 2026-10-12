const RECEIVER_URL = "http://172.23.0.134:8089/api/sync-cookie";
const AUTH_TOKEN = "zlf-idn-task-sync-2026";

async function syncCookies() {
  try {
    const cookies = await chrome.cookies.getAll({ domain: "idn.id" });
    const taskCookies = cookies.filter(c => 
      c.domain.includes("task.idn.id") || 
      c.domain === ".idn.id" || 
      c.domain === "idn.id"
    );
    
    if (taskCookies.length === 0) {
      console.log("[Sync] Tidak ada cookie untuk idn.id ditemukan.");
      return { success: false, message: "Belum ada cookie idn.id" };
    }

    const cookieHeader = taskCookies.map(c => `${c.name}=${c.value}`).join("; ");

    const payload = {
      updated_at: new Date().toISOString(),
      source: "chrome_extension",
      cookie_header: cookieHeader,
      cookies: taskCookies
    };

    const res = await fetch(RECEIVER_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Auth-Token": AUTH_TOKEN
      },
      body: JSON.stringify(payload)
    });

    if (res.ok) {
      console.log("[Sync] Berhasil disinkronkan ke server deb-zlf!");
      chrome.action.setBadgeText({ text: "OK" });
      chrome.action.setBadgeBackgroundColor({ color: "#16a34a" });
      return { success: true, count: taskCookies.length };
    } else {
      console.error("[Sync] Server mengembalikan status:", res.status);
      chrome.action.setBadgeText({ text: "ERR" });
      chrome.action.setBadgeBackgroundColor({ color: "#dc2626" });
      return { success: false, status: res.status };
    }
  } catch (err) {
    console.error("[Sync] Gagal menghubungkan ke receiver:", err);
    chrome.action.setBadgeText({ text: "ERR" });
    chrome.action.setBadgeBackgroundColor({ color: "#dc2626" });
    return { success: false, error: err.message };
  }
}

// 1. Sinkronkan otomatis jika ada perubahan cookie di domain idn.id
chrome.cookies.onChanged.addListener((changeInfo) => {
  if (changeInfo.cookie && changeInfo.cookie.domain && changeInfo.cookie.domain.includes("idn.id")) {
    console.log("[Sync] Cookie berubah:", changeInfo.cookie.name);
    syncCookies();
  }
});

// 2. Sinkronkan otomatis saat tab task.idn.id dibuka atau di-refresh
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === "complete" && tab.url && tab.url.includes("task.idn.id")) {
    console.log("[Sync] Tab task.idn.id aktif, menjalankan sync...");
    syncCookies();
  }
});

// 3. Sinkronkan saat extension pertama kali dimuat
chrome.runtime.onInstalled.addListener(() => {
  syncCookies();
});

chrome.runtime.onStartup.addListener(() => {
  syncCookies();
});

// 4. Handler pesan dari popup UI
chrome.runtime.onMessage.addListener((req, sender, sendResponse) => {
  if (req.action === "sync_now") {
    syncCookies().then(res => sendResponse(res));
    return true;
  }
});
