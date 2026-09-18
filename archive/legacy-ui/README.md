# Archived legacy interface files

These files were removed from Flask's production `templates` and `static` directories during
the Milestone 1 surface audit on September 17, 2026.

No reachable route, active template, stylesheet, JavaScript file, or test referenced them.
They are retained here for historical review and are not served by Flask. The production
surface is enforced by `tests/test_surface_audit.py`; adding a new route, template, or static
asset requires an explicit inventory update and review.
