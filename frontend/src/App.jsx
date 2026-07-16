import { useState } from "react";

const prompts = [
  "Summarize the latest project status",
  "What decisions are documented in Confluence?",
  "Find risks related to the current sprint",
];

function App() {
  const [query, setQuery] = useState("");
  const [answer, setAnswer] = useState("");
  const [citations, setCitations] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  const askQuestion = async (event) => {
    event?.preventDefault();
    const question = query.trim();

    if (!question || isLoading) return;

    setIsLoading(true);
    setError("");
    setAnswer("");
    setCitations(null);

    try {
      const response = await fetch("http://127.0.0.1:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: question }),
      });

      if (!response.ok) throw new Error("The assistant is temporarily unavailable.");

      const data = await response.json();
      setAnswer(data.response || "I couldn't find an answer for that question.");
      setCitations(data.citations || null);
    } catch (requestError) {
      setError(requestError.message || "Something went wrong. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="app-shell">
      <header className="topbar">
        <a className="brand" href="#top" aria-label="AI SDLC home">
          <span className="brand-mark" aria-hidden="true">
            <svg viewBox="0 0 32 32" fill="none">
              <path d="M7 11.5 16 6l9 5.5v9L16 26l-9-5.5v-9Z" fill="currentColor" opacity=".18" />
              <path d="m7 11.5 9 5.2 9-5.2M16 16.7V26M7 11.5 16 6l9 5.5v9L16 26l-9-5.5v-9Z" stroke="currentColor" strokeWidth="2" strokeLinejoin="round" />
              <circle cx="16" cy="16.5" r="2.5" fill="currentColor" />
            </svg>
          </span>
          <span>AI SDLC</span>
        </a>
        <div className="secure-status"><span aria-hidden="true">●</span> Secure workspace</div>
      </header>

      <section className="chat-page" id="top">
        <div className="intro">
          <p className="eyebrow">KNOWLEDGE ASSISTANT</p>
          <h1>Make every project decision easier.</h1>
          <p className="intro-copy">Search your connected Jira, Confluence, and document knowledge in one thoughtful conversation.</p>
        </div>

        <section className="chat-card" aria-label="AI SDLC assistant">
          <div className="chat-card-header">
            <div>
              <p className="section-label">ASK AI SDLC</p>
              <h2>How can I help today?</h2>
            </div>
            <span className="online-indicator"><i /> Online</span>
          </div>

          <form className="input-section" onSubmit={askQuestion}>
            <label className="sr-only" htmlFor="question">Your question</label>
            <input
              id="question"
              type="text"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Ask about Jira, Confluence, or PDFs..."
              disabled={isLoading}
            />
            <button type="submit" disabled={!query.trim() || isLoading}>
              {isLoading ? "Thinking..." : "Ask AI"}
              {!isLoading && <span aria-hidden="true">→</span>}
            </button>
          </form>

          {/* {!answer && !isLoading && !error && (
            <div className="prompt-list" aria-label="Suggested questions">
              <span>Try asking:</span>
              {prompts.map((prompt) => (
                <button className="prompt-chip" type="button" key={prompt} onClick={() => setQuery(prompt)}>
                  {prompt}
                </button>
              ))}
            </div>
          )} */}

          {query && (
            <div className="message user-message">
              <span className="message-label">YOU</span>
              <p>{query}</p>
            </div>
          )}

          {isLoading && <div className="message loading-message"><span className="loading-dot" /><span className="loading-dot" /><span className="loading-dot" /></div>}
          {error && <p className="error-message" role="alert">{error}</p>}

          {answer && (
            <article className="message bot-message">
              <div className="assistant-heading">
                <span className="assistant-icon">AI</span>
                <div><span className="message-label">AI SDLC</span><h3>Answer</h3></div>
              </div>
              <p>{answer}</p>

              {citations && (
                <section className="citations">
                  <h4>Sources used</h4>
                  {citations.primary?.length > 0 && <CitationGroup label="Primary context" items={citations.primary} getText={(item) => item.title} />}
                  {citations.parents?.length > 0 && <CitationGroup label="Related context" items={citations.parents} />}
                  {citations.children?.length > 0 && <CitationGroup label="Supporting context" items={citations.children} />}
                  {citations.linked?.length > 0 && <CitationGroup label="Linked context" items={citations.linked} />}
                </section>
              )}
            </article>
          )}
        </section>
        <p className="disclaimer">AI-generated answers may be incomplete. Verify important project decisions with the source material.</p>
      </section>
    </main>
  );
}

function CitationGroup({ label, items, getText = (item) => item }) {
  return <div className="citation-group"><strong>{label}</strong><div className="citation-list">{items.map((item, index) => <div key={index} className="citation-card">{getText(item)}</div>)}</div></div>;
}

export default App;