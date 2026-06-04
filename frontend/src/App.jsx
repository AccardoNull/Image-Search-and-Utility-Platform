import { useState } from "react";
import "./App.css";

function App() {
  const [text, setText] = useState("ABABDABACDABABCABAB");
  const [pattern, setPattern] = useState("ABABCABAB");
  const [steps, setSteps] = useState([]);
  const [currentStep, setCurrentStep] = useState(0);

  async function runKMP() {
    const response = await fetch("http://127.0.0.1:8000/kmp", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ text, pattern }),
    });

    const data = await response.json();
    setSteps(data.steps);
    setCurrentStep(0);
  }

  const step = steps[currentStep];

  return (
    <div className="container">
      <h1>KMP Visualizer</h1>

      <label>Text:</label>
      <input value={text} onChange={(e) => setText(e.target.value)} />

      <label>Pattern:</label>
      <input value={pattern} onChange={(e) => setPattern(e.target.value)} />

      <button onClick={runKMP}>Run KMP</button>

      {step && (
        <>
          <h2>Step {currentStep + 1}</h2>
          <p>{step.message}</p>

          <div className="chars">
            {text.split("").map((char, index) => (
              <span
                key={index}
                className={step.phase === "search" && index === step.i ? "highlight" : ""}
              >
                {char}
              </span>
            ))}
          </div>

          <div className="chars">
            {pattern.split("").map((char, index) => (
              <span
                key={index}
                className={index === step.j ? "highlight" : ""}
              >
                {char}
              </span>
            ))}
          </div>

          <h3>LPS Table</h3>
          <div className="chars">
            {step.lps?.map((value, index) => (
              <span key={index}>{value}</span>
            ))}
          </div>

          <button
            onClick={() => setCurrentStep(Math.max(currentStep - 1, 0))}
          >
            Previous
          </button>

          <button
            onClick={() =>
              setCurrentStep(Math.min(currentStep + 1, steps.length - 1))
            }
          >
            Next
          </button>
        </>
      )}
    </div>
  );
}

export default App;