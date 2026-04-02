from __future__ import annotations

import common  # noqa: E402


class PreferencesTestSupport:
    @staticmethod
    def expected_extra(expected: dict[str, object]) -> dict[str, object]:
        compat = common.load_preferences_compat()
        defaults = common.merge_extra_preferences(
            common.compat_default_extra(compat),
            {"delegation_preference": common.DEFAULT_DELEGATION_PREFERENCE},
        )
        return common.merge_extra_preferences(defaults, expected)

    @staticmethod
    def mojibake(value: str) -> str:
        return value.encode("utf-8").decode("latin-1")
