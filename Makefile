install:
\tpython -m pip install -r requirements.txt

run:
\tpython -m core.pipeline

run-local:
\tpython -m core.pipeline --skip-postgres

test:
\tpytest -q

dashboard:
\tstreamlit run dashboard/app.py

docker-run:
\tdocker compose up --build
