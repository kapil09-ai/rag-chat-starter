import { useState } from 'react';
import { useChatStream } from './useChatStream.js';

const EXAMPLES = ['How do I reset my password?', 'What is the API rate limit?', 'Can I get a refund?'];

export default function App() {
  const { messages, busy, ask, stop } = useChatStream();
  const [input, setInput] = useState('');

  const submit = (q) => {
    const question = (q ?? input).trim();
    if (!question || busy) return;
    setInput('');
    ask(question);
  };

  return (
    <main className="shell">
      <header>
        <h1>RAG Chat Starter</h1>
        <p>Ask about the sample docs. Answers stream in with the passages they came from.</p>
      </header>

      <section className="log" aria-live="polite">
        {messages.length === 0 && (
          <div className="examples">
            {EXAMPLES.map((e) => (
              <button key={e} onClick={() => submit(e)}>{e}</button>
            ))}
          </div>
        )}
        {messages.map((m, i) => (
          <article key={i} className={`msg ${m.role}`}>
            <p>{m.text || (m.role === 'assistant' && busy ? '…' : '')}</p>
            {m.error && <p className="error">Error: {m.error}</p>}
            {m.sources?.length > 0 && (
              <ul className="sources">
                {m.sources.map((s) => (
                  <li key={s.n}>[{s.n}] {s.source} · {s.heading}</li>
                ))}
              </ul>
            )}
          </article>
        ))}
      </section>

      <form onSubmit={(e) => { e.preventDefault(); submit(); }}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question…"
          aria-label="Question"
        />
        {busy
          ? <button type="button" onClick={stop}>Stop</button>
          : <button type="submit" disabled={!input.trim()}>Send</button>}
      </form>
    </main>
  );
}
