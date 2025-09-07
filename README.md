# MemoScholar

Allow users to gather resources for their research and studies. 
See full techspec here: https://docs.google.com/document/d/1EDiuOM7pzMlwyO4g-ZQU2VtMs2yAtt-3llWDrcgQpJQ/edit?usp=sharing

## Prerequisites

### Backend
Perform the following in the project root directory...
- `python -m venv venv_memo`
- After activating virtual environment, run `pip install -r .\requirements.txt`

### Frontend
- Download Node.js here: https://nodejs.org/en (node -v >= 22.19.0, npm -v >= 11.6.0)
- `cd frontend/memo-scholar`
- `npm install`


## Running server(s)
- **Frontend:** `cd frontend/memo-scholar`, then `npm run dev`
- **Backend:** `python .\backend\run_server.py`

Open the printed local URL in your browser.

## Build & Preview
`npm run build`
`npm run preview`

## Notes
- The app uses Tailwind CSS and shadcn/ui. All CSS tooling is already configured in this repo (Tailwind, PostCSS, Autoprefixer). After a fresh clone, only `npm install` is required.