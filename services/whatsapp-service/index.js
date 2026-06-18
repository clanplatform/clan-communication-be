/**
 * WhatsApp orchestration shim (Node.js).
 * Receives webhook events from Meta and forwards them to the Python service.
 */
const express = require("express");
const axios = require("axios");

const app = express();
app.use(express.json());

const PYTHON_SERVICE_URL = process.env.PYTHON_SERVICE_URL || "http://localhost:8005";
const VERIFY_TOKEN = process.env.META_VERIFY_TOKEN || "clan-verify-token";
const PORT = process.env.PORT || 3001;

// Meta webhook verification
app.get("/webhook", (req, res) => {
  const mode = req.query["hub.mode"];
  const token = req.query["hub.verify_token"];
  const challenge = req.query["hub.challenge"];
  if (mode === "subscribe" && token === VERIFY_TOKEN) {
    return res.status(200).send(challenge);
  }
  res.sendStatus(403);
});

// Receive incoming WhatsApp messages / status updates
app.post("/webhook", async (req, res) => {
  const body = req.body;
  res.sendStatus(200);

  try {
    if (body.object !== "whatsapp_business_account") return;
    for (const entry of body.entry || []) {
      for (const change of entry.changes || []) {
        const value = change.value;
        if (value.messages) {
          for (const msg of value.messages) {
            await axios.post(`${PYTHON_SERVICE_URL}/api/v1/webhook/incoming`, {
              from: msg.from,
              message_id: msg.id,
              timestamp: msg.timestamp,
              type: msg.type,
              text: msg.text?.body,
            });
          }
        }
        if (value.statuses) {
          for (const status of value.statuses) {
            await axios.post(`${PYTHON_SERVICE_URL}/api/v1/webhook/status`, {
              message_id: status.id,
              status: status.status,
              timestamp: status.timestamp,
              recipient: status.recipient_id,
            });
          }
        }
      }
    }
  } catch (err) {
    console.error("Webhook processing error:", err.message);
  }
});

app.get("/health", (_req, res) => res.json({ status: "ok", service: "whatsapp-shim" }));

app.listen(PORT, () => console.log(`WhatsApp shim listening on port ${PORT}`));
