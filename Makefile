.PHONY: setup data pipeline test dashboard

setup:
	python -m pip install -r requirements.txt

data:
	python src/generate_data.py
	python src/prepare_data.py

pipeline:
	python src/run_pipeline.py

test:
	python -m unittest discover -s tests -v

dashboard:
	streamlit run dashboard/app.py
