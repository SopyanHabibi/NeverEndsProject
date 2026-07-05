import * as http from 'http';
import { VscodeAskPayload, NeiraStreamCallbacks } from '../types/neiraTypes';

const NEIRA_HOST = 'localhost';
const NEIRA_PORT = 5000;

export function askNeiraStream(
  payload: VscodeAskPayload,
  callbacks: NeiraStreamCallbacks
): void {
  const body = JSON.stringify(payload);

  const req = http.request(
    {
      hostname: NEIRA_HOST,
      port: NEIRA_PORT,
      path: '/api/vscode/ask',
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(body)
      }
    },
    res => {
      res.setEncoding('utf8');
      let buffer = '';

      res.on('data', chunk => {
        buffer += chunk;
        const events = buffer.split('\n\n');
        buffer = events.pop() || '';

        for (const rawEvent of events) {
          handleSseEvent(rawEvent, callbacks);
        }
      });

      res.on('end', () => {
        if (buffer) {
          handleSseEvent(buffer, callbacks);
        }
        callbacks.onComplete?.();
      });
    }
  );

  req.on('error', err => {
    callbacks.onError?.(err.message);
  });

  req.write(body);
  req.end();
}

function handleSseEvent(rawEvent: string, callbacks: NeiraStreamCallbacks): void {
  const line = rawEvent.trim();
  if (!line.startsWith('data:')) {
    return;
  }

  const content = line.slice('data:'.length).trim();

  const sessionMatch = content.match(/^\[SESSION_ID_ASSIGNED:(\d+)\]$/);
  if (sessionMatch) {
    callbacks.onSessionAssigned?.(parseInt(sessionMatch[1], 10));
    return;
  }

  try {
    const parsed = JSON.parse(content);
    if (parsed.text !== undefined) {
      const token = parsed.text.replace(/\[NEWLINE\]/g, '\n');
      callbacks.onToken(token);
    }
  } catch {
    // baris SSE kosong/parsial, aman diabaikan
  }
}