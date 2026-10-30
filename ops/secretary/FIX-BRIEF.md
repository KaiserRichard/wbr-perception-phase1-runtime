# Fix brief (codex-k)

Problem (MEASURED on 30 Oct, 15:24): `digest.sh afternoon` exited 0, but `out/digest-2026-10-30-afternoon.md` held only
agy's 7-line meta-note ("Digest is ready for your review..."), not the digest. Earlier attempts also failed with
"listen tcp 127.0.0.1:0: bind: operation not permitted" (sandbox).

Fix:
1. Make agy return the digest text itself on stdout. For example, tell it in the prompt to output ONLY the Markdown and not to
   write files, and/or use the right agy print/mode flags (check `agy --help`); otherwise capture any file it wrote.
2. Add a check: fail if the output is under 20 lines or lacks the required section headers.
3. Document the sandbox bind error and that the script must run outside the Codex sandbox.
Test once for real. Commit on the current branch and push it (`git push -u origin HEAD`). If the push fails,
leave the commit and say so.
