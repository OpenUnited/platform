SCHEMA="public"
DB="openunited"
CURRENT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

EXPORT_DIR="$CURRENT_DIR/export"
mkdir -p $EXPORT_DIR
EXPORT_DIR="$EXPORT_DIR/csv"
mkdir -p $EXPORT_DIR

psql -Atc "select tablename from pg_tables where schemaname='$SCHEMA'" $DB |\
  while read TBL; do
    psql -c "COPY $SCHEMA.$TBL TO '$EXPORT_DIR/$TBL.csv' DELIMITER ',' CSV HEADER;" $DB
  done


