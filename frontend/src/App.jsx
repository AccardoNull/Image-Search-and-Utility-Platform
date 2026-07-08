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
  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;
  const [convertedFiles, setConvertedFiles] = useState({});

  async function runKMP() {
    const response = await fetch(`${API_BASE_URL}/kmp`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ 
        text: text, 
        pattern: pattern,
      }),
    });

    const data = await response.json();
    setSteps(data.steps);
    setCurrentStep(0);
  }

  const step = steps[currentStep];

  async function searchImages() {
  const response = await fetch(
    `${API_BASE_URL}/search?q=${encodeURIComponent(searchQuery)}`
  );

  const data = await response.json();

  setSearchResults(data.results);
  setResultCount(data.count);
}

  async function openFileLocation(filepath) {
  await fetch(`${API_BASE_URL}/open-file`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      filepath: filepath,
    }),
  });
}

  async function convertImage(image, outputFormat) {
  const response = await fetch(`${API_BASE_URL}/convert-image`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      filename: image.filename,
      output_format: outputFormat,
    }),
  });

  const data = await response.json();

  if (data.status === "success") {
    setConvertedFiles((prev) => ({
      ...prev,
      [image.id]: data.download_url,
    }));
  } else {
    alert(data.error || "Conversion failed");
  }
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

     <h1>Image Search</h1>

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
           <a
            href={`${API_BASE_URL}/preview/${image.filename}`}
            target="_blank"
            rel="noopener noreferrer"
          >
            <img
              src={`${API_BASE_URL}${image.url}`}
              alt={image.description}
            />
          </a>

           <h3 className="image-filename"
               style={{cursor: "pointer"}}
               onClick={() => openFileLocation(image.filepath)}>
               {image.filename}
           </h3>
           <p className="image-description">
               {image.description}
           </p>

           <div>
            {image.tags.map((tag) => (
               <span key={tag} className="tag">
                 {tag}
               </span>
             ))}
           </div>
           <div className="converter-controls">
            <select
              onChange={(e) => {
               if (e.target.value) {
                  convertImage(image, e.target.value);
                }
              }}
              defaultValue=""
            >
              <option value="" disabled>
                Convert to...
              </option>
              <option value="png">PNG</option>
              <option value="jpg">JPG</option>
              <option value="webp">WEBP</option>
              <option value="ico">ICO</option>
              <option value="pdf">PDF</option>
           </select>

           {convertedFiles[image.id] && (
              <a
                href={`${API_BASE_URL}${convertedFiles[image.id]}`}
                target="_blank"
                rel="noopener noreferrer"
                download
              >
                Download converted file
              </a>
            )}
          </div>
         </div>
       ))}
     </div>
    </div> 
  );
}

export default App;