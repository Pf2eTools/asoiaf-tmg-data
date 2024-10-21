rm -f "rev-list.txt"
find ./generated ./portraits ./custom/generated/cmon-prerelease ./custom/portraits/cmon-prerelease -type f | \
while read -r file
do
  echo $file $(git rev-list -1 --remotes=origin HEAD $file) | tee -a "rev-list.txt"
done
