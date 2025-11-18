set positional-arguments

test *args:
    uv run --isolated --with-editable '.[test]' pytest "$@"

datasette *args:
    uv run --isolated \
      --with-editable '.[test]' \
      datasette "$@" \
