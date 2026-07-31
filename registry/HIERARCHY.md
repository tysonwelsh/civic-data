# Entity hierarchy (GENERATED — `python3 scripts/build_hierarchy.py`)

Derived from `entities.csv` + `relationships.csv`; regenerate, never edit.
Geography lives in the relationship edges, not the folder tree (SCHEMA_SPEC §0).

- **State of Utah** (`ut_state`, fed 301, built (db))
  - **Utah Department of Transportation** (`udot`, fed 302, registered only) — state executive agency
  - **Utah Transit Authority** (`uta`, fed 303, registered only) — statutorily created transit district
  - **Mountainland Association of Governments** (`mag_mpo`, fed 202, built (db)) — 8 member entities
  - **Wasatch Front Regional Council** (`wfrc_mpo`, fed 201, built (db)) — 27 member entities
  - **Salt Lake County** (`salt_lake_county`, fed 101, built (db))
    - **Alta** (`alta`, fed 21, built (db))
    - **Bluffdale** (`bluffdale`, fed 26, built (db)) — primary county
    - **Copperton** (`copperton`, fed 30, built (db))
    - **Cottonwood Heights** (`cottonwood_heights`, fed 23, built (db))
    - **Draper** (`draper`, fed 19, built (db)) — primary county
    - **Emigration Canyon** (`emigration_canyon`, fed 31, built (db))
    - **Herriman** (`herriman`, fed 18, built (db))
    - **Holladay** (`holladay`, fed 24, built (db))
    - **Kearns** (`kearns`, fed 28, built (db))
    - **Magna** (`magna`, fed 29, built (db))
    - **Midvale** (`midvale`, fed 22, built (db))
    - **Millcreek** (`millcreek`, fed 15, built (db))
    - **Murray** (`murray`, fed 17, built (db))
    - **Riverton** (`riverton`, fed 20, built (db))
    - **Sandy** (`sandy`, fed 8, built (db))
    - **Salt Lake City** (`slc`, fed 9, built (db))
    - **South Jordan** (`south_jordan`, fed 14, built (db))
    - **South Salt Lake** (`south_salt_lake`, fed 25, built (db))
    - **Taylorsville** (`taylorsville`, fed 16, built (db))
    - **West Jordan** (`west_jordan`, fed 12, built (db))
    - **West Valley City** (`west_valley`, fed 13, built (db))
    - **White City** (`white_city`, fed 27, built (db))
  - **Utah County** (`utah_county`, fed 102, built (db))
    - **Bluffdale** (`bluffdale`, fed 26, built (db)) — straddle/secondary (low)
    - **Draper** (`draper`, fed 19, built (db)) — straddle/secondary (medium)
    - **Lehi** (`lehi`, fed 1, built (db))
    - **Orem** (`orem`, fed 5, built (db))
    - **Provo** (`provo`, fed 7, built (db))
    - **Vineyard** (`vineyard`, fed 11, built (db))
  - **Weber County** (`weber_county`, fed 103, built (db))
    - **Ogden** (`ogden`, fed 4, built (db))
  - **Cache County** (`cache_county`, fed 104, built (db))
    - **Logan** (`logan`, fed 2, built (db))
  - **Summit County** (`summit_county`, fed 105, built (db))
    - **Park City** (`park_city`, fed 6, built (db)) — straddle/secondary (high)
  - **Washington County** (`washington_county`, fed 106, built (modules, db-less))
    - **St. George** (`st_george`, fed 10, built (db))
  - **Juab County** (`juab_county`, fed 107, built (modules, db-less))
    - **Nephi** (`nephi`, fed 3, built (db))
  - **Wasatch County** (`wasatch_county`, fed 108, registered only)
    - **Park City** (`park_city`, fed 6, built (db)) — straddle/secondary (high)

Totals: 31 cities/towns · 8 counties · 2 regional · 3 state = 44 entities.
