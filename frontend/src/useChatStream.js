import { useCallback, useRef, useState } from 'react';

const API = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

/**
 * Reads the Server-Sent Events stream from POST /chat.
 * EventSource only supports GET, so we parse the stream from fetch() ourselves.
 */
export function useChatStream() {
  const [messages, setMessages] = useState([]);
  const [busy, setBusy] = useState(false);
  const abortRef = useRef(null);

  const patchLast = (fn) =>
    setMessages((m) => [...m.slice(0, -1), fn(m[m.length - 1])]);

  const ask = useCallback(async (question) => {
    abortRef.current?.abort();
    const ctrl = new AbortController();
    abortRef.current = ctrl;
    setBusy(true);
    setMessages((m) => [
      ...m,
      { role: 'user', text: question },
      { role: 'assistant', text: '', sources: [] },
    ]);

    try {
      const res = await fetch(`${API}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question }),
        signal: ctrl.signal,
      });
      if (!res.ok) throw new Error(`Server returned ${res.status}`);

      const reader = res.body.pipeThrough(new TextDecoderStream()).getReader();
      let buffer = '';
      for (;;) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += value;
        const events = buffer.split('\n\n');
        buffer = events.pop(); // keep any partial event for the next read
        for (const raw of events) {
          const event = raw.match(/^event: (.*)$/m)?.[1];
          const data = JSON.parse(raw.match(/^data: (.*)$/m)?.[1] ?? 'null');
          if (event === 'sources') patchLast((msg) => ({ ...msg, sources: data }));
          if (event === 'token') patchLast((msg) => ({ ...msg, text: msg.text + data }));
          if (event === 'error') patchLast((msg) => ({ ...msg, error: data }));
        }
      }
    } catch (err) {
      if (err.name !== 'AbortError') patchLast((msg) => ({ ...msg, error: err.message }));
    } finally {
      setBusy(false);
    }
  }, []);

  const stop = useCallback(() => abortRef.current?.abort(), []);

  return { messages, busy, ask, stop };
}
