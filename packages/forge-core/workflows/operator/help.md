---
name: help
type: flexible
triggers:
  - shortcut: /help
  - user feels stuck or asks what to do next
quality_gates:
  - Repo state inspected before giving advice
  - One primary recommendation plus at most two alternatives
  - No recap theater or save-memory ritual
---

# Help - Contextual Operator Guidance

> Muc tieu: dua ra huong dan ngan, dung ngu canh, va dua tren repo state that su co san.

<HARD-GATE>
- Khong duoc goi y `/recap` hoac `/save-brain` nhu reflex.
- Khong fabricate current state neu repo/artifact chua xac nhan.
- Khong dua hon 1 huong chinh va toi da 2 lua chon thay the.
</HARD-GATE>

## Process

1. Doc repo state huu ich nhat:
   - `git status`
   - plan/spec docs gan nhat
   - `.brain/session.json` hoac `.brain/handover.md` neu co
2. Resolve bang:

```powershell
python scripts/resolve_help_next.py --workspace <workspace> --mode help
```

3. Tra loi ngan gon:
   - Ban dang o dau
   - Lam tiep gi la tot nhat
   - Toi da 2 lua chon thay the neu can

## Output Contract

```text
Ban dang o: [...]
Lam tiep: [...]
Lua chon khac:
- [...]
- [...]
```

## Activation Announcement

```text
Forge: help | repo-first guidance, no recap theater
```
