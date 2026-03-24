# UI Escalation Rules

> Dùng để quyết định khi nào `frontend` hoặc `visualize` nên kéo thêm `$ui-ux-pro-max`.

## Escalate To `$ui-ux-pro-max` When

- user muốn nhiều visual directions hoặc style exploration
- visual direction còn mơ hồ và cần reference breadth
- cần palette / typography / landing pattern suggestions
- task là concept-first hơn implementation-first
- muốn nghiên cứu rộng trước khi chốt brief

## Do Not Escalate When

- chỉ là bug CSS nhỏ hoặc spacing fix
- design system hiện có đã quá rõ và task chỉ là implementation
- chỉ cần sửa behavior/state nhỏ trong component hiện có
- task thiên về accessibility/responsive cleanup hơn là visual exploration

## Recommended Order

### Khi task là visualize-heavy

```text
1. visualize
2. Nếu visual direction còn rộng hoặc user muốn nhiều options -> load $ui-ux-pro-max
3. Chốt visual brief
4. Handoff cho frontend/build
```

### Khi task là frontend nhưng cần mở visual range

```text
1. frontend
2. Nếu design system chưa đủ direction -> load $ui-ux-pro-max
3. Update frontend brief
4. Implement UI
```

## Output Discipline

- `$ui-ux-pro-max` cung cấp design exploration và breadth
- Forge `frontend`/`visualize` vẫn giữ:
  - scope discipline
  - brief requirement
  - responsive/a11y/state coverage
  - handoff/report shape

Đừng để `$ui-ux-pro-max` thay brief hoặc thay delivery checklist của Forge.
