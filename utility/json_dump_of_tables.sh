SCHEMA="public"
DB="openunited"
CURRENT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

EXPORT_DIR="$CURRENT_DIR/export"
mkdir -p $EXPORT_DIR
EXPORT_DIR="$EXPORT_DIR/json"
mkdir -p $EXPORT_DIR

psql -Atc "select tablename from pg_tables where schemaname='$SCHEMA'" $DB |\
  while read TBL; do
    psql -d $DB -qAtX -c "select json_agg(t) FROM (SELECT * from $SCHEMA.$TBL) t;" -o $EXPORT_DIR/$TBL.json
  done


