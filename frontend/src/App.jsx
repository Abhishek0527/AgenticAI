import { useState } from "react";

function App() {
  const [query, setQuery] = useState("");
  const [answer, setAnswer] = useState("");
  const [source, setSource] = useState("jira");
  const [citations, setCitations] = useState(null);

  const askQuestion = async () => {
    const response = await fetch(
      "http://127.0.0.1:8000/chat",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          query: query,
          source: source,
        }),
      }
    );

    const data = await response.json();

    setAnswer(data.response);
    setCitations(data.citations);
  };

  return (
  <div className="app">
    <div className="chat-container">

      <h1>AI SDLC</h1>

      <div className="input-section">

        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask a question..."
        />

        <select
          value={source}
          onChange={(e) => setSource(e.target.value)}
        >
          {/* <option value="react.pdf">React</option>
          <option value="langgraph.pdf">LangGraph</option> */}
          <option value="jira">Jira</option>
          <option value="confluence">Confluence</option>
        </select>

        <button onClick={askQuestion}>
          Ask
        </button>

      </div>

      {query && (
        <div className="user-message">
          {query}
        </div>
      )}

      {answer && (
        <div className="bot-message">

          <h3>Answer</h3>

          <p>{answer}</p>

          {citations && (
            <div className="citations">

              <h4>
                Knowledge Fabric Context
              </h4>

              {citations.primary?.length > 0 && (
                <div className="citation-group">
                  <strong>Primary</strong>

                  {citations.primary.map(
                    (item, index) => (
                      <div
                        key={index}
                        className="citation-card"
                      >
                        {item.title}
                      </div>
                    )
                  )}
                </div>
              )}

              {citations.parents?.length > 0 && (
                <div className="citation-group">
                  <strong>Parent Context</strong>

                  {citations.parents.map(
                    (item, index) => (
                      <div
                        key={index}
                        className="citation-card"
                      >
                        {item}
                      </div>
                    )
                  )}
                </div>
              )}

              {citations.children?.length > 0 && (
                <div className="citation-group">
                  <strong>Child Context</strong>

                  {citations.children.map(
                    (item, index) => (
                      <div
                        key={index}
                        className="citation-card"
                      >
                        {item}
                      </div>
                    )
                  )}
                </div>
              )}

            </div>
          )}

        </div>
      )}

    </div>
  </div>
  );
}

export default App;