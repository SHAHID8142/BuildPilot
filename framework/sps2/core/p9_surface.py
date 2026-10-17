"""Stable ownership definition for the P9 surface.

This module lives outside ``framework/domain/seo`` so rollback and snapshot recovery can
still import the allowlist after that deletable package has been removed.
"""

P9_ALLOWLIST_RELATIVE_PATHS: list[str] = [
    "framework/domain/seo/__init__.py",
    "framework/domain/seo/model.py",
    "framework/domain/seo/metadata.py",
    "framework/domain/seo/indexing.py",
    "framework/domain/seo/structured_data.py",
    "framework/domain/seo/onpage.py",
    "framework/domain/seo/media.py",
    "framework/domain/seo/url_taxonomy.py",
    "framework/domain/seo/cwv.py",
    "framework/domain/seo/specialized.py",
    "framework/domain/seo/audit.py",
    "framework/domain/seo/isolation.py",
    "framework/domain/seo/tests/__init__.py",
    "framework/domain/seo/tests/test_model.py",
    "framework/domain/seo/tests/test_metadata.py",
    "framework/domain/seo/tests/test_indexing.py",
    "framework/domain/seo/tests/test_structured_data.py",
    "framework/domain/seo/tests/test_onpage.py",
    "framework/domain/seo/tests/test_media.py",
    "framework/domain/seo/tests/test_url_taxonomy.py",
    "framework/domain/seo/tests/test_cwv.py",
    "framework/domain/seo/tests/test_specialized.py",
    "framework/domain/seo/tests/test_audit.py",
    "framework/domain/seo/tests/test_isolation.py",
    "framework/sps2/tools/seo_audit.py",
    "framework/sps2/tools/rollback_seo.py",
]
