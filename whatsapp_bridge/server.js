/**
 * AwaazLedger WhatsApp Bridge (Docker-free Evolution API drop-in)
 * Powered by Baileys & Express.
 *
 * Runs locally on Node.js without requiring Docker or root privileges.
 * Mimics Evolution API port 8080 endpoints and forwards incoming messages
 * to AwaazLedger backend at http://localhost:8000/api/v1/webhooks/whatsapp.
 */

const express = require('express');
const { makeWASocket, useMultiFileAuthState, DisconnectReason, fetchLatestBaileysVersion, downloadMediaMessage } = require('@whiskeysockets/baileys');
const pino = require('pino');
const qrcodeTerminal = require('qrcode-terminal');
const QRCode = require('qrcode');
const path = require('path');
const fs = require('fs');
const http = require('http');

const PORT = process.env.PORT || 8080;
const WEBHOOK_URL = process.env.WEBHOOK_URL || 'http://localhost:8000/api/v1/webhooks/whatsapp';
const INSTANCE_NAME = process.env.INSTANCE_NAME || 'paytm-awaazledger';
const AUTH_DIR = path.join(__dirname, 'auth_info_baileys');

let sock = null;
let connectionState = 'connecting';
let currentQR = null;
let lastUserChatJid = null;
const userChatJidMap = new Map();
const botSentMessageIds = new Set();
const LOG_FILE = path.join(__dirname, 'bridge.log');

function logBridge(msg) {
    const line = `[${new Date().toISOString()}] ${msg}\n`;
    console.log(msg);
    try {
        fs.appendFileSync(LOG_FILE, line, 'utf8');
    } catch (_) {}
}

const app = express();
app.use(express.json({ limit: '50mb' }));
app.use(express.urlencoded({ extended: true, limit: '50mb' }));

// Ensure dist and auth dirs exist
const distDir = path.join(__dirname, '..', 'dist');
if (!fs.existsSync(distDir)) {
    fs.mkdirSync(distDir, { recursive: true });
}
if (!fs.existsSync(AUTH_DIR)) {
    fs.mkdirSync(AUTH_DIR, { recursive: true });
}

async function startWhatsApp() {
    const { state, saveCreds } = await useMultiFileAuthState(AUTH_DIR);
    const { version } = await fetchLatestBaileysVersion();

    sock = makeWASocket({
        version,
        logger: pino({ level: 'silent' }),
        printQRInTerminal: false,
        auth: state,
        browser: ['AwaazLedger', 'Chrome', '120.0.0'],
    });

    sock.ev.on('creds.update', saveCreds);

    sock.ev.on('connection.update', async (update) => {
        const { connection, lastDisconnect, qr } = update;

        if (qr) {
            currentQR = qr;
            console.log('\n============================================================');
            console.log('SCAN THIS QR CODE WITH WHATSAPP (+918788021157):');
            console.log('WhatsApp -> Linked Devices -> Link a Device');
            console.log('============================================================\n');
            qrcodeTerminal.generate(qr, { small: true });

            const qrPath = path.join(distDir, 'evolution_qr.png');
            try {
                await QRCode.toFile(qrPath, qr);
                console.log(`[QR Saved] ${qrPath}`);
            } catch (err) {
                console.error('[Error saving QR PNG]:', err.message);
            }
        }

        if (connection === 'close') {
            const shouldReconnect = lastDisconnect?.error?.output?.statusCode !== DisconnectReason.loggedOut;
            console.log(`\n[WhatsApp Connection Closed] Reconnecting: ${shouldReconnect}...`);
            connectionState = 'close';
            if (shouldReconnect) {
                setTimeout(startWhatsApp, 3000);
            }
        } else if (connection === 'open') {
            connectionState = 'open';
            currentQR = null;
            console.log('\n============================================================');
            console.log('>>> WHATSAPP CONNECTED SUCCESSFULLY! <<<');
            console.log(`Ready to receive disputes and voice notes!`);
            console.log('============================================================\n');
        }
    });

    sock.ev.on('messages.upsert', async (m) => {
        try {
            if (m.type !== 'notify' && m.type !== 'append') return;

            for (const msg of m.messages) {
                // Ignore bot's own outbound messages to prevent loops
                if (botSentMessageIds.has(msg.key.id)) continue;

                const remoteJid = msg.key.remoteJid;
                if (!remoteJid || remoteJid.includes('@g.us') || remoteJid.includes('@newsletter') || remoteJid.includes('@broadcast') || remoteJid === 'status@broadcast') continue;

                const myPhone = sock?.user?.id ? sock.user.id.split(':')[0] : '918788021157';
                const myLid = sock?.user?.lid ? sock.user.lid.split(':')[0] : null;
                const myJid = `${myPhone}@s.whatsapp.net`;

                // Support both:
                // 1. Someone else messaging this number (fromMe == false)
                // 2. You messaging yourself on WhatsApp (fromMe == true in your self-chat)
                const isSelfMessage = msg.key.fromMe && (
                    remoteJid === myJid ||
                    remoteJid.includes(myPhone) ||
                    (myLid && remoteJid.includes(myLid)) ||
                    (lastUserChatJid && remoteJid === lastUserChatJid)
                );

                if (msg.key.fromMe && !isSelfMessage) {
                    // Ignore outbound messages you sent to other contacts
                    continue;
                }

                if (isSelfMessage) {
                    lastUserChatJid = remoteJid;
                }

                const senderJid = isSelfMessage ? myJid : remoteJid;
                logBridge(`\n[Incoming Message] From: ${senderJid}${isSelfMessage ? ' (Self-Message)' : ''} (chatJid: ${remoteJid})`);

                const cleanSender = senderJid.replace(/[^0-9]/g, '');
                userChatJidMap.set(cleanSender, remoteJid);
                userChatJidMap.set(senderJid, remoteJid);
                userChatJidMap.set(remoteJid, remoteJid);

                let text = extractTextFromBaileysMessage(msg.message);
                let messageType = 'conversation';
                let base64Media = null;
                let mimeType = null;

                if (msg.message?.audioMessage) {
                    messageType = 'audioMessage';
                    mimeType = msg.message.audioMessage.mimetype || 'audio/ogg';
                    console.log(`[Voice Note Received] Mime: ${mimeType}`);
                    try {
                        const buffer = await downloadMediaMessage(msg, 'buffer', {}, { logger: pino({ level: 'silent' }), reuploadRequest: sock.updateMediaMessage });
                        base64Media = buffer.toString('base64');
                    } catch (e) {
                        console.warn('[Could not decode audio buffer]:', e.message);
                    }
                } else if (msg.message?.imageMessage) {
                    messageType = 'imageMessage';
                    text = msg.message.imageMessage.caption || text || '';
                    mimeType = msg.message.imageMessage.mimetype || 'image/jpeg';
                    console.log(`[Screenshot Received] Caption: ${text}`);
                    try {
                        const buffer = await downloadMediaMessage(msg, 'buffer', {}, { logger: pino({ level: 'silent' }), reuploadRequest: sock.updateMediaMessage });
                        base64Media = buffer.toString('base64');
                    } catch (e) {
                        console.warn('[Could not decode image buffer]:', e.message);
                    }
                } else if (text) {
                    messageType = msg.message?.extendedTextMessage ? 'extendedTextMessage' : 'conversation';
                }

                console.log(`[Content] "${text || messageType}"`);

                // Format into Evolution API compatible webhook payload
                const webhookPayload = {
                    event: 'messages.upsert',
                    instance: INSTANCE_NAME,
                    data: {
                        key: {
                            remoteJid: senderJid,
                            fromMe: false,
                            id: msg.key.id,
                        },
                        messageType: messageType,
                        text: text,
                        message: msg.message,
                        base64: base64Media,
                        mimetype: mimeType,
                        messageTimestamp: msg.messageTimestamp,
                    },
                };

                // Forward to AwaazLedger backend
                forwardToBackend(webhookPayload);
            }
        } catch (err) {
            console.error('[Error handling message]:', err);
        }
    });
}

function forwardToBackend(payload) {
    try {
        const dataStr = JSON.stringify(payload);
        const url = new URL(WEBHOOK_URL);
        const req = http.request(
            {
                hostname: url.hostname,
                port: url.port || 8000,
                path: url.pathname,
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Content-Length': Buffer.byteLength(dataStr),
                },
                timeout: 10000,
            },
            (res) => {
                let body = '';
                res.on('data', (d) => (body += d));
                res.on('end', () => {
                    console.log(`[Backend Handled] Status: ${res.statusCode}`);
                });
            }
        );

        req.on('error', (e) => {
            console.error(`[Webhook Forward Failed]: ${e.message} (Is backend running on ${WEBHOOK_URL}?)`);
        });

        req.write(dataStr);
        req.end();
    } catch (e) {
        console.error('[Error forwarding to backend]:', e.message);
    }
}

// -------------------------------------------------------------
// Evolution API Compatible HTTP Endpoints
// -------------------------------------------------------------

// Health / Status
app.get('/', (req, res) => {
    res.json({
        status: 200,
        message: 'AwaazLedger WhatsApp Bridge is Running',
        version: '1.0.0',
        connectionState,
    });
});

app.get('/instance/fetchInstances', (req, res) => {
    res.json([
        {
            instance: {
                instanceName: INSTANCE_NAME,
                status: connectionState === 'open' ? 'open' : 'connecting',
            },
        },
    ]);
});

app.post('/instance/create', (req, res) => {
    res.json({
        instance: {
            instanceName: INSTANCE_NAME,
            status: connectionState === 'open' ? 'open' : 'connecting',
        },
        qrcode: {
            code: currentQR || '',
        },
    });
});

app.get('/instance/connect/:instance', (req, res) => {
    res.json({
        instance: req.params.instance,
        status: connectionState === 'open' ? 'open' : 'connecting',
        code: currentQR || '',
    });
});

function extractTextFromBaileysMessage(message) {
    if (!message) return '';
    if (message.conversation) return message.conversation;
    if (message.extendedTextMessage?.text) return message.extendedTextMessage.text;
    if (message.imageMessage?.caption) return message.imageMessage.caption;
    if (message.videoMessage?.caption) return message.videoMessage.caption;
    if (message.documentMessage?.caption) return message.documentMessage.caption;
    if (message.ephemeralMessage?.message) return extractTextFromBaileysMessage(message.ephemeralMessage.message);
    if (message.viewOnceMessage?.message) return extractTextFromBaileysMessage(message.viewOnceMessage.message);
    if (message.viewOnceMessageV2?.message) return extractTextFromBaileysMessage(message.viewOnceMessageV2.message);
    return '';
}

function resolveDestinationJid(number, cleanNumber, myPhone) {
    if (cleanNumber === myPhone) {
        if (lastUserChatJid) {
            return lastUserChatJid;
        }
        return `${myPhone}@s.whatsapp.net`;
    }
    if (userChatJidMap.get(number)) {
        return userChatJidMap.get(number);
    }
    if (userChatJidMap.get(cleanNumber)) {
        return userChatJidMap.get(cleanNumber);
    }
    if (number.includes('@')) {
        return number;
    }
    if (cleanNumber && cleanNumber.length >= 10 && cleanNumber.length <= 13) {
        return `${cleanNumber}@s.whatsapp.net`;
    }
    return number.includes('@') ? number : `${cleanNumber}@s.whatsapp.net`;
}

// Outbound send text
app.post('/message/sendText/:instance', async (req, res) => {
    try {
        const { number, text } = req.body;
        if (!number || !text) {
            return res.status(400).json({ error: 'Missing number or text' });
        }

        const cleanNumber = number.replace(/\D/g, '');
        const myPhone = sock?.user?.id ? sock.user.id.split(':')[0] : '918788021157';
        const jid = resolveDestinationJid(number, cleanNumber, myPhone);
        
        logBridge(`[Outbound Text] Sending to ${jid}: "${text.slice(0, 60)}..."`);

        if (sock && connectionState === 'open') {
            const sent = await sock.sendMessage(jid, { text });
            if (sent?.key?.id) {
                botSentMessageIds.add(sent.key.id);
            }
            return res.json({ status: 'SUCCESS', key: sent.key });
        } else {
            console.warn('[Outbound Text Mocked] WhatsApp not connected yet. Message logged.');
            return res.json({ status: 'MOCKED', warning: 'WhatsApp socket not open' });
        }
    } catch (err) {
        console.error('[Error sending text]:', err.message);
        return res.status(500).json({ error: err.message });
    }
});

// Outbound send media (e.g. tracker card image)
app.post('/message/sendMedia/:instance', async (req, res) => {
    try {
        const { number, media, caption } = req.body;
        if (!number || !media) {
            return res.status(400).json({ error: 'Missing number or media' });
        }

        const cleanNumber = number.replace(/\D/g, '');
        const myPhone = sock?.user?.id ? sock.user.id.split(':')[0] : '918788021157';
        const jid = resolveDestinationJid(number, cleanNumber, myPhone);
        logBridge(`[Outbound Media] Sending image to ${jid} (caption: ${caption || 'none'})`);

        if (sock && connectionState === 'open') {
            let buffer;
            if (media.startsWith('data:')) {
                const b64 = media.split(',')[1];
                buffer = Buffer.from(b64, 'base64');
            } else if (media.length > 500 && !media.startsWith('http')) {
                buffer = Buffer.from(media, 'base64');
            } else {
                buffer = { url: media };
            }

            const sent = await sock.sendMessage(jid, {
                image: buffer,
                caption: caption || '',
            });
            if (sent?.key?.id) {
                botSentMessageIds.add(sent.key.id);
            }
            return res.json({ status: 'SUCCESS', key: sent.key });
        } else {
            return res.json({ status: 'MOCKED', warning: 'WhatsApp socket not open' });
        }
    } catch (err) {
        console.error('[Error sending media]:', err.message);
        return res.status(500).json({ error: err.message });
    }
});

// Outbound send audio
app.post('/message/sendWhatsAppAudio/:instance', async (req, res) => {
    try {
        const { number, audio } = req.body;
        if (!number || !audio) {
            return res.status(400).json({ error: 'Missing number or audio' });
        }

        const cleanNumber = number.replace(/\D/g, '');
        const myPhone = sock?.user?.id ? sock.user.id.split(':')[0] : '918788021157';
        const jid = resolveDestinationJid(number, cleanNumber, myPhone);
        logBridge(`[Outbound Audio] Sending voice note to ${jid}`);

        if (sock && connectionState === 'open') {
            let buffer;
            if (audio.startsWith('data:')) {
                buffer = Buffer.from(audio.split(',')[1], 'base64');
            } else if (audio.length > 500 && !audio.startsWith('http')) {
                buffer = Buffer.from(audio, 'base64');
            } else {
                buffer = { url: audio };
            }

            const sent = await sock.sendMessage(jid, {
                audio: buffer,
                mimetype: 'audio/mp4',
                ptt: true,
            });
            if (sent?.key?.id) {
                botSentMessageIds.add(sent.key.id);
            }
            return res.json({ status: 'SUCCESS', key: sent.key });
        } else {
            return res.json({ status: 'MOCKED', warning: 'WhatsApp socket not open' });
        }
    } catch (err) {
        console.error('[Error sending audio]:', err.message);
        return res.status(500).json({ error: err.message });
    }
});

app.listen(PORT, () => {
    console.log(`============================================================`);
    console.log(`AwaazLedger WhatsApp Bridge running on http://localhost:${PORT}`);
    console.log(`Forwarding inbound webhooks to: ${WEBHOOK_URL}`);
    console.log(`============================================================`);
    startWhatsApp();
});
