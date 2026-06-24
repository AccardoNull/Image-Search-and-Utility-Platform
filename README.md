# Interactive-Algorithm-Visualizer-Image-Search-Platform
## Overview
An interactive full-stack web application that visualizes KMP algorithm execution step-by-step to help users understand complex computational processes and utilizes the algorithm's string matching function for quick local image file search. The long-term goal of the platform is to support additional algorithms including DFA simulation and graph traversal algorithms (BFS/DFS), as well as external image search API integration.

## Completed features
### KMP visualizer

a Knuth-Morris-Pratt (KMP) string matching visualizer that demonstrates pattern searching, prefix table construction, and character-by-character comparisons through an intuitive graphical interface.

Built with a React frontend and FastAPI backend, the application generates detailed execution traces that allow users to navigate algorithm states, inspect internal variables, and observe how algorithm decisions evolve over time. The project aims to make fundamental computer science concepts more accessible through interactive visualization and real-time feedback.

#### Features
- Step-by-step visualization of the KMP string matching algorithm
- Interactive text and pattern comparison highlighting
- Dynamic LPS (Longest Prefix Suffix) table construction display
- Forward and backward navigation through algorithm execution states
- FastAPI backend that generates structured execution traces
- React-based frontend with real-time visualization updates
- Automated testing and continuous integration using GitHub Actions

#### Screenshots
![screenshot1](ImageFolder/Screenshot1.jpg)
![screenshot2](ImageFolder/Screenshot2.jpg)
![screenshot3](ImageFolder/Screenshot3.jpg)

### Image File Search Framework

An interactive full-stack search application that enables users to locate images files using keyword-based pattern matching across filenames, tags, and descriptive metadata. The framework leverages the Knuth-Morris-Pratt (KMP) string matching algorithm to efficiently identify relevant records and return searchable results through a responsive graphical interface.

Built with a React frontend and FastAPI backend, the application automatically indexes image assets, extracts searchable metadata from filenames, and generates a structured search database for efficient retrieval. User queries are processed through a custom search engine that performs pattern matching against indexed file records and displays matching images with associated metadata. The project aims to bridge algorithmic pattern matching with practical search engine functionality while providing a foundation for future enhancements such as local file indexing, metadata extraction, AI-generated image captions, and desktop search capabilities.

#### Features

- Keyword-based image file search using the KMP string matching algorithm
- Automated image indexing pipeline that scans directories and generates searchable metadata records
- Search across filenames, tags, descriptions, and indexed file metadata
- Interactive image gallery with real-time search results and metadata display
- Clickable image previews and filenames that link directly to original image assets and open file locations
- FastAPI backend for search processing, indexing, and metadata retrieval
- React-based frontend with dynamic query submission and result rendering
- Static asset serving for image storage and retrieval
- Automated testing and continuous integration using GitHub Actions

#### Current Architecture

```text
Image Directory
       │
       ▼
Automated Indexing Script
       │
       ▼
Searchable Metadata Database (JSON)
       │
       ▼
FastAPI Search API
       │
       ▼
React Search Interface
```

#### Screenshots
![screenshot4](ImageFolder/Screenshot4.jpg)
![screenshot5](ImageFolder/Screenshot5.jpg)
![screenshot6](ImageFolder/Screenshot6.jpg)

## Tech Stack

Frontend
- React
- Vite
- JavaScript
- Node.js

Backend
- Python
- FastAPI
- REST APIs
- Uvicorn

Development Tools
- GitHub/GitHub Actions
- VS Code
- Git
- Pytest