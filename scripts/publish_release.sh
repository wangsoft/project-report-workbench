#!/usr/bin/env bash
# Run after tests, from the repository root. Requires Git, gh, Python, and sha256sum.
set -euo pipefail

version=$(tr -d '\r\n' < VERSION)
if [[ ! "$version" =~ ^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$ ]]; then
  echo 'VERSION must contain a stable semantic version.' >&2
  exit 1
fi
export RELEASE_TAG="v$version"
notes="release-notes/$RELEASE_TAG.md"
test -s "$notes"
commit=$(git rev-parse HEAD)
if [[ -n "$(git status --porcelain)" ]]; then
  echo 'Release requires a clean working tree.' >&2
  exit 1
fi

# A failed API request must stop publication, rather than masquerade as a missing release.
state=$(gh api --paginate --slurp "repos/$GH_REPO/releases" | python3 -c '
import json, os, sys
releases = [r for page in json.load(sys.stdin) for r in page]
r = next((r for r in releases if r["tag_name"] == os.environ["RELEASE_TAG"]), None)
print("missing" if r is None else "draft" if r["draft"] else "published")
')
if [[ "$state" == published ]]; then
  echo "$RELEASE_TAG is already published; increment VERSION for a new release."
  exit 0
fi
if [[ "$state" == draft ]]; then
  target=$(gh release view "$RELEASE_TAG" --json targetCommitish --jq .targetCommitish)
  if [[ "$target" != "$commit" ]]; then
    echo 'Existing draft targets a different commit; resolve it before retrying.' >&2
    exit 1
  fi
fi

# Never attach artifacts from a different commit to an existing tag.
git fetch origin --tags
if git rev-parse --verify "refs/tags/$RELEASE_TAG" >/dev/null 2>&1; then
  test "$(git rev-parse "$RELEASE_TAG^{commit}")" = "$commit" || {
    echo "$RELEASE_TAG points to a different commit." >&2
    exit 1
  }
fi

output=$(mktemp -d)
trap 'rm -rf "$output"' EXIT
name="project-report-workbench-$version"
git archive --format=tar.gz --prefix="$name/" -o "$output/$name.tar.gz" "$commit"
git archive --format=zip --prefix="$name/" -o "$output/$name.zip" "$commit"
(cd "$output" && sha256sum "$name.tar.gz" "$name.zip" > SHA256SUMS)

# Keep partial uploads private; rerunning resumes an existing draft.
if [[ "$state" == missing ]]; then
  gh release create "$RELEASE_TAG" --target "$commit" --draft \
    --title "$RELEASE_TAG — Project Report Workbench" --notes-file "$notes"
fi
gh release upload "$RELEASE_TAG" "$output/$name.tar.gz" "$output/$name.zip" \
  "$output/SHA256SUMS" --clobber
gh release edit "$RELEASE_TAG" --draft=false

gh release view "$RELEASE_TAG" --json url,isDraft,tagName
