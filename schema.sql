CREATE TABLE IF NOT EXISTS videos (id STRING PRIMARY KEY, 
                                   title STRING,
                                   description STRING,
                                   channel STRING,
                                   publishDate BIGINT,
                                   thumbnail STRING,
                                   duration FLOAT);

CREATE VIRTUAL TABLE IF NOT EXISTS [videos_fts] USING FTS5 (
    [title], [description], [id],
    content=[videos]
)
/* videos_fts(title,description,id) */;
CREATE TABLE IF NOT EXISTS 'videos_fts_data'(id INTEGER PRIMARY KEY, block BLOB);
CREATE TABLE IF NOT EXISTS 'videos_fts_idx'(segid, term, pgno, PRIMARY KEY(segid, term)) WITHOUT ROWID;
CREATE TABLE IF NOT EXISTS 'videos_fts_docsize'(id INTEGER PRIMARY KEY, sz BLOB);
CREATE TABLE IF NOT EXISTS 'videos_fts_config'(k PRIMARY KEY, v) WITHOUT ROWID;
CREATE TRIGGER IF NOT EXISTS[videos_ai] AFTER INSERT ON [videos] BEGIN
  INSERT INTO [videos_fts] (rowid, [title], [description], [id]) VALUES (new.rowid, new.[title], new.[description], new.[id]);
END;
CREATE TRIGGER IF NOT EXISTS [videos_ad] AFTER DELETE ON [videos] BEGIN
  INSERT INTO [videos_fts] ([videos_fts], rowid, [title], [description], [id]) VALUES('delete', old.rowid, old.[title], old.[description], old.[id]);
END;
CREATE TRIGGER IF NOT EXISTS [videos_au] AFTER UPDATE ON [videos] BEGIN
  INSERT INTO [videos_fts] ([videos_fts], rowid, [title], [description], [id]) VALUES('delete', old.rowid, old.[title], old.[description], old.[id]);
  INSERT INTO [videos_fts] (rowid, [title], [description], [id]) VALUES (new.rowid, new.[title], new.[description], new.[id]);
END;