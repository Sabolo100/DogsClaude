"""Pacsi partneri ajánlat → nyilvános GitHub Pages-oldal (külön repó, az apptól független).

Használat:  python marketing/tools/deploy_pitch.py
  1. build: python marketing/tools/build_pitch.py --pdf --public
  2. a marketing/pitch/public/ tartalma a Sabolo100/pacsi-partner repó main ágára kerül (commit + push)
  3. ha még nincs bekapcsolva, a GitHub Pages a main ág gyökeréből szolgál ki
Élő cím: https://sabolo100.github.io/pacsi-partner/

A munkapéldány a marketing/tmp/pages-pacsi-partner mappában van (gitignore-olt, bármikor törölhető).
"""
import json, pathlib, shutil, subprocess, sys

MK = pathlib.Path(__file__).resolve().parents[1]
REPO = "Sabolo100/pacsi-partner"
WORK = MK / "tmp" / "pages-pacsi-partner"
PUBLIC = MK / "pitch" / "public"
URL = "https://sabolo100.github.io/pacsi-partner/"


def run(*cmd, cwd=None, check=True):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8")
    if check and r.returncode:
        sys.exit(f"hiba: {' '.join(cmd)}\n{r.stdout}\n{r.stderr}")
    return r


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")   # a Windows-konzol kódlapja nem ismer minden jelet
    run(sys.executable, str(MK / "tools" / "build_pitch.py"), "--pdf", "--public")
    ver = (MK / "pitch" / "VERSION").read_text(encoding="utf-8").strip()
    exists = run("gh", "repo", "view", REPO, "--json", "name", check=False).returncode == 0
    if not (WORK / ".git").exists():
        if WORK.exists():
            shutil.rmtree(WORK)
        if exists:
            run("git", "clone", f"https://github.com/{REPO}.git", str(WORK))
        else:
            run("gh", "repo", "create", REPO, "--public",
                "--description", "Pacsi – partneri ajánlat kutyás márkáknak (webes prezentáció) · DarwinAI",
                "--homepage", URL)
            WORK.mkdir(parents=True)
            run("git", "init", "-b", "main", cwd=WORK)
            run("git", "remote", "add", "origin", f"https://github.com/{REPO}.git", cwd=WORK)
    # a munkapéldány tartalmát lecseréljük a friss buildre (a .git marad)
    for p in WORK.iterdir():
        if p.name != ".git":
            shutil.rmtree(p) if p.is_dir() else p.unlink()
    for p in PUBLIC.iterdir():
        (shutil.copytree if p.is_dir() else shutil.copy2)(p, WORK / p.name)
    run("git", "add", "-A", cwd=WORK)
    if run("git", "status", "--porcelain", cwd=WORK).stdout.strip():
        build = next((line.split("build ")[1].split(")")[0] for line in (PUBLIC / "README.md").read_text(encoding="utf-8").splitlines() if "build " in line), "")
        msg = f"Pacsi partneri ajánlat v{ver} (build {build})\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
        run("git", "commit", "-m", msg, cwd=WORK)
        run("git", "push", "-u", "origin", "main", cwd=WORK)
        print(f"  feltöltve: {REPO} (v{ver})")
    else:
        print("  nincs változás – nem kellett feltölteni")
    # GitHub Pages: a main ág gyökeréből (egyszeri beállítás)
    if run("gh", "api", f"repos/{REPO}/pages", check=False).returncode:
        run("gh", "api", "-X", "POST", f"repos/{REPO}/pages", "-f", "source[branch]=main", "-f", "source[path]=/")
        print("  GitHub Pages bekapcsolva (main / gyökér)")
    info = json.loads(run("gh", "api", f"repos/{REPO}/pages").stdout)
    print(f"  Pages: {info.get('html_url', URL)} · állapot: {info.get('status')}")


if __name__ == "__main__":
    main()
