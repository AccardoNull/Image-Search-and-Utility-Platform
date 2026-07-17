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
  const [uploadFile, setUploadFile] = useState(null);
  const [uploadFormat, setUploadFormat] = useState("png");
  const [uploadDownloadUrl, setUploadDownloadUrl] = useState("");
  const [onlineQuery, setOnlineQuery] = useState("");
  const [onlineResults, setOnlineResults] = useState([]);
  const [onlinePage, setOnlinePage] = useState(0);
  const [onlineHasNext, setOnlineHasNext] = useState(false);
  const [onlineLoading, setOnlineLoading] = useState(false);
  const [onlineError, setOnlineError] = useState("");

  const [onlineConvertedFiles, setOnlineConvertedFiles] = useState({});
  const [onlineConversionMessages, setOnlineConversionMessages] = useState({});

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

async function uploadAndConvertImage() {
  if (!uploadFile) {
    alert("Please choose an image file first.");
    return;
  }

  const formData = new FormData();
  formData.append("file", uploadFile);
  formData.append("output_format", uploadFormat);

  const response = await fetch(`${API_BASE_URL}/upload-convert`, {
    method: "POST",
    body: formData,
  });

  const data = await response.json();

  if (data.status === "success") {
    setUploadDownloadUrl(data.download_url);
  } else {
    alert(data.error || "Upload conversion failed.");
  }
}

async function searchOnlineImages(page = 0) {
  const cleanedQuery = onlineQuery.trim();

  if (!cleanedQuery) {
    setOnlineError("Enter an online image search query.");
    return;
  }

  setOnlineLoading(true);
  setOnlineError("");

  try {
    const response = await fetch(
      `${API_BASE_URL}/search-online` +
      `?q=${encodeURIComponent(cleanedQuery)}` +
      `&page=${page}`
    );

    const data = await response.json();

    if (!response.ok) {
      throw new Error(
        data.detail || "Online image search failed."
      );
    }

    setOnlineResults(data.results ?? []);
    setOnlinePage(data.page ?? page);
    setOnlineHasNext(Boolean(data.has_next));

    setOnlineConvertedFiles({});
    setOnlineConversionMessages({});
  } catch (error) {
    setOnlineResults([]);
    setOnlineHasNext(false);
    setOnlineError(error.message);
  } finally {
    setOnlineLoading(false);
  }
}

async function handleSearch() {
  if (searchSource === "local") {
    await searchImages();
    setOnlineResults([]);
    return;
  }

  if (searchSource === "online") {
    setSearchResults([]);
    await searchOnlineImages(0);
    return;
  }

  await Promise.all([
    searchImages(),
    searchOnlineImages(0),
  ]);
}

async function convertOnlineImage(image, outputFormat) {
  setOnlineConversionMessages((previous) => ({
    ...previous,
    [image.id]: "Downloading and converting...",
  }));

  setOnlineConvertedFiles((previous) => {
    const updated = { ...previous };
    delete updated[image.id];
    return updated;
  });

  try {
    const response = await fetch(
      `${API_BASE_URL}/convert-online-image`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          image_url: image.full_url,
          output_format: outputFormat,
        }),
      }
    );

    const data = await response.json();

    if (!response.ok) {
      throw new Error(
        data.detail || "Online image conversion failed."
      );
    }

    setOnlineConvertedFiles((previous) => ({
      ...previous,
      [image.id]: data.download_url,
    }));

    setOnlineConversionMessages((previous) => ({
      ...previous,
      [image.id]: "Conversion complete.",
    }));

  } catch (error) {
    setOnlineConversionMessages((previous) => ({
      ...previous,
      [image.id]: error.message,
    }));
  }
}

  return (
    <div className="container">
      <h1>Image Search & Utility Platform</h1>
      <hr />

      <h2>KMP Visualizer</h2>

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

     <section className="search-section">
     <h2>Local Image Search</h2>
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
    </section>
     <section className="search-section online-search-section">
      <h2>Online Image Search</h2>

      <div className="search-controls">
        <input
          type="text"
          value={onlineQuery}
          onChange={(event) => setOnlineQuery(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter") {
              searchOnlineImages(0);
            }
          }}
          placeholder="Search Google Images..."
        />

        <button
          type="button"
          onClick={() => searchOnlineImages(0)}
          disabled={onlineLoading}
        >
          {onlineLoading ? "Searching..." : "Search Online"}
        </button>
      </div>

      {onlineLoading && <p>Searching online...</p>}

      {onlineError && (
        <p className="error-message">
          {onlineError}
        </p>
      )}

      <div className="image-grid">
        {onlineResults.map((image) => (
          <article key={image.id} className="image-card">
            <a
              href={image.full_url}
              target="_blank"
              rel="noopener noreferrer"
            >
              <img
                src={image.thumbnail_url}
                alt={image.title || "Online image"}
                loading="lazy"
              />
            </a>

            <h3>{image.title}</h3>

            {image.source_name && (
              <p className="image-description">
                Source: {image.source_name}
              </p>
            )}

            {image.width && image.height && (
              <p className="image-description">
                {image.width} × {image.height}
              </p>
            )}

            {image.source_page && (
              <a
                href={image.source_page}
                target="_blank"
                rel="noopener noreferrer"
              >
                Open source page
              </a>
            )}

            <div className="converter-controls">
              <select
                defaultValue=""
                onChange={(event) => {
                  const format = event.target.value;

                  if (format) {
                    convertOnlineImage(image, format);
                  }
                }}
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

              {onlineConversionMessages[image.id] && (
                <p className="image-description">
                  {onlineConversionMessages[image.id]}
                </p>
              )}

              {onlineConvertedFiles[image.id] && (
                <a
                  href={`${API_BASE_URL}${onlineConvertedFiles[image.id]}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  download
                >
                  Download converted image
                </a>
              )}
            </div>
          </article>
        ))}
      </div>

      {onlineResults.length > 0 && (
        <div className="pagination-controls">
          <button
            type="button"
            disabled={onlineLoading || onlinePage === 0}
            onClick={() => searchOnlineImages(onlinePage - 1)}
          >
            Previous
          </button>

          <span>Page {onlinePage + 1}</span>

          <button
            type="button"
            disabled={onlineLoading || !onlineHasNext}
            onClick={() => searchOnlineImages(onlinePage + 1)}
          >
            Next
          </button>
        </div>
      )}
    </section>
     <hr />

     <h2>Image Format Converter</h2>

     <input
       type="file"
       accept="image/*"
       onChange={(e) => {
         setUploadFile(e.target.files[0]);
         setUploadDownloadUrl("");
       }}
     />

     <select
       value={uploadFormat}
       onChange={(e) => setUploadFormat(e.target.value)}
     >
       <option value="png">PNG</option>
       <option value="jpg">JPG</option>
       <option value="webp">WEBP</option>
       <option value="ico">ICO</option>
       <option value="pdf">PDF</option>
     </select>

     <button onClick={uploadAndConvertImage}>
       Convert Uploaded Image
     </button>

     {uploadDownloadUrl && (
       <a
         href={`${API_BASE_URL}${uploadDownloadUrl}`}
         target="_blank"
         rel="noopener noreferrer"
         download
       >
         Download Converted Image
       </a>
     )}
    </div>
     
  );
}

export default App;