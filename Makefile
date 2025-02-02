.PHONY: install


install:
	mkdir -p data
	sqlite3 data/podcasts.db < schema.sql
