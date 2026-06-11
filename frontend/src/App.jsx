import { useState } from "react";

function App() {
  const [query, setQuery] = useState("");
  const [answer, setAnswer] = useState("");
  const [source, setSource] = useState("react.pdf");

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
  };

  return (
    <div>
      <h1>Agentic RAG</h1>

      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Ask a question"
      />

      <select
        value={source}
        onChange={(e) => setSource(e.target.value)}
      >
        <option value="react.pdf">
          React
        </option>

        {/* <option value="python.pdf">
          Python
        </option> */}

        <option value="langgraph.pdf">
          LangGraph
        </option>
        <option value="confluence">
          Confluence
        </option>
      </select>

      <button onClick={askQuestion}>
        Ask
      </button>

      <p>{answer}</p>
    </div>
  );
}

export default App;