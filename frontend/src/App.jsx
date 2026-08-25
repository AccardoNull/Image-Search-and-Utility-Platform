import { useRef, useState } from "react";
import "./App.css";

function App() {

  const folderInputRef = useRef(null);
  const [activeTab, setActiveTab] = useState("online");
  const [text, setText] = useState("ABABDABACDABABCABAB");
  const [pattern, setPattern] = useState("ABABCABAB");
  const [steps, setSteps] = useState([]);
  const [currentStep, setCurrentStep] = useState(0);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState([]);
  const [resultCount, setResultCount] = useState(0);
  const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  "http://localhost:8000";
  const [convertedFiles, setConvertedFiles] = useState({});
  const [uploadFile, setUploadFile] = useState(null);
  const [uploadFormat, setUploadFormat] = useState("png");
  const [uploadDownloadUrl, setUploadDownloadUrl] = useState("");
  const [localPage, setLocalPage] = useState(0);
  const LOCAL_RESULTS_PER_PAGE = 12;
  const [onlineQuery, setOnlineQuery] = useState("");
  const [onlineResults, setOnlineResults] = useState([]);
  const [onlinePage, setOnlinePage] = useState(0);
  const [onlineHasNext, setOnlineHasNext] = useState(false);
  const [onlineLoading, setOnlineLoading] = useState(false);
  const [onlineError, setOnlineError] = useState("");

  const [onlineConvertedFiles, setOnlineConvertedFiles] = useState({});
  const [onlineConversionMessages, setOnlineConversionMessages] = useState({});

  const [folderSessionId, setFolderSessionId] = useState("");
  const [indexedImageCount, setIndexedImageCount] = useState(0);
  const [isUploadingFolder, setIsUploadingFolder] = useState(false);
  const [isSearchingFolder, setIsSearchingFolder] = useState(false);
  const [folderUploadProgress, setFolderUploadProgress] = useState("");
  const [folderError, setFolderError] = useState("");

  const SUPPORTED_IMAGE_TYPES = new Set([
  "image/jpeg",
  "image/png",
  "image/webp",
  "image/gif",
  "image/bmp",
  "image/tiff",
  "image/x-icon",
]);

  const MAX_FILES = 250;
  const MAX_FILE_SIZE = 10 * 1024 * 1024;
  const MAX_TOTAL_SIZE = 200 * 1024 * 1024;

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
  const cleanedQuery = searchQuery.trim();

  if (!folderSessionId) {
    setFolderError(
      "Select and upload an image folder first.",
    );
    return;
  }

  if (!cleanedQuery) {
    setFolderError("Enter a search term.");
    return;
  }

  setFolderError("");
  setIsSearchingFolder(true);

  try {
    const params = new URLSearchParams({
      q: cleanedQuery,
      session_id: folderSessionId,
    });

    const response = await fetch(
      `${API_BASE_URL}/search?${params.toString()}`,
    );

    const data = await response.json();

    if (!response.ok) {
      throw new Error(
        data.detail || "Local image search failed.",
      );
    }

    setSearchResults(data.results ?? []);
    setResultCount(data.count ?? 0);
    setLocalPage(0);
    setConvertedFiles({});
  } catch (error) {
    setSearchResults([]);
    setResultCount(0);

    setFolderError(
      error instanceof Error
        ? error.message
        : "Unable to search the uploaded folder.",
    );
  } finally {
    setIsSearchingFolder(false);
  }
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
  try {
    const response = await fetch(
      `${API_BASE_URL}/convert-image`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          session_id: folderSessionId,
          relative_path: image.relative_path,
          output_format: outputFormat,
        }),
      },
    );

    const data = await response.json();

    if (!response.ok) {
      throw new Error(
        data.detail ||
          data.error ||
          "Conversion failed.",
      );
    }

    setConvertedFiles((previous) => ({
      ...previous,
      [image.id]: data.download_url,
    }));
  } catch (error) {
    setFolderError(
      error instanceof Error
        ? error.message
        : "Image conversion failed.",
    );
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

async function handleFolderUpload(event) {
  const selectedFiles = Array.from(
    event.target.files || [],
  );

  setFolderError("");
  setSearchResults([]);
  setResultCount(0);
  setLocalPage(0);
  setConvertedFiles({});
  setIndexedImageCount(0);

  const imageFiles = selectedFiles.filter((file) =>
    SUPPORTED_IMAGE_TYPES.has(file.type),
  );

  if (imageFiles.length === 0) {
    setFolderError(
      "The selected folder contains no supported images.",
    );
    return;
  }

  if (imageFiles.length > MAX_FILES) {
    setFolderError(
      `Select no more than ${MAX_FILES} images.`,
    );
    return;
  }

  const oversizedFile = imageFiles.find(
    (file) => file.size > MAX_FILE_SIZE,
  );

  if (oversizedFile) {
    setFolderError(
      `${oversizedFile.name} exceeds the 10 MB limit.`,
    );
    return;
  }

  const totalSize = imageFiles.reduce(
    (sum, file) => sum + file.size,
    0,
  );

  if (totalSize > MAX_TOTAL_SIZE) {
    setFolderError(
      "The selected folder exceeds the 200 MB limit.",
    );
    return;
  }

  const sessionId = crypto.randomUUID();
  const formData = new FormData();

  formData.append("session_id", sessionId);

  for (const file of imageFiles) {
    formData.append("files", file);
    formData.append(
      "relative_paths",
      file.webkitRelativePath || file.name,
    );
  }

  setIsUploadingFolder(true);
  setFolderUploadProgress(
    `Uploading and indexing ${imageFiles.length} images...`,
  );

  try {
    const response = await fetch(
      `${API_BASE_URL}/upload-folder`,
      {
        method: "POST",
        body: formData,
      },
    );

    const data = await response.json();

    if (!response.ok) {
      throw new Error(
        data.detail || "Folder upload failed.",
      );
    }

    setFolderSessionId(data.session_id);
    setIndexedImageCount(data.indexed_count);
    setFolderUploadProgress(
      `${data.indexed_count} images indexed and ready to search.`,
    );
  } catch (error) {
    setFolderSessionId("");
    setFolderError(
      error instanceof Error
        ? error.message
        : "Unable to upload the selected folder.",
    );
  } finally {
    setIsUploadingFolder(false);
  }
}

async function clearUploadedFolder() {
  if (folderSessionId) {
    try {
      await fetch(
        `${API_BASE_URL}/uploaded-folder/${folderSessionId}`,
        {
          method: "DELETE",
        },
      );
    } catch (error) {
      console.error(
        "Unable to clean up upload session:",
        error,
      );
    }
  }

  setFolderSessionId("");
  setIndexedImageCount(0);
  setSearchQuery("");
  setSearchResults([]);
  setResultCount(0);
  setLocalPage(0);
  setConvertedFiles({});
  setFolderUploadProgress("");
  setFolderError("");

  if (folderInputRef.current) {
    folderInputRef.current.value = "";
  }
}

const localStartIndex =
  localPage * LOCAL_RESULTS_PER_PAGE;

const localEndIndex =
  localStartIndex + LOCAL_RESULTS_PER_PAGE;

const paginatedLocalResults =
  searchResults.slice(
    localStartIndex,
    localEndIndex
  );

const localHasNext =
  localEndIndex < searchResults.length;

  return (
    <div className="container">
      <h1>Image Search & Utility Platform</h1>
      <nav className="toolbar">
        <button
          className={activeTab === "online" ? "active-tab" : ""}
          onClick={() => setActiveTab("online")}
        >
          Online Search
        </button>

        <button
          className={activeTab === "local" ? "active-tab" : ""}
          onClick={() => setActiveTab("local")}
        >
          Local Search
        </button>

        <button
          className={activeTab === "converter" ? "active-tab" : ""}
          onClick={() => setActiveTab("converter")}
        >
          Format Converter
        </button>

        <button
          className={activeTab === "kmp" ? "active-tab" : ""}
          onClick={() => setActiveTab("kmp")}
        >
          Algorithm Visualizer
        </button>
      </nav>
      <hr />
      {activeTab === "kmp" && (
      <>
      <h2>KMP Algorithm Visualizer</h2>

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
      </>
      )}

     {activeTab === "local" && (
  <>
    <h2>Local Image Search</h2>

    <div className="folder-upload-controls">
      <label className="folder-upload-button">
        Select Image Folder

        <input
          ref={folderInputRef}
          type="file"
          accept="image/*"
          multiple
          webkitdirectory=""
          directory=""
          onChange={handleFolderUpload}
          disabled={isUploadingFolder}
        />
      </label>

      {folderSessionId && (
        <button
          type="button"
          onClick={clearUploadedFolder}
          disabled={isUploadingFolder}
        >
          Clear Folder
        </button>
      )}
    </div>

    {isUploadingFolder && (
      <p>{folderUploadProgress}</p>
    )}

    {!isUploadingFolder &&
      indexedImageCount > 0 && (
        <p>
          {indexedImageCount} images indexed and ready
          to search
        </p>
      )}

    {folderError && (
      <p className="error-message">
        {folderError}
      </p>
    )}

    <div className="search-controls">
      <input
        value={searchQuery}
        onChange={(event) =>
          setSearchQuery(event.target.value)
        }
        onKeyDown={(event) => {
          if (event.key === "Enter") {
            searchImages();
          }
        }}
        placeholder="Search by filename, folder, tag, or description"
        disabled={
          !folderSessionId ||
          isUploadingFolder ||
          isSearchingFolder
        }
      />

      <button
        type="button"
        onClick={searchImages}
        disabled={
          !folderSessionId ||
          isUploadingFolder ||
          isSearchingFolder
        }
      >
        {isSearchingFolder
          ? "Searching..."
          : "Search"}
      </button>
    </div>

    {folderSessionId && (
      <p>{resultCount} result(s) found</p>
    )}

{searchResults.length > 0 && (
  <div className="pagination-controls">
    <button
      type="button"
      disabled={localPage === 0}
      onClick={() =>
        setLocalPage((previous) => previous - 1)
      }
    >
      Previous
    </button>

    <span>Page {localPage + 1}</span>

    <button
      type="button"
      disabled={!localHasNext}
      onClick={() =>
        setLocalPage((previous) => previous + 1)
      }
    >
      Next
    </button>
  </div>
)}

    <div className="image-grid">
      {paginatedLocalResults.map((image) => (
        <article
          key={image.id}
          className="image-card"
        >
          <a
            href={`${API_BASE_URL}${image.url}`}
            target="_blank"
            rel="noopener noreferrer"
          >
            <img
              src={`${API_BASE_URL}${image.url}`}
              alt={
                image.description ||
                image.filename
              }
              loading="lazy"
            />
          </a>

          <h3 className="image-filename">
            <a
              href={`${API_BASE_URL}${image.url}`}
              target="_blank"
              rel="noopener noreferrer"
            >
              {image.filename}
            </a>
          </h3>

          {image.description && (
            <p className="image-description">
              {image.description}
            </p>
          )}

          {image.relative_path && (
            <p className="image-description">
              {image.relative_path}
            </p>
          )}

          {Array.isArray(image.tags) &&
            image.tags.length > 0 && (
              <div>
                {image.tags.map((tag) => (
                  <span
                    key={tag}
                    className="tag"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            )}

          <div className="converter-controls">
            <select
              defaultValue=""
              onChange={(event) => {
                const outputFormat =
                  event.target.value;

                if (outputFormat) {
                  convertImage(
                    image,
                    outputFormat,
                  );
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
        </article>
      ))}
    </div>
{searchResults.length > 0 && (
  <div className="pagination-controls">
    <button
      type="button"
      disabled={localPage === 0}
      onClick={() =>
        setLocalPage((previous) => previous - 1)
      }
    >
      Previous
    </button>

    <span>Page {localPage + 1}</span>

    <button
      type="button"
      disabled={!localHasNext}
      onClick={() =>
        setLocalPage((previous) => previous + 1)
      }
    >
      Next
    </button>
  </div>
)}
  </>
)}
      {activeTab === "online" && (
      <>
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

      <div className="image-grid">
        {onlineResults.map((image) => (
          <article key={image.id} className="image-card">
           <a
             href={
               `${API_BASE_URL}/preview-online?url=` +
               encodeURIComponent(image.full_url)
             }
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
     </>
      )}

     {activeTab === "converter" && (
     <> 
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
     </>
     )}
    </div>
  );
}

export default App;