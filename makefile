.PHONY: test init-db run serve lint

test:
	pytest tests/ -v

# создать БД и таблицы (один раз)
init-db:
	python -c "from app.db.session import init_db; init_db()"

run:
	uvicorn app.main:app --reload

serve:
	gunicorn -c gunicorn.conf.py app.main:app

lint:
	ruff check .
