DROP TABLE IF EXISTS likes;
DROP TABLE IF EXISTS rec_impressions;
DROP TABLE IF EXISTS youtube;
DROP TABLE IF EXISTS paperauthors;
DROP TABLE IF EXISTS authors;
DROP TABLE IF EXISTS papers;
DROP TABLE IF EXISTS queries;
DROP TABLE IF EXISTS project_features;
DROP TABLE IF EXISTS item_features;
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
    guidelines TEXT
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
    pdf_link VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_papers_project (project_id),
    INDEX idx_papers_url (pdf_link),
    INDEX idx_papers_year (published_year),
    INDEX idx_papers_created (created_at)
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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_youtube_project (project_id),
    INDEX idx_youtube_url (video_url(191)),
    INDEX idx_youtube_engagement (video_views, video_likes),
    INDEX idx_youtube_created (created_at)
);

CREATE TABLE likes (
    liked_disliked_id SERIAL PRIMARY KEY,
    project_id INT NOT NULL REFERENCES project(project_id) ON DELETE CASCADE,
    target_type VARCHAR(20) CHECK (target_type IN ('youtube', 'paper')),
    target_id INT NOT NULL,
    isLiked BOOLEAN NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uniq_like (project_id, target_type, target_id),
    INDEX idx_likes_project (project_id),
    INDEX idx_likes_target (target_type, target_id),
    INDEX idx_likes_created (created_at)
);

-- ===========================================================
-- ✅ New tables for the recommendation system (feature storage)
-- ===========================================================

-- Project features: match project.project_id (SERIAL => BIGINT UNSIGNED)
CREATE TABLE project_features (
  project_id BIGINT UNSIGNED NOT NULL,
  feature VARCHAR(191) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_project_features_project
    FOREIGN KEY (project_id) REFERENCES project(project_id)
    ON DELETE CASCADE,
  UNIQUE KEY uniq_project_feature (project_id, feature)
) ENGINE=InnoDB;

CREATE INDEX idx_project_features_project ON project_features(project_id);
CREATE INDEX idx_project_features_feature  ON project_features(feature);
CREATE INDEX idx_project_features_created ON project_features(created_at);

-- Item features (no FK needed; these reference either youtube or papers)
CREATE TABLE item_features (
  target_type VARCHAR(20) NOT NULL CHECK (target_type IN ('youtube','paper')),
  target_id   BIGINT UNSIGNED NOT NULL,   -- use BIGINT to be safe with SERIAL ids
  feature     VARCHAR(191) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uniq_item_feature (target_type, target_id, feature)
) ENGINE=InnoDB;

CREATE INDEX idx_item_features_target ON item_features(target_type, target_id);
CREATE INDEX idx_item_features_feature ON item_features(feature);
CREATE INDEX idx_item_features_created ON item_features(created_at);
CREATE INDEX idx_item_features_composite ON item_features(target_type, feature, target_id);

CREATE TABLE rec_impressions (
  id SERIAL PRIMARY KEY,
  project_id BIGINT UNSIGNED NOT NULL,
  target_type VARCHAR(20) NOT NULL CHECK (target_type IN ('youtube','paper')),
  target_id   BIGINT UNSIGNED NOT NULL,
  impression_ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uniq_proj_target (project_id, target_type, target_id),
  INDEX idx_impressions_project_ts (project_id, impression_ts),
  INDEX idx_impressions_target (target_type, target_id)
) ENGINE=InnoDB;
