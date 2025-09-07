# MemoScholar

Allow users to gather resources for their research and studies. 
See full techspec here: https://docs.google.com/document/d/1EDiuOM7pzMlwyO4g-ZQU2VtMs2yAtt-3llWDrcgQpJQ/edit?usp=sharing

## Prerequisites
- **Node.js**: Download here: https://nodejs.org/en (node -v >= 22.19.0, npm -v >= 11.6.0)
- **Python**: Python 3.8+ with pip

## Quick Start

1. **Clone and install all dependencies:**
   ```bash
   git clone <your-repo>
   cd MemoScholar
   npm run install:all
   ```

2. **Run both frontend and backend:**
   ```bash
   npm run dev
   ```

3. **Open your browser:**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:5000


## Notes
- The app uses Tailwind CSS and shadcn/ui. All CSS tooling is already configured in this repo (Tailwind, PostCSS, Autoprefixer). After a fresh clone, only `npm install` is required.