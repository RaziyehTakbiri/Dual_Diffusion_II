"""Code-state stamp. Claude bumps this on EVERY shipment; notebooks print it.

If the version a notebook prints does not match the version Claude last
announced in chat, the Git sync did not deliver the latest code - stop and
say so before running anything expensive. Added 2026-07-19 after a sync
overwrote newer files with older copies and silently reverted two fixes.
"""

DMD_VERSION = "2026-07-19.1  (loop-free CFC [R17]; NODE checkpoint+RK4x1 restored)"
