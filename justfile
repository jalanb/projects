push:
    mkdir -p ~/.claude/skills/projects
    cp src/* ~/.claude/skills/projects/

pull:
    test -f ~/.claude/skills/projects/SKILL.md && cp -r ~/.claude/skills/projects/. src/

regen-clones:
    python3 src/clones.py /opt/clones/github/jalanb --quiet --report src/clones.md || true

regen-local:
    python3 src/local.py


