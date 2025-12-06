# MemoScholar

Allow users to gather resources for their research and studies. 
[See full techspec here](https://docs.google.com/document/d/1EDiuOM7pzMlwyO4g-ZQU2VtMs2yAtt-3llWDrcgQpJQ/edit?usp=sharing)

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


## Running the Collaborative Filtering Recommender

To train and evaluate the hybrid recommendation system (`citeulike_cf.py`), you need to download the citeulike-t dataset first.

### Downloading the Dataset

1. **Download the citeulike-t dataset:**
   - The dataset was used in the paper "Collaborative Topic Regression with Social Regularization" [Wang, Chen and Li]
   - You can find download links on the [paper's repository](http://wanghao.in/paper/IJCAI13_CTRSR.pdf) or check the [CiteULike dataset resources](http://www.citeulike.org/faq/data.adp)
   - Alternatively, search for "citeulike-t dataset CTRSR" for available download sources

2. **Extract and place the dataset:**
   - Create the directory `backend/src/cf_recommender/data-cite/` if it doesn't exist
   - Extract all dataset files into this directory
   - Required files: `users.dat`, `mult.dat`, `tags.dat`, `vocabulary.dat`, `citations.dat`, `tag-item.dat`, `rawtext.dat`

### Running the Script

Once the dataset is in place, run the recommendation system:

```bash
python backend/src/cf_recommender/citeulike_cf.py
```

The script will:
- Load and filter the data
- Train item-based collaborative filtering and content-based models
- Create a switched ensemble model
- Evaluate all models
- Display the results table with metrics (NDCG@10, Precision@10, Recall@10, Hit Rate@10)
- Save the trained model and metadata to `backend/src/cf_recommender/models/`

**Note:** The dataset directory (`backend/src/cf_recommender/data-cite/`) is already included in `.gitignore` to prevent committing large data files to the repository.

## Notes
- The app uses Tailwind CSS and shadcn/ui. All CSS tooling is already configured in this repo (Tailwind, PostCSS, Autoprefixer). After a fresh clone, only `npm install` is required.
