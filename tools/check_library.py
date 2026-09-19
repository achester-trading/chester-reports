#!/usr/bin/env python3
"""The white paper library's gate.

WHY THIS EXISTS. The library's rules are all of the kind that a human keeps
correctly for a week and then stops keeping: cite papers by name because the
numerals were reassigned once and every in-text numeral broke; put the version
in the masthead and copy it to the guide, never the reverse; give each rule
namespace a prefix so "Rule 21" means one thing. Audit 1 found sixty-seven
stale numerals, five mastheads with no numeral, a guide header off by five
papers and forty thousand words, and two papers missing a part heading their
own prose referred to. None of that is hard to see; all of it is easy to stop
looking for.

Every check here is one of those rules. FAIL means the library is now wrong in
a way a reader would act on -- a figure a paper references and the repo does
not have, a numeral cited where a name belongs. WARN means something is
drifting and a human should decide: a built edition whose source has moved on
is one `make html` away from correct. INFO is neither -- it says a check
declined to look, which is only ever about a path git is told to ignore.

THE REGISTRY BELOW IS THE MAP FROM NUMERAL TO FILE. It is the one thing the
guide cannot supply (it names titles, not paths) and the filenames cannot
supply (a slug is not a numeral). Adding a paper to the library means adding
one line to it -- the same discipline as adding a validator to the Makefile or
a report key to state/emit.py:VALID_KEYS.
"""

import hashlib
import re
import subprocess
import sys
from pathlib import Path

# The authoring machine is Windows, whose console defaults to cp1252 and dies
# on the em dashes and section signs this library is full of.
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

ROOT = Path(__file__).resolve().parent.parent
PAPERS = ROOT / "docs" / "whitepapers"
GUIDE = ROOT / "docs" / "white-paper-library-guide.md"
CLAUDE = ROOT / "CLAUDE.md"
AGENTS = ROOT / "AGENTS.md"
HTML = ROOT / "docs" / "html"

# numeral -> filename slug. The registry of paper identities.
REGISTRY = {
    "I": "disruptive-themes", "II": "tail-scenarios", "III": "monthly-macro",
    "IV": "rates-liquidity", "V": "currencies", "VI": "credit", "VII": "energy",
    "VIII": "metals", "IX": "digital-assets", "X": "tops-and-bottoms",
    "XI": "volatility", "XII": "daily-cascade", "XIII": "dealers-hand",
    "XIV": "technical-indicators", "XV": "equities", "XVI": "positioning-and-flows",
    "XVII": "portfolio-construction", "XVIII": "operating-doctrine",
    "XIX": "systematic-book", "XX": "base-rates", "XXI": "international-equities",
    "XXII": "options-expression", "XXIII": "evidence-inference", "XXIV": "earnings",
    "XXV": "price-time-and-edge",
}

# D4: the two papers that own a dotted rule namespace, and the chapters whose
# rules belong to the Dealer's Hand rather than to the Daily Cascade.
DH_OWN_CHAPTERS = {18, 20, 21}

# Check 2: words that take a roman numeral for reasons that have nothing to do
# with the series, plus VIX, which is not a numeral at all but matches like one.
NUMERAL_OK = {
    "Part", "Chapter", "Factor", "Scenario", "Phase", "Gate", "Tier", "Book",
    "Family", "Era", "Lens", "Type", "Class", "Quadrant", "Ring", "Pillar",
    "VIX",
}

ROMAN = {r: i for i, r in enumerate(REGISTRY, start=1)}

fails: list[str] = []
warns: list[str] = []
infos: list[str] = []


def fail(check, msg):
    fails.append(f"[{check}] {msg}")


def warn(check, msg):
    warns.append(f"[{check}] {msg}")


def info(check, msg):
    infos.append(f"[{check}] {msg}")


