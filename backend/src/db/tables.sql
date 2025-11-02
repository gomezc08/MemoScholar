-- Drop in FK-safe order
DROP TABLE IF EXISTS likes;
DROP TABLE IF EXISTS youtube_has_rec;
DROP TABLE IF EXISTS youtube_features;
DROP TABLE IF EXISTS youtube_embeddings;
DROP TABLE IF EXISTS youtube;
DROP TABLE IF EXISTS paperauthors;
DROP TABLE IF EXISTS authors;
DROP TABLE IF EXISTS papers;
DROP TABLE IF EXISTS queries;
DROP TABLE IF EXISTS project_embeddings;
DROP TABLE IF EXISTS project;
DROP TABLE IF EXISTS users;

-- Users
CREATE TABLE users (
  user_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  name    TEXT NOT NULL,
  email   VARCHAR(255) NOT NULL
); 

-- Projects
CREATE TABLE project (
  project_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  user_id    BIGINT UNSIGNED NOT NULL,
  topic      VARCHAR(255) NOT NULL,
  objective  TEXT,
  guidelines TEXT,
  FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Project Embeddings
CREATE TABLE project_embeddings (
	project_embedding_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    project_id BIGINT UNSIGNED NOT NULL,
    embedding  VECTOR(1536),
    FOREIGN KEY (project_id) REFERENCES project(project_id) ON DELETE CASCADE
);

-- Queries
CREATE TABLE queries (
  query_id            BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  project_id          BIGINT UNSIGNED NOT NULL,
  queries_text        TEXT,
  special_instructions TEXT,
  FOREIGN KEY (project_id) REFERENCES project(project_id) ON DELETE CASCADE
);

-- Papers
CREATE TABLE papers (
  paper_id      BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  project_id    BIGINT UNSIGNED NOT NULL,
  query_id      BIGINT UNSIGNED NULL,
  paper_title   VARCHAR(255) NOT NULL,
  paper_summary TEXT,
  published_year INT,
  pdf_link      VARCHAR(100),
  FOREIGN KEY (project_id) REFERENCES project(project_id) ON DELETE CASCADE,
  FOREIGN KEY (query_id) REFERENCES queries(query_id) ON DELETE SET NULL
);

-- Authors
CREATE TABLE authors (
  author_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  name      VARCHAR(255) NOT NULL
);

-- PaperAuthors (junction)
CREATE TABLE paperauthors (
  paper_id  BIGINT UNSIGNED NOT NULL,
  author_id BIGINT UNSIGNED NOT NULL,
  PRIMARY KEY (paper_id, author_id),
  FOREIGN KEY (paper_id)  REFERENCES papers(paper_id)   ON DELETE CASCADE,
  FOREIGN KEY (author_id) REFERENCES authors(author_id) ON DELETE CASCADE
);

-- YouTube
CREATE TABLE youtube (
  youtube_id        BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  project_id        BIGINT UNSIGNED NOT NULL,
  query_id          BIGINT UNSIGNED NULL,
  video_title       VARCHAR(255) NOT NULL,
  video_description TEXT,
  video_duration    TIME,
  video_url         VARCHAR(500),
  video_views       BIGINT DEFAULT 0,
  video_likes       BIGINT DEFAULT 0,
  FOREIGN KEY (project_id) REFERENCES project(project_id) ON DELETE CASCADE,
  FOREIGN KEY (query_id)   REFERENCES queries(query_id)  ON DELETE SET NULL
);

CREATE TABLE youtube_has_rec (
	youtube_has_rec_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    youtube_id BIGINT UNSIGNED NOT NULL,
    hasBeenRecommended BOOLEAN NOT NULL,
    FOREIGN KEY (youtube_id) REFERENCES youtube(youtube_id) ON DELETE CASCADE
);

-- Project Embeddings
CREATE TABLE youtube_embeddings (
	youtube_embedding_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    project_id BIGINT UNSIGNED NOT NULL,
    embedding  VECTOR(1536),
    FOREIGN KEY (project_id) REFERENCES project(project_id) ON DELETE CASCADE
);

-- YouTube Feautures
CREATE TABLE youtube_features (
	youtube_feature_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    youtube_id         BIGINT UNSIGNED NOT NULL,
    category           ENUM('dur','fresh','pop','type','tok','kp','emb') NOT NULL,
    feature            VARCHAR(64) NOT NULL,
    FOREIGN KEY (youtube_id) REFERENCES youtube(youtube_id) ON DELETE CASCADE
);

-- Likes
CREATE TABLE likes (
  liked_disliked_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  project_id        BIGINT UNSIGNED NOT NULL,
  target_type       VARCHAR(20) CHECK (target_type IN ('youtube', 'paper')),
  target_id         BIGINT UNSIGNED NOT NULL,
  isLiked           BOOLEAN NOT NULL,
  FOREIGN KEY (project_id) REFERENCES project(project_id) ON DELETE CASCADE
);