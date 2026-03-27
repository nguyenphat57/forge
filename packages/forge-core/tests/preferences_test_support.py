from __future__ import annotations

import common  # noqa: E402


class PreferencesTestSupport:
    @staticmethod
    def expected_extra(expected: dict[str, object]) -> dict[str, object]:
        compat = common.load_preferences_compat()
        return common.merge_extra_preferences(common.compat_default_extra(compat), expected)

    @staticmethod
    def mojibake(value: str) -> str:
        return value.encode("utf-8").decode("latin-1")