def gitignored(paths):
    """Which of these paths git is told to ignore.

    Ask git rather than reimplementing its matching: the root .gitignore is
    not the only one in the tree, and the rules have negations and anchoring
    that a quick fnmatch gets wrong in exactly the cases worth getting right.
    If git is not on the box, nothing is reported ignored and the caller
    behaves as it did before -- erring toward checking a path, not skipping it.
    """
    if not paths:
        return set()
    try:
        done = subprocess.run(
            ["git", "-C", str(ROOT), "check-ignore", "-z", "--stdin"],
            input="\0".join(paths).encode("utf-8"),
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    except OSError:
        return set()
    return {s for s in done.stdout.decode("utf-8").split("\0") if s}


def source_sha256(path):
    """The fingerprint tools/build_paper_html.py stamps into a built edition.

    Kept in both files deliberately: this gate carries no third-party imports
    and the builder needs `markdown`, so importing one from the other would
    make the gate unrunnable wherever the builder is not installed. The
    duplication is self-policing -- if the two ever disagree, check 10 warns
    on all 24 editions at once.

    Line endings are normalised first: .gitattributes lets .md follow the
    platform, so the same paper is CRLF on the authoring Windows box and LF on
    Linux CI, and the raw bytes would fingerprint the checkout, not the paper.
    """
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def paper_files():
    """Every roster paper. archive/ and readme.md are not the roster."""
    return sorted(p for p in PAPERS.glob("*.md") if p.name != "readme.md")


def split_masthead(text):
    """Masthead is everything before the first line that is exactly '---'."""
    lines = text.split("\n")
    for i, line in enumerate(lines):
        if line.strip() == "---":
            return "\n".join(lines[:i]), lines[i + 1:], i + 1
    return "", lines, 0


def version_of(text):
    """1.0, Draft 1, v2.0 and 'Version: 1.1 -- September' all reduce to a pair."""
    m = re.search(r"[Vv]ersion:?\**\s*\**\s*v?(\d+)\.(\d+)", text)
    if m:
        return f"{m.group(1)}.{m.group(2)}"
    m = re.search(r"\bv(\d+)\.(\d+)", text)
    if m:
        return f"{m.group(1)}.{m.group(2)}"
    m = re.search(r"Draft\s+(\d+)(?:\.(\d+))?", text)
    if m:
        return f"{m.group(1)}.{m.group(2) or '0'}"
    return None


def slugify(heading):
    """GitHub's anchor rule: lowercase, drop punctuation, one hyphen per space."""
    s = heading.strip().lstrip("#").strip().lower()
    return re.sub(r"\s", "-", re.sub(r"[^\w\s-]", "", s))


def guide_rows():
    """Parse the at-a-glance table: numeral -> title, short name, size."""
    lines = GUIDE.read_text(encoding="utf-8").split("\n")
    start = next(i for i, l in enumerate(lines) if l.startswith("| Layer | # | Paper |"))
    rows = {}
    for line in lines[start + 2:]:
        if not line.startswith("|"):
            break
        cells = line.split("|")
        m = re.search(r"\*\*([IVX]+)\*\*", cells[2])
        if m:
            rows[m.group(1)] = {
                "title": cells[3].strip(),
                "short": cells[4].strip(),
                "size": cells[6].strip(),
            }
    return rows


# --------------------------------------------------------------------------
def check_1_roster(rows, papers):
    """Every guide numeral has a file whose masthead carries it, and back."""
    if set(rows) != set(REGISTRY):
        fail(1, f"guide numerals {sorted(set(rows) ^ set(REGISTRY))} differ from the registry")
    by_slug = {p.name[: -len("-whitepaper.md")]: p for p in papers
               if p.name.endswith("-whitepaper.md")}
    for num, slug in REGISTRY.items():
        p = by_slug.get(slug)
        if p is None:
            # X was on the roster for months before its source was committed.
            # An absent paper is a gap to fill, not a broken library.
            warn(1, f"{num}: no file docs/whitepapers/{slug}-whitepaper.md")
            continue
        head, _, _ = split_masthead(p.read_text(encoding="utf-8"))
        if not re.search(rf"\b{num}\b", head):
            fail(1, f"{p.name}: masthead does not carry its numeral {num}")
    for p in papers:
        slug = p.name[: -len("-whitepaper.md")] if p.name.endswith("-whitepaper.md") else None
        if slug not in REGISTRY.values():
            fail(1, f"{p.name}: no row in the guide's at-a-glance table")


def check_2_numerals(rows, papers):
    """Papers are cited by name. Mastheads keep their numerals; bodies do not."""
    names = {r["title"] for r in rows.values()} | {r["short"] for r in rows.values()}
    names = {n.lower().lstrip("*").rstrip("*") for n in names}
    p1 = re.compile(r"(paper|Paper|Companion|White Paper)\s+([IVX]{1,5})\b")
    p2 = re.compile(r"([A-Za-z*'’&]+)\s\(([IVX]{1,5})\)")
    ref = re.compile(r"\*([^*\n]{2,60})\*\s+(?:paper|Paper)\b")
    for p in papers:
        text = p.read_text(encoding="utf-8")
        _, body, offset = split_masthead(text)
        slug = p.name[: -len("-whitepaper.md")]
        own = next((n for n, s in REGISTRY.items() if s == slug), None)
        for i, line in enumerate(body, start=offset + 1):
            for m in p1.finditer(line):
                if m.group(1) in NUMERAL_OK or m.group(2) == own:
                    continue
                fail(2, f"{p.name}:{i}: numeral reference {m.group(0)!r} -- cite by name")
            for m in p2.finditer(line):
                word = m.group(1).strip("*'’&")
                if word in NUMERAL_OK or m.group(2) in NUMERAL_OK or m.group(2) == own:
                    continue
                fail(2, f"{p.name}:{i}: numeral reference {m.group(0)!r} -- cite by name")
            # A reference that says it is a paper must name one the guide knows.
            for m in ref.finditer(line):
                cited = m.group(1).lower().lstrip("*")
                if cited.startswith("the "):
                    cited = cited[4:]
                if any(cited == n or f"the {cited}" == n or f"{cited} paper" == n
                       for n in names):
                    continue
                fail(2, f"{p.name}:{i}: {m.group(0)!r} names no paper in the guide")


def check_3_sequences(papers):
    """Parts, chapters and numbered sections run consecutively."""
    part = re.compile(r"^#+\s*PART\s+(\d+|[IVX]+)(-[A-Z])?\b", re.I)
    chap = re.compile(r"^#+\s*CHAPTER\s+(\d+)\b", re.I)
    sect = re.compile(r"^##\s+(\d+)\.\s")
    for p in papers:
        lines = p.read_text(encoding="utf-8").split("\n")
        for label, pat, conv in (("Part", part, None), ("Chapter", chap, int),
                                 ("Section", sect, int)):
            seen = []
            for line in lines:
                m = pat.match(line)
                if not m:
                    continue
                raw = m.group(1)
                n = ROMAN.get(raw.upper(), None) if conv is None and not raw.isdigit() \
                    else int(raw)
                if n is not None and n not in seen:
                    seen.append(n)
            if len(seen) < 2:
                continue
            expected = list(range(seen[0], seen[0] + len(seen)))
            if seen != expected:
                missing = sorted(set(expected) - set(seen))
                fail(3, f"{p.name}: {label} sequence {seen} is not consecutive"
                        f"{f' (missing {missing})' if missing else ''}")


def check_4_figures(papers):
    """Figure numbers run from 1 with no gaps. 'Figure set 8a/8b' is figure 8."""
    pat = re.compile(r"Figures?\s+(?:set\s+)?(\d+)[ab]?\b")
    for p in papers:
        nums = {int(m) for m in pat.findall(p.read_text(encoding="utf-8"))}
        if not nums:
            continue
        expected = set(range(1, max(nums) + 1))
        if nums != expected:
            fail(4, f"{p.name}: figures {sorted(nums)} -- missing {sorted(expected - nums)}")


def check_5_rules(papers):
    """Doctrine Rule N outside the Doctrine; DC/DH on a foreign dotted rule."""
    # A sentence ends at .!? followed by whitespace. A rule ID's dots are never
    # followed by a space, so "Rule 2.7.1" stays inside the sentence it sits in
    # -- which is the difference between reading the citation and reading a
    # bare "Rule 2" that was never written.
    boundary = re.compile(r"(?<=[.!?])(?=\s)|\n")
    bare = re.compile(r"\bRule\s+(\d+)(?!\.\d)\b")
    for p in papers:
        slug = p.name[: -len("-whitepaper.md")]
        text = p.read_text(encoding="utf-8")
        if slug != "operating-doctrine":
            for s in boundary.split(text):
                if bare.search(s) and not re.search(r"[Dd]octrine", s):
                    fail(5, f"{p.name}: bare {bare.search(s).group(0)!r} -- "
                            f"name the Doctrine or prefix it: {s.strip()[:90]}")
        if slug in ("daily-cascade", "operating-doctrine"):
            continue
        for m in re.finditer(r"(?:(DC|DH)\s+)?Rule\s+(\d+)\.(\d+)", text):
            if m.group(1):
                continue
            if slug == "dealers-hand" and int(m.group(2)) in DH_OWN_CHAPTERS:
                continue
            fail(5, f"{p.name}: {m.group(0)!r} needs a DC or DH prefix")


def check_6_filenames():
    pat = re.compile(r"^[a-z0-9-]+-whitepaper\.md$")
    for p in sorted(PAPERS.glob("*.md")):
        if p.name == "readme.md":
            continue
        if not pat.match(p.name):
            fail(6, f"{p.name}: filename is not <slug>-whitepaper.md")


def check_7_claude_paths():
    """Every path CLAUDE.md names exists -- except the ones it says it deleted.

    And except the ones git is told to ignore. CLAUDE.md names `build/`, which
    `make figures` writes and a fresh clone does not have; a path whose whole
    job is to be absent from the repository cannot be evidence that CLAUDE.md
    is wrong. Those are reported as info, because a skipped check should say so
    out loud rather than pass silently -- but not as a warning, because there
    is nothing here for a human to decide.
    """
    text = CLAUDE.read_text(encoding="utf-8")
    cleanup = text.find("### Known cleanup")
    if cleanup != -1:
        text = text[:cleanup]
    toks = []
    for tok in set(re.findall(r"`([^`\s]+)`", text)):
        # Only repo-relative paths. Not $ENV_VARS, not URLs, not the
        # <slug> placeholders in the naming rules, and not the file:SYMBOL form
        # CLAUDE.md uses to point at a definition inside a module.
        tok = tok.split(":")[0]
        if "/" not in tok or tok.startswith(("$", "http")) or "<" in tok:
            continue
        toks.append(tok)
    toks = sorted(set(toks))
    ignored = gitignored(toks)
    for tok in toks:
        if tok in ignored:
            info(7, f"CLAUDE.md names {tok}, which .gitignore covers -- not checked")
        elif not (ROOT / tok.rstrip("/")).exists():
            fail(7, f"CLAUDE.md names {tok}, which does not exist")


def check_8_links():
    bad = 0
    for f in sorted((ROOT / "docs").rglob("*.md")):
        text = re.sub(r"`[^`\n]*`", "", f.read_text(encoding="utf-8"))
        anchors = {slugify(l) for l in text.split("\n") if l.startswith("#")}
        for _, tgt in re.findall(r"\[([^\]]*)\]\(([^)]+)\)", text):
            if tgt.startswith("#"):
                if slugify(tgt[1:]) not in anchors:
                    fail(8, f"{f.relative_to(ROOT)}: broken anchor {tgt}")
                    bad += 1
            elif not tgt.startswith(("http", "mailto")):
                if not (f.parent / tgt.split("#")[0]).exists():
                    fail(8, f"{f.relative_to(ROOT)}: broken path {tgt}")
                    bad += 1
    return bad


def check_9_versions(rows, papers):
    """The masthead owns the version string; the guide copies it."""
    by_slug = {p.name[: -len("-whitepaper.md")]: p for p in papers
               if p.name.endswith("-whitepaper.md")}
    for num, slug in REGISTRY.items():
        p, row = by_slug.get(slug), rows.get(num)
        if p is None or row is None:
            continue
        head, _, _ = split_masthead(p.read_text(encoding="utf-8"))
        mv, gv = version_of(head), version_of(row["size"])
        if mv is None:
            fail(9, f"{p.name}: masthead carries no version")
        elif mv != gv:
            fail(9, f"{num}: masthead says {mv}, guide says {gv} -- the masthead owns it")


def check_10_figures_and_builds():
    """Figure links resolve; built editions are not older than their source.

    This check used to warn that one of six hand-made HTML editions was
    missing, back when a paper's figures lived only in its HTML and the HTML
    was called canonical for reading. The figures are files under
    docs/figures/ now and docs/html/ is build output, so the two things worth
    checking are the two that rule made impossible to check: that every figure
    a paper references is actually there, and that the built edition is not
    behind the .md it was built from.

    A missing figure is a FAIL -- a paper that references artwork the repo
    does not have is wrong in a way a reader meets immediately. A stale build
    is ALSO a FAIL, since 19 September 2026. It was a warning on the reasoning
    that the fix is one `make html`, which is true and turned out to be beside
    the point: a warning is a thing a green run is allowed to carry, so a stale
    edition could be -- and was -- committed and pushed while the gate reported
    success. Change order L4 asked for a CI step that regenerates every edition
    and fails on a diff; this is that requirement, met by hash instead of by
    regeneration, and it only actually meets it as a failure.

    STALENESS IS A HASH, NOT A TIMESTAMP. This check compared mtimes until it
    was pointed out that git does not record them: every file in a fresh clone
    is stamped with the checkout, in whatever order the checkout happened to
    write them, so the answer was noise on any machine that had not just run
    the build. tools/build_paper_html.py therefore stamps each edition with
    the SHA-256 of the .md it was built from, and this recomputes it. An
    edition with no stamp is one built before this existed -- also a `make
    html` away, and reported the same way.
    """
    for f in sorted((ROOT / "docs").rglob("*.md")):
        text = re.sub(r"`[^`\n]*`", "", f.read_text(encoding="utf-8"))
        for alt, tgt in re.findall(r"!\[([^\]]*)\]\(([^)]+)\)", text):
            if tgt.startswith(("http", "data:")):
                continue
            if not (f.parent / tgt.split("#")[0]).exists():
                fail(10, f"{f.relative_to(ROOT)}: figure {tgt} does not exist "
                         f"({alt[:40]})")

    stamp = re.compile(r'<meta name="source-sha256" content="([0-9a-f]{64})"')
    for built in sorted(HTML.glob("*.html")):
        src = PAPERS / f"{built.stem}.md"
        if not src.exists():
            src = ROOT / "docs" / f"{built.stem}.md"
        if not src.exists():
            warn(10, f"docs/html/{built.name}: no .md it could have been built from")
            continue
        # The stamp is a <meta> in the head; an edition with figures inlined
        # runs to megabytes, and none of the rest of it is any of this check's
        # business.
        with built.open(encoding="utf-8") as fh:
            m = stamp.search(fh.read(4096))
        if m is None:
            fail(10, f"docs/html/{built.name} carries no source-sha256 -- "
                     f"run `make html`")
        elif m.group(1) != source_sha256(src):
            fail(10, f"docs/html/{built.name} was built from a different "
                     f"{src.name} -- run `make html`")


def check_11_wordcount(papers):
    # Whitespace-split, which runs about 1.5% above `wc -w` on this corpus
    # (wc disagrees with Python about some of the punctuation these papers
    # are full of). The 5% band is wide enough that the method does not
    # matter and narrow enough to catch a header five papers out of date.
    measured = sum(len(p.read_text(encoding="utf-8").split()) for p in papers)
    m = re.search(r"roughly ([\d,]+) words", GUIDE.read_text(encoding="utf-8"))
    if not m:
        warn(11, "the guide header states no word total")
        return
    claimed = int(m.group(1).replace(",", ""))
    if abs(claimed - measured) > 0.05 * measured:
        warn(11, f"guide claims {claimed:,} words, measured {measured:,}")


def check_12_stale(papers):
    pat = re.compile(r"when written|remains owed|to be written next", re.I)
    for p in papers:
        for i, line in enumerate(p.read_text(encoding="utf-8").split("\n"), 1):
            if pat.search(line):
                warn(12, f"{p.name}:{i}: stale forward reference "
                         f"{pat.search(line).group(0)!r}")


def check_13_agents():
    """AGENTS.md points at CLAUDE.md and restates nothing.

    A second copy of the rules is a copy that goes stale, and this one did.
    """
    text = AGENTS.read_text(encoding="utf-8").strip()
    lines = [l for l in text.split("\n") if l.strip()]
    if not lines or not lines[0].startswith("# "):
        fail(13, "AGENTS.md has no heading")
        return
    body = "\n".join(lines[1:])
    if "CLAUDE.md" not in body:
        fail(13, "AGENTS.md does not point at CLAUDE.md")
    if len(body.split()) > 120:
        fail(13, f"AGENTS.md restates rules ({len(body.split())} words); it is a "
                 f"pointer to CLAUDE.md, not a second copy")
    for tok in set(re.findall(r"`([^`\s]+)`", text)):
        if "/" in tok or tok.endswith((".md", ".py", ".yml")):
            if not (ROOT / tok.rstrip("/")).exists():
                fail(13, f"AGENTS.md names {tok}, which does not exist")


def main():
    rows = guide_rows()
    papers = paper_files()
    check_1_roster(rows, papers)
    check_2_numerals(rows, papers)
    check_3_sequences(papers)
    check_4_figures(papers)
    check_5_rules(papers)
    check_6_filenames()
    check_7_claude_paths()
    check_8_links()
    check_9_versions(rows, papers)
    check_10_figures_and_builds()
    check_11_wordcount(papers)
    check_12_stale(papers)
    check_13_agents()

    for i in infos:
        print(f"info {i}")
    for w in warns:
        print(f"warn {w}")
    for f in fails:
        print(f"FAIL {f}")
    print(f"\n{len(papers)} papers checked -- {len(fails)} failures, {len(warns)} warnings")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
