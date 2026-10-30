---
name: projects
description: Explains local projects. Use whenever need to know what projects and/or code is available locally. Use when user asks about related work. Use when encountering a new word that might be a project name.
---

# projects

Local OSS projects are cloned under /opt/clones/github/jalanb

## Description

One genuine insight from the zeitgeist:
> Write the description in third person — inconsistent POV causes discovery problems

This tells us: the description is injected raw into the system prompt and must survive that context, which reframes the whole authoring problem correctly.

## Progressive Disclosure

The progressive disclosure architecture is sound: keep SKILL.md lean and move deep detail into well-named resource files so Claude loads only what's needed.

## Good Skills

A good SKILL.md has:
 - tight description (third-person, trigger conditions explicit)
 - SKILL.md as table-of-contents only
  - logic in referenced files
 - at least concrete test cases you can run to verify
  - it fires correctly
  - it does (at least some of) what it is supposed to

Or: a good skill should succinctly and precisely tell Claude how it can help.

## Bad Skills

Some examples of how to write bad skills:

1. Don't talk about testability.

2. Take the "onboarding guide for a new hire" approach.

3. YAGNI
