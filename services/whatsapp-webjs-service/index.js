"use strict";
/**
 * WhatsApp Web.js worker service.
 * Maintains a persistent browser session and exposes an HTTP API
 * for the Python whatsapp-service to dispatch messages through.
 */
const fs = require("fs");
const path = require("path");
const express = require("express");
const { Client, LocalAuth, MessageMedia } = require("whatsapp-web.js");
const qrcode = require("qrcode-terminal");
const axios = require("axios");

const app = express();
app.use(express.json());

const PORT = process.env.PORT || 3000;
const NOTIFY_CALLBACK_URL = process.env.NOTIFY_CALLBACK_URL || "";
const SESSION_ID = process.env.SESSION_ID || "default";

// ---------------------------------------------------------------------------
// WhatsApp client
// ---------------------------------------------------------------------------

let clientReady = false;
let qrCode = null;

const client = new Client({
  authStrategy: new LocalAuth({ clientId: SESSION_ID }),
  puppeteer: {
    headless: true,
    args: [
      "--no-sandbox",
      "--disable-setuid-sandbox",
      "--disable-dev-shm-usage",
      "--disable-gpu",
    ],
  },
});

client.on("qr", (qr) => {
  qrCode = qr;
  qrcode.generate(qr, { small: true });
  console.log("[WhatsApp] QR code generated — scan with WhatsApp app");
});

client.on("ready", () => {
  clientReady = true;
  qrCode = null;
  console.log("[WhatsApp] Client is ready");
});

client.on("disconnected", (reason) => {
  clientReady = false;
  console.warn("[WhatsApp] Disconnected:", reason);
  setTimeout(() => client.initialize(), 5000);
});

client.on("message", async (msg) => {
  if (NOTIFY_CALLBACK_URL) {
    try {
      await axios.post(`${NOTIFY_CALLBACK_URL}/api/v1/webhook/incoming`, {
        from: msg.from,
        body: msg.body,
        timestamp: msg.timestamp,
        message_id: msg.id._serialized,
        type: msg.type,
      });
    } catch (err) {
      console.error("[WhatsApp] Failed to forward incoming message:", err.message);
    }
  }
});

// Remove stale Chromium lock files left by a previous container instance.
// Without this, Chromium refuses to start when the volume is reused.
function cleanupChromiumLocks() {
  const sessionDir = path.join("/app/.wwebjs_auth", `session-${SESSION_ID}`);
  for (const lockFile of ["SingletonLock", "SingletonSocket", "SingletonCookie"]) {
    const lockPath = path.join(sessionDir, lockFile);
    try {
      if (fs.existsSync(lockPath)) {
        fs.unlinkSync(lockPath);
        console.log(`[WhatsApp] Removed stale lock: ${lockFile}`);
      }
    } catch (err) {
      console.warn(`[WhatsApp] Could not remove ${lockFile}:`, err.message);
    }
  }
}

cleanupChromiumLocks();
client.initialize();

// ---------------------------------------------------------------------------
// HTTP API
// ---------------------------------------------------------------------------

/**
 * POST /send
 * Body: { to: "+1234567890", message: "text", mediaUrl?: "https://..." }
 */
app.post("/send", async (req, res) => {
  if (!clientReady) {
    return res.status(503).json({ error: "WhatsApp client not ready", qr: qrCode });
  }

  const { to, message, mediaUrl } = req.body;
  if (!to || !message) {
    return res.status(400).json({ error: "to and message are required" });
  }

  // Normalise number to WhatsApp JID format
  const jid = to.replace(/[^0-9]/g, "") + "@c.us";

  try {
    let sentMsg;
    if (mediaUrl) {
      const media = await MessageMedia.fromUrl(mediaUrl, { unsafeMime: true });
      sentMsg = await client.sendMessage(jid, media, { caption: message });
    } else {
      sentMsg = await client.sendMessage(jid, message);
    }
    return res.json({ success: true, messageId: sentMsg.id._serialized });
  } catch (err) {
    console.error("[WhatsApp] Send error:", err.message);
    return res.status(500).json({ error: err.message });
  }
});

/**
 * GET /qr — return current QR code for scanning
 */
app.get("/qr", (_req, res) => {
  if (clientReady) return res.json({ status: "connected" });
  if (!qrCode) return res.json({ status: "initialising" });
  res.json({ status: "pending_scan", qr: qrCode });
});

/**
 * GET /health
 */
app.get("/health", (_req, res) => {
  res.json({
    status: "ok",
    service: "whatsapp-webjs-service",
    clientReady,
  });
});

app.listen(PORT, () =>
  console.log(`[WhatsApp WebJS] Listening on port ${PORT}`)
);
