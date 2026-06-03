import { useState } from "react";

function App() {
  const [query, setQuery] = useState("");
  const [answer, setAnswer] = useState("");

  const askQuestion = async () => {
    const response = await fetch("http://127.0.0.1:8000/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        query: query,
      }),
    });

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

      <button onClick={askQuestion}>
        Ask
      </button>

      <p>{answer}</p>
    </div>
  );
}

export default App;