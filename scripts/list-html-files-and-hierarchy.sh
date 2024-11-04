find . \( -path ./env -o -path "*/__pycache__" \) -prune -o -type f -name "*.html" -exec dirname {} \; | sort -u | while read dir; do
  echo "$dir"
  tree "$dir" -P "*.html" --prune
done
