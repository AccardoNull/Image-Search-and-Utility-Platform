import { useState } from "react";
import "./App.css";

function App() {
  const [text, setText] = useState("ABABDABACDABABCABAB");
  const [pattern, setPattern] = useState("ABABCABAB");
  const [steps, setSteps] = useState([]);
  const [currentStep, setCurrentStep] = useState(0);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState([]);
  const [resultCount, setResultCount] = useState(0);

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

  async function searchImages() {
  const response = await fetch(
    `http://127.0.0.1:8000/search?q=${encodeURIComponent(searchQuery)}`
  );

  const data = await response.json();

  setSearchResults(data.results);
  setResultCount(data.count);
}

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
      <hr />

     <h2>Image Search</h2>

     <input
       value={searchQuery}
       onChange={(e) => setSearchQuery(e.target.value)}
       placeholder="Search images by filename, tag, or description"
     />

     <button onClick={searchImages}>Search</button>

     <p>{resultCount} result(s) found</p>

     <div className="image-grid">
       {searchResults.map((image) => (
         <div key={image.id} className="image-card">
           <img
             src={`http://127.0.0.1:8000${image.url}`}
             alt={image.description}
           />

           <h3>{image.filename}</h3>
           <p>{image.description}</p>

           <div>
            {image.tags.map((tag) => (
               <span key={tag} className="tag">
                 {tag}
               </span>
             ))}
           </div>
         </div>
       ))}
     </div>
    </div> 
  );
}

export default App;