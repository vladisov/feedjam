/**
 * Cloudflare Email Worker for FeedJam
 *
 * This worker receives emails via Cloudflare Email Routing and forwards
 * them to the FeedJam API webhook for processing.
 *
 * Setup:
 * 1. Deploy this worker to Cloudflare Workers
 * 2. Configure Email Routing for in.feedjam.app to send to this worker
 * 3. Set the WEBHOOK_URL and WEBHOOK_SECRET environment variables
 *
 * Environment variables:
 * - WEBHOOK_URL: The FeedJam API webhook URL (e.g., https://api.feedjam.app/webhooks/inbound-email)
 * - WEBHOOK_SECRET: Secret key for authenticating with the webhook
 */

export default {
  async email(message, env) {
    const webhookUrl = env.WEBHOOK_URL || "https://api.feedjam.app/webhooks/inbound-email";
    const webhookSecret = env.WEBHOOK_SECRET || "";

    try {
      // Read the raw email content
      const rawEmail = await this.streamToString(message.raw);

      // Parse the email
      const parsed = this.parseEmail(rawEmail, message);

      // Build the payload for our webhook
      const payload = {
        to: message.to,
        from_address: message.from,
        from_name: parsed.fromName,
        subject: parsed.subject,
        html: parsed.html,
        text: parsed.text,
        date: parsed.date,
      };

      // Send to webhook
      const response = await fetch(webhookUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Webhook-Secret": webhookSecret,
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error(`Webhook failed: ${response.status} ${errorText}`);
        // Still accept the email to avoid bounces
        message.setReject(false);
      } else {
        const result = await response.json();
        console.log(`Email processed: ${result.message}`);
      }
    } catch (error) {
      console.error(`Error processing email: ${error.message}`);
      // Accept the email even on error to prevent bounces
      message.setReject(false);
    }
  },

  /**
   * Convert a ReadableStream to a string
   */
  async streamToString(stream) {
    const reader = stream.getReader();
    const chunks = [];
    let done = false;

    while (!done) {
      const { value, done: readerDone } = await reader.read();
      done = readerDone;
      if (value) {
        chunks.push(value);
      }
    }

    // Combine all chunks into a single Uint8Array
    const totalLength = chunks.reduce((acc, chunk) => acc + chunk.length, 0);
    const combined = new Uint8Array(totalLength);
    let offset = 0;
    for (const chunk of chunks) {
      combined.set(chunk, offset);
      offset += chunk.length;
    }

    return new TextDecoder().decode(combined);
  },

  /**
   * Parse email content - simple parser for common email formats
   */
  parseEmail(rawEmail, message) {
    const result = {
      subject: "",
      fromName: null,
      html: null,
      text: null,
      date: null,
    };

    // Split headers and body
    const headerEndIndex = rawEmail.indexOf("\r\n\r\n");
    const headers = headerEndIndex > 0 ? rawEmail.substring(0, headerEndIndex) : rawEmail;
    const body = headerEndIndex > 0 ? rawEmail.substring(headerEndIndex + 4) : "";

    // Parse Subject header
    const subjectMatch = headers.match(/^Subject:\s*(.+?)(?:\r?\n(?!\s)|$)/im);
    if (subjectMatch) {
      result.subject = this.decodeHeader(subjectMatch[1].trim());
    }

    // Parse From header for display name
    const fromMatch = headers.match(/^From:\s*(.+?)(?:\r?\n(?!\s)|$)/im);
    if (fromMatch) {
      const fromValue = fromMatch[1].trim();
      // Extract name from "Name <email>" format
      const nameMatch = fromValue.match(/^"?([^"<]+)"?\s*<.*>/);
      if (nameMatch) {
        result.fromName = this.decodeHeader(nameMatch[1].trim());
      }
    }

    // Parse Date header
    const dateMatch = headers.match(/^Date:\s*(.+?)(?:\r?\n(?!\s)|$)/im);
    if (dateMatch) {
      try {
        result.date = new Date(dateMatch[1].trim()).toISOString();
      } catch {
        result.date = null;
      }
    }

    // Parse Content-Type for multipart handling
    const contentTypeMatch = headers.match(/^Content-Type:\s*(.+?)(?:\r?\n(?!\s)|$)/im);
    const contentType = contentTypeMatch ? contentTypeMatch[1].toLowerCase() : "text/plain";

    if (contentType.includes("multipart/")) {
      // Extract boundary
      const boundaryMatch = contentType.match(/boundary="?([^";\s]+)"?/i);
      if (boundaryMatch) {
        const boundary = boundaryMatch[1];
        const parts = this.parseMultipart(body, boundary);
        result.html = parts.html;
        result.text = parts.text;
      }
    } else if (contentType.includes("text/html")) {
      result.html = this.decodeBody(body, headers);
    } else {
      result.text = this.decodeBody(body, headers);
    }

    // Limit content size to prevent huge payloads
    const maxSize = 50000;
    if (result.html && result.html.length > maxSize) {
      result.html = result.html.substring(0, maxSize);
    }
    if (result.text && result.text.length > maxSize) {
      result.text = result.text.substring(0, maxSize);
    }

    return result;
  },

  /**
   * Parse multipart email body
   */
  parseMultipart(body, boundary) {
    const result = { html: null, text: null };
    const parts = body.split(`--${boundary}`);

    for (const part of parts) {
      if (part.trim() === "" || part.trim() === "--") continue;

      const partHeaderEnd = part.indexOf("\r\n\r\n");
      if (partHeaderEnd < 0) continue;

      const partHeaders = part.substring(0, partHeaderEnd);
      const partBody = part.substring(partHeaderEnd + 4);

      const partContentType = partHeaders.match(/Content-Type:\s*([^;\r\n]+)/i);
      const type = partContentType ? partContentType[1].toLowerCase() : "text/plain";

      const decoded = this.decodeBody(partBody, partHeaders);

      if (type.includes("text/html") && !result.html) {
        result.html = decoded;
      } else if (type.includes("text/plain") && !result.text) {
        result.text = decoded;
      }
    }

    return result;
  },

  /**
   * Decode email body based on Content-Transfer-Encoding
   */
  decodeBody(body, headers) {
    const encodingMatch = headers.match(/Content-Transfer-Encoding:\s*(\S+)/i);
    const encoding = encodingMatch ? encodingMatch[1].toLowerCase() : "7bit";

    let decoded = body;

    if (encoding === "base64") {
      try {
        decoded = atob(body.replace(/\s/g, ""));
      } catch {
        // If base64 decode fails, return as-is
      }
    } else if (encoding === "quoted-printable") {
      decoded = this.decodeQuotedPrintable(body);
    }

    return decoded.trim();
  },

  /**
   * Decode quoted-printable encoding
   */
  decodeQuotedPrintable(str) {
    return str
      .replace(/=\r?\n/g, "") // Remove soft line breaks
      .replace(/=([0-9A-Fa-f]{2})/g, (_, hex) => String.fromCharCode(parseInt(hex, 16)));
  },

  /**
   * Decode MIME encoded header values (=?charset?encoding?text?=)
   */
  decodeHeader(header) {
    return header.replace(/=\?([^?]+)\?([BQ])\?([^?]+)\?=/gi, (_, charset, encoding, text) => {
      try {
        if (encoding.toUpperCase() === "B") {
          return atob(text);
        } else if (encoding.toUpperCase() === "Q") {
          return this.decodeQuotedPrintable(text.replace(/_/g, " "));
        }
      } catch {
        return text;
      }
      return text;
    });
  },
};
