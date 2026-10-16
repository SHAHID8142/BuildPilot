run_timeout() {
  local secs="$1"; shift
  local out_file="$1"; shift
  "$@" >"$out_file" 2>&1 &
  local cmd_pid=$!
  ( sleep "$secs"; kill -TERM "$cmd_pid" 2>/dev/null; sleep 2; kill -KILL "$cmd_pid" 2>/dev/null ) >/dev/null 2>&1 &
  local watch_pid=$!
  wait "$cmd_pid" 2>/dev/null; local rc=$?
  kill -TERM "$watch_pid" 2>/dev/null; wait "$watch_pid" 2>/dev/null
  return $rc
}
run_timeout 90 .test.out claude plugin list
echo "exit code: $?"
cat .test.out
