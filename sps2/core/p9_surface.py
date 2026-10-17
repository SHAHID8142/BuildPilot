"""Stable ownership definition for the P9 surface.

This module lives outside ``domain/seo`` so rollback and snapshot recovery can
still import the allowlist after that deletable package has been removed.
"""

P9_ALLOWLIST_RELATIVE_PATHS: list[str] = [
    "domain/seo/__init__.py",
    "domain/seo/model.py",
    "domain/seo/metadata.py",
    "domain/seo/indexing.py",
    "domain/seo/structured_data.py",
    "domain/seo/onpage.py",
    "domain/seo/media.py",
    "domain/seo/url_taxonomy.py",
    "domain/seo/cwv.py",
    "domain/seo/specialized.py",
    "domain/seo/audit.py",
    "domain/seo/isolation.py",
    "domain/seo/tests/__init__.py",
    "domain/seo/tests/test_model.py",
    "domain/seo/tests/test_metadata.py",
    "domain/seo/tests/test_indexing.py",
    "domain/seo/tests/test_structured_data.py",
    "domain/seo/tests/test_onpage.py",
    "domain/seo/tests/test_media.py",
    "domain/seo/tests/test_url_taxonomy.py",
    "domain/seo/tests/test_cwv.py",
    "domain/seo/tests/test_specialized.py",
    "domain/seo/tests/test_audit.py",
    "domain/seo/tests/test_isolation.py",
    "sps2/tools/seo_audit.py",
    "sps2/tools/rollback_seo.py",
]
