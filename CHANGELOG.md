# automig changelog

## 0.0.x

* 0.0.9 bugfix: support jsonb and array types in alter parser
* 0.0.8 feature: drop & alter column
* 0.0.7 bugfix: --initial was broken by streams fix in 0.0.3
* 0.0.6 bugfix: ignore comments
* 0.0.5 bugfix: `search_parent_directories` so you don't have to run from repo root
* 0.0.4 bugfix: 0.0.3 didn't bundle VERSION file correctly, crashed on load
* 0.0.3
	- bugfix: `data_stream` property in gitpython throws funky traceback when created from more than one blob & then read; so read stream proactively
	- BROKEN, do not use
* 0.0.2 bugfix: treat newlines correctly as whitespace in create table stmts
* 0.0.1 initial release
