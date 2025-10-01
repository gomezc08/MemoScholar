DROP TABLE IF EXISTS Likes;
DROP TABLE IF EXISTS Youtube;
DROP TABLE IF EXISTS PaperAuthors;
DROP TABLE IF EXISTS Authors;
DROP TABLE IF EXISTS Papers;
DROP TABLE IF EXISTS Project;

CREATE TABLE Project (
    project_id SERIAL PRIMARY KEY,
    topic VARCHAR(255) NOT NULL,
    objective TEXT,
    guidelines TEXT
);

CREATE TABLE Papers (
    paper_id SERIAL PRIMARY KEY,
    project_id INT NOT NULL REFERENCES Project(project_id) ON DELETE CASCADE,
    paper_title VARCHAR(255) NOT NULL,
    paper_summary TEXT,
    published_year INT,
    Pdf_link VARCHAR(100)
);

CREATE TABLE Authors (
    author_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL
);

CREATE TABLE PaperAuthors (
    paper_id INT REFERENCES Papers(paper_id) ON DELETE CASCADE,
    author_id INT REFERENCES Authors(author_id) ON DELETE CASCADE,
    PRIMARY KEY (paper_id, author_id)
);

CREATE TABLE Youtube (
    youtube_id SERIAL PRIMARY KEY,
    project_id INT NOT NULL REFERENCES Project(project_id) ON DELETE CASCADE,
    video_title VARCHAR(255) NOT NULL,
    video_description TEXT,
    video_duration TIME,
    video_url VARCHAR(500),
    video_views BIGINT DEFAULT 0,   
    video_likes BIGINT DEFAULT 0
);

CREATE TABLE Likes (
    liked_disliked_id SERIAL PRIMARY KEY,
    project_id INT NOT NULL REFERENCES Project(project_id) ON DELETE CASCADE,
    target_type VARCHAR(20) CHECK (target_type IN ('youtube', 'paper')),
    target_id INT NOT NULL,
    isLiked BOOLEAN NOT NULL
);