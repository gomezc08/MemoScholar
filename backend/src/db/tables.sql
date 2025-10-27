-- Drop in FK-safe order
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

-- Users
CREATE TABLE users (
  user_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  name    TEXT NOT NULL,
  email   VARCHAR(255) NOT NULL
); 

-- Project
CREATE TABLE project (
  project_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  user_id    BIGINT UNSIGNED NOT NULL,
  topic      VARCHAR(255) NOT NULL,
  objective  TEXT,
  guidelines TEXT,
  embedding  VECTOR(1536),
  FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
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
  video_embedding   VECTOR(1536),
  FOREIGN KEY (project_id) REFERENCES project(project_id) ON DELETE CASCADE,
  FOREIGN KEY (query_id)   REFERENCES queries(query_id)  ON DELETE SET NULL
);

-- Staging area for per-project recommendation candidates (15 at a time)
CREATE TABLE youtube_current_recs (
  rec_id          BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  project_id      BIGINT UNSIGNED NOT NULL,
  video_title     VARCHAR(255) NOT NULL,
  video_description TEXT,
  video_duration  TIME,
  video_url       VARCHAR(500),
  video_views     BIGINT DEFAULT 0,
  video_likes     BIGINT DEFAULT 0,
  score           DOUBLE PRECISION DEFAULT 0,
  rank_position   INT,
  video_embedding VECTOR(1536),
  created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (project_id) REFERENCES project(project_id) ON DELETE CASCADE
);

-- Feature stores for Jaccard
CREATE TABLE project_features (
  project_id BIGINT UNSIGNED NOT NULL,
  feature    VARCHAR(255) NOT NULL,
  PRIMARY KEY (project_id, feature),
  INDEX idx_pf_project_id (project_id),
  FOREIGN KEY (project_id) REFERENCES project(project_id) ON DELETE CASCADE
);

CREATE TABLE item_features (
  target_type VARCHAR(20) CHECK (target_type IN ('youtube', 'paper')),
  target_id   BIGINT UNSIGNED NOT NULL,  -- must match youtube_id/paper_id
  feature     VARCHAR(255) NOT NULL,
  PRIMARY KEY (target_type, target_id, feature)
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