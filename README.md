# Image-Search-and-Utility-Platform/Algorithm Visualizer
## Overview
An interactive full-stack web application that started as a visualizer showcases KMP algorithm execution step-by-step to help users understand complex computational processes, then evolved into a platform that utilizes the algorithm's string matching function for efficient local/external image file search and conversion. The long-term goal of the platform is to implenment more image utility functions, as well as support visualization of additional algorithms.

## Demo
Live Demo: https://interactive-algorithm-visualizer-im.vercel.app/  
- The local image search function on live website is currently limited to the sample images stored in the repository, under backend/static/images.

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
- Automated testing and continuous integration using Pytest, Git and GitHub Actions

#### Screenshots
![screenshot1](ImageFolder/Screenshot1.jpg)
![screenshot2](ImageFolder/Screenshot2.jpg)
![screenshot3](ImageFolder/Screenshot3.jpg)

### Image Search and Utility Platform

An interactive full-stack application that enables users to perform local/online image search using keyword-based pattern matching across filenames, tags, and descriptive metadata, and convert the search results/upload images to selected formats. The framework leverages the Knuth-Morris-Pratt (KMP) string matching algorithm to efficiently identify relevant records and return searchable results through a responsive graphical interface.

Built with a React frontend and FastAPI backend, the application automatically indexes image assets and generates a structured search database for efficient retrieval, with format conversions done through Pillow library. The app is also Dockerized and deployed to cloud platgforms Railway and Vercel, and integrated with external image search APIs using SerpApi for online search functionality. User queries are processed through a custom search engine that performs pattern matching against indexed file records and displays matching images with associated metadata. 

The project aims to bridge algorithmic pattern matching with practical search engine functionality while providing a foundation for future enhancements such as image resizing/compression, AI-generated image captions, and desktop search capabilities.

#### Features

- Keyword-based image file search using the KMP string matching algorithm across filenames, tags, descriptions, and indexed file metadata
  - Added a token-based search layer for fuzzy matching. KMP powers exact substring matching, while the search layer handles tokenization, ranking, and flexible query matching.
  - Integrated external image search APIs for broader image retrieval, with security features including backend-only API key management, temporary downloads/cleanup , URL/content-type validation, and file size limits.
- FastAPI backend for search processing, indexing, and metadata retrieval
- React-based frontend with dynamic query submission and result rendering
- Static asset serving for image storage and retrieval
- Automated image indexing pipeline that scans directories and generates searchable metadata records
- Interactive image gallery with real-time search results and metadata display
- Clickable image previews and filenames that link directly to original image assets through custom FastAPI preview and open file locations through Windows Explorer integration
  - Added a custom FastAPI preview route to serve image assets with inline display headers for consistent browser preview behavior across JPG, PNG, and WebP files.
  - Windows Explorer integration is only supported in local Windows execution mode, while Dockerized/live demo supports KMP visualization, image search, and preview.
- Format conversion options for uploaded files and search results using Pillow
- Automated testing and continuous integration using Pytest, Git, and GitHub Actions

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
##### local image search:  
![screenshot4](ImageFolder/Screenshot4.jpg)  
##### Online image search:  
![screenshot5](ImageFolder/Screenshot5.jpg)  
##### Image format converte:  
![screenshot6](ImageFolder/Screenshot6.jpg)

## Local Setup
### Activate frontend and backend servers
Local Windows execution mode 
- cd backend
  - .\\.venv\Scripts\Activate.ps1
    - uvicorn main:app --reload
- cd frontend
  - npm run dev  
Docker
- docker compose up --build

### Local image metadata indexing
Store images under backend/static/images, then run:
- cd backend
  - py index_images.py

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
- Pillow
- SerpApi

Development Tools
- GitHub/GitHub Actions
- VS Code
- Git
- Pytest
- Docker

Cloud deployment
- Vercel
- Railway