CREATE TABLE IF NOT EXISTS  podcasts (
  id TEXT PRIMARY KEY,
  url TEXT NOT NULL,
  title TEXT NOT NULL,
  author TEXT NOT NULL,
  description TEXT NULL,
  image_url TEXT NULL
);
