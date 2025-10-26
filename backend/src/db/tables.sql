DROP TABLE IF EXISTS likes;
DROP TABLE IF EXISTS youtube_current_recs;
DROP TABLE IF EXISTS item_features;
DROP TABLE IF EXISTS project_features;
DROP TABLE IF EXISTS youtube;
DROP TABLE IF EXISTS paperauthors;
DROP TABLE IF EXISTS authors;
DROP TABLE IF EXISTS papers;
DROP TABLE IF EXISTS queries;
DROP TABLE IF EXISTS project;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
	user_id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    email VARCHAR(255) NOT NULL
);

CREATE TABLE project ( 
    project_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    topic VARCHAR(255) NOT NULL,
    objective TEXT,
    guidelines TEXT,
    embedding VECTOR(1536)
);

CREATE TABLE queries (
    query_id SERIAL PRIMARY KEY,
    project_id INT NOT NULL REFERENCES project(project_id) ON DELETE CASCADE,
    queries_text TEXT,
    special_instructions TEXT
);

CREATE TABLE papers (
    paper_id SERIAL PRIMARY KEY,
    project_id INT NOT NULL REFERENCES project(project_id) ON DELETE CASCADE,
    query_id INT REFERENCES queries(query_id) ON DELETE SET NULL,
    paper_title VARCHAR(255) NOT NULL,
    paper_summary TEXT,
    published_year INT,
    pdf_link VARCHAR(100)
);

CREATE TABLE authors (
    author_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL
);

CREATE TABLE paperauthors (
    paper_id INT REFERENCES papers(paper_id) ON DELETE CASCADE,
    author_id INT REFERENCES authors(author_id) ON DELETE CASCADE,
    PRIMARY KEY (paper_id, author_id)
);

CREATE TABLE youtube (
    youtube_id SERIAL PRIMARY KEY,
    project_id INT NOT NULL REFERENCES project(project_id) ON DELETE CASCADE,
    query_id INT REFERENCES queries(query_id) ON DELETE SET NULL,
    video_title VARCHAR(255) NOT NULL,
    video_description TEXT,
    video_duration TIME,
    video_url VARCHAR(500),
    video_views BIGINT DEFAULT 0,   
    video_likes BIGINT DEFAULT 0,
    video_embedding VECTOR(1536)
);

-- Staging area for per-project recommendation candidates (15 at a time)
CREATE TABLE youtube_current_recs (
    rec_id SERIAL PRIMARY KEY,
    project_id INT NOT NULL REFERENCES project(project_id) ON DELETE CASCADE,
    video_title VARCHAR(255) NOT NULL,
    video_description TEXT,
    video_duration TIME,
    video_url VARCHAR(500),
    video_views BIGINT DEFAULT 0,
    video_likes BIGINT DEFAULT 0,
    score DOUBLE PRECISION DEFAULT 0,
    rank_position INT,
    video_embedding VECTOR(1536),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Feature stores for Jaccard
CREATE TABLE project_features (
    project_id INT NOT NULL REFERENCES project(project_id) ON DELETE CASCADE,
    feature VARCHAR(255) NOT NULL,
    PRIMARY KEY (project_id, feature)
);

CREATE TABLE item_features (
    target_type VARCHAR(20) CHECK (target_type IN ('youtube', 'paper')),
    target_id INT NOT NULL,
    feature VARCHAR(255) NOT NULL,
    PRIMARY KEY (target_type, target_id, feature)
);

CREATE TABLE likes (
    liked_disliked_id SERIAL PRIMARY KEY,
    project_id INT NOT NULL REFERENCES project(project_id) ON DELETE CASCADE,
    target_type VARCHAR(20) CHECK (target_type IN ('youtube', 'paper')),
    target_id INT NOT NULL,
    isLiked BOOLEAN NOT NULL
);