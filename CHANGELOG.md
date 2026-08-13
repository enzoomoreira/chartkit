# Project Changelog

## [2026-08-13 07:40]
### Fixed
- **Month and weekday names follow `babel_locale`**: `mdates.DateFormatter` hands the format string to `datetime.strftime`, whose names come from the process C locale, so a figure read `R$ 5,60` on one axis and `Sep/24` on the other. The name-spelling directives (`%a %A %b %B %p`) are now resolved through Babel; every other directive still goes to strftime, so `%Y-%m-%d` is unaffected and `en_US` output is byte-identical. Abbreviated names drop the period CLDR gives them -- `fev./24` puts it against the separator for nothing. The `axis_controls` snapshot had been storing `Sep/23` since it was written: the suite recorded the defect without anyone asserting it was wrong
- **Auto tick rotation fires before labels touch**: the trigger was strict intersection, which twenty quarterly labels sitting 0.96px apart never met -- none touching, all reading as one word. It is now a minimum separation, `ticks.min_gap_px`, defaulting to the width of a space at the default label size. The escalation check keeps strict intersection on purpose: the bounding box of a rotated label is its diagonal envelope, so two 45-degree labels measure ~1.2px apart while reading perfectly clear, and applying the gap to that number sent every rotated chart to 90 degrees. The GDP example carried `tick_rotation=45` as a workaround for this; removing it renders a byte-identical PNG
- **`width=` no longer raises `TypeError`**: the bar enhancers always passed their own width to `ax.bar()`, so a caller asking for one collided with it. On a grouped chart the value is the width of the whole group

### Changed
- **BREAKING -- bar width is a share of the spacing, not a frequency tier**: measured as the fraction of the slot each bar owned, the three tiers gave weekly 11% and quarterly 22% while daily and annual sat near 80%. Width is now the median gap between points times `bars.width_fraction`, putting every frequency at 80%; daily and annual land within 3% of where the tiers had them, so only the broken frequencies move. The median, not the mean: a series with a few missing dates still has a spacing. `bars.width_default` is now `bars.width_fraction`, and `bars.width_monthly`, `bars.width_annual` and the whole `bars.frequency_detection` table are gone
- **BREAKING -- the series palette separates by hue**: the six colours were shades of one teal, a sequential palette doing a categorical job. The closest adjacent pair was `secondary`/`tertiary` at 12.9 CIELAB units, below the ~25 at which two colours stop reading as one -- and `primary`/`secondary`, the pair that looked worst in the gallery, was not even the worst at 16.8. The dark teal `#00464D` still anchors the set; the other five are copper, steel blue, olive, wine and muted purple, with no pair closer than 26.4. A config that pinned the old hexes keeps them

### Added
- **`README.pt-BR.md`**: the remaining half of decision D6. The English README is the one PyPI renders; this is the entry point for the audience the defaults were built for, cross-linked from both sides and shipped in the sdist. Every code block was executed. The documentation itself stays in English, and the file says so
- **`tests/formatting/test_tick_rotation.py`**: the crowding trigger, the configured gap, the escalation to 90 degrees, and the case that must *not* escalate
- **Localized tick label tests**: the same directive across locales, the `%%` escape, and the axis picking up the configured locale
- **Bar width tests**: one share of the slot per frequency, a gapped series measuring the same as a regular one, repeated dates falling back, and the three `width=`/`height=` override paths

## [2026-08-13 05:10]
### Fixed
- **Labels leaving the data area are now resolved**: a highlight label is anchored `ha='left'` at the last data point, so it extends past it by construction. Resolution only ran when a label overlapped another label or a registered obstacle, and the axes border is neither, so the label sat on top of the right spine of every dual-axis chart. `edge_margin_factor` did not save it -- that only ranks candidates once a resolution is already running. Measured on the composition example: 13px of overflow before, 14px of clearance after
- **Rescue candidate for out-of-bounds labels**: triggering alone was not enough. The proactive candidates step in multiples of the label height, which is the right scale for separating two labels but arbitrary against a border -- a label hanging 30px past the spine was offered 14, 21 and 28px and every one was discarded for still being outside, so the solver ran and found nothing. `_generate_bounds_candidates()` returns the exact correction instead, landing at the edge margin rather than flush against the border: a glyph's ink reaches past the extent matplotlib reports for its text, so a box measured as inside still drew over the spine

### Changed
- **BREAKING -- rolling overlays demand a full window**: `lines.moving_avg_min_periods` defaulted to `1`, so the first eleven points of an `ma:12` were averages of one to eleven samples while the legend read MM12; `std_band` computed its first band from two observations. The default is now `None`, meaning the full window, and the field is `int | None` with `ge=1`. Set an explicit value to restore the old output. This also aligns the overlays with the transforms, which already passed `min_periods=window` in `accum` and `zscore` -- the inconsistency was internal, not only cosmetic

### Performance
- **Collision cost on label-heavy charts cut by up to 46%**: measuring a text extent lays the string out, and the solver asked each label for its own on every pass over every other one -- quadratic in labels, for values that only change when something moves. Extents are taken once per resolution and refreshed only for the label that moved. Measured against the same chart with the engine off: 36 labels 845ms -> 458ms, 18 labels 280ms -> 220ms, 3 labels unchanged. The regenerated gallery is byte-identical, so placement did not change -- only its cost

### Added
- **`examples/` gallery over Brazilian macro series**: five runnable scripts rendering IPCA, Selic, USD/BRL and GDP, with the output committed under `docs/assets/gallery/` and indexed in `docs/gallery.md`. The library's product is a theme and nothing in the suite could see it: the structural snapshots assert that a footer exists and that a series has the colour it was handed, not that the result reads well. Re-running `render_all.py` produces a diff a human can review, which is the only form that coverage can take. Data is synthetic, generated from a fixed seed and labelled illustrative throughout
- **`tests/metrics/test_moving_average.py`**: the moving average overlay had no direct test. Covers the full-window default, an explicit `min_periods`, the partial case between them, and a window longer than the series
- **Out-of-bounds collision tests**: label past the right edge, label rescued clear of the border rather than flush against it, overflow at the top, and a label already inside left untouched

### Documentation
- **Why the solver is greedy**: the algorithm was documented as a procedure without saying which family it belongs to or what it was chosen over. It now states the position -- candidate-based greedy, the same family as Vega-Lite's labeler, improving on that baseline by scoring every valid candidate instead of taking the first that fits -- and why simulated annealing is not planned
- **Occupancy grid note qualified**: the grid was removed as losing "consistently, even at 10000 points", but that benchmark varied obstacle count while the cost that scales is labels times candidates. It was never measured on the axis where it would compete, so the note now says what the evidence supports rather than more
- **"Label never leaves the visible chart area" corrected**: false until this release -- candidates were filtered to stay inside, but a label that began outside was never picked up
- **Stale dependencies removed from the README**: `loguru` and `cachetools` were still listed under Requirements after being dropped, and `pydantic` was missing. `architecture.md` still described `_logging.py` as loguru setup
- **Test counts refreshed**: `testing.md` claimed 701 against an actual 809, its per-directory numbers were stale, eleven test files were missing from the tree, and `metrics/conftest.py` was listed after being removed

### Known issues
All four issues recorded here -- English month names, the bar width tiers,
strict-overlap rotation and the palette contrast -- were fixed in the entry
above. Each was found by looking at the gallery, not by running the suite.

## [2026-08-05 04:22]
### Added
- **`LICENSE` (MIT)**: an absolute blocker for publishing. Without a licence file the package is legally unusable by any company
- **`src/chartkit/py.typed`**: without the PEP 561 marker the type hints are invisible to anyone installing the package -- every annotation in the library stopped at the wheel boundary
- **`pyproject` metadata**: `license`, `authors`, `keywords`, `classifiers` and `project.urls`
- **`.github/workflows/release.yml`**: publishes to PyPI through trusted publishing when a `v*` tag is pushed. No token to store or rotate. The job fails before publishing if the tag disagrees with the version in `pyproject`, and runs the suite -- on a release, a red test has to stop the publish rather than be noticed afterwards
- **sdist includes `tests`, `docs`, `CHANGELOG.md` and `LICENSE`**

### Changed
- **`description` translated to English**: per decision D6 of the plan
- **`pandas>=2.2.0` kept without an upper bound**: the CI matrix already exercises 2.2 and 3.0 on Linux and Windows. Capping a library's core dependency forces every downstream project to wait on a release

### Verified
- Name `chartkit` available on PyPI (404 at `pypi.org/pypi/chartkit/json`)
- `twine check` passes wheel and sdist; `py.typed` and `LICENSE` present in the wheel
- `pydantic` was already declared explicitly (F7.5)
- CI already installs the wheel into a clean venv and validates import, accessor and plot (F7.10)

## [2026-08-05 03:48]
### Changed
- **pyright errors: 174 -> 51**: two annotations that were in fact wrong accounted for 123 of them. The collision factories declared `Artist` while calling methods of `Line2D`, `Patch` and `Collection`; and `Path.vertices` was indexed without `np.asarray`, so the stubs saw `ArrayLike`. What remains is friction with the matplotlib and pandas stubs (`Figure | SubFigure`, `Timestamp | NaTType`), which calls for `cast()` rather than better types
- **`barh` warns about readability**: `bar` has warned above `bars.warning_threshold` since it was written; the horizontal version never did
- **`_infer_highlight_style` hoisted out of the loop**: it was recomputed per column, rescanning the patches the previous columns had added. The answer -- whether this kind draws patches -- is settled by the first
- **`**kwargs: Any` on the bar enhancers**: without the annotation they did not satisfy the `Enhancer` Protocol
- **`_extract_metric_name(spec: str | MetricSpec)`**: was `str | object`, and the `hasattr(spec, "name")` inside would have matched a `pd.Series`

### Added
- **Module docstrings in 13 files**: the 11 enhancers, `accessor.py` and `markers.py`
- **Formatter dispatch coverage test**: it was a module-level `assert`, which `python -O` strips -- precisely in the runs where the failure costs most

### Removed
- **`kwargs.get("patch_artist", True)` in boxplot**: the `setdefault` just above makes the default unreachable

## [2026-08-05 03:02]
### Performance
- **Scatter collision: 45s -> 0.6s at 100 points**: `_PathObstacle` called `Path.get_extents()` on every intersection test -- per path, per candidate, per label, per iteration. On a scatter every marker is a circle of Beziers, and `get_extents()` solves for the exact extrema with a polynomial root-find per segment. The profile put 9.8s of 9.8s there. Bounding boxes now come from the control points and are computed once at construction
- **Aggregate hull per obstacle**: one comparison discards the whole obstacle when the label is far from it; only the paths that actually overlap reach `intersects_bbox()`
- Measured: 1,000 points from 12.9s to 0.38s; 10,000 points from 75s to 2.0s. `plot` (line) is unchanged

### Added
- **`tests/collision/test_collision_perf.py`**: expresses the ceiling as a multiple of the same chart with the engine off, so it keeps holding on a slower machine

### Not done
- **Occupancy grid for large Collections (F5.2)**: implemented and measured against the alternative. After the extents fix it loses consistently even at 10,000 points (3.96s against 3.58s) -- the first favourable measurement was noise. Removed
- **Early exit in the candidate loop (F5.3)**: contradicts the cost-based selection that landed after the plan was written. The solver has to score every valid candidate to pick the cheapest; stopping at the first free position returns to the greedy behaviour
- **Auto-disable above a threshold (F5.4)**: a safety valve for the pathological case, which no longer exists

## [2026-08-05 02:14]
### Changed
- **BREAKING -- registering an existing name raises `RegistryError`**: `MetricRegistry.register` and `ChartRenderer.register_enhancer` overwrote silently, so two libraries registering `'ma'` cancelled each other without warning. Pass `replace=True` to override deliberately
- **BREAKING -- `MetricRegistry.clear()` removed**: it emptied the whole registry, leaving `'ath'` and `'ma'` undefined. Replaced by `reset_to_builtins()`, which drops only what the user registered
- **`_toml_data` is no longer a `ClassVar`**: the merged TOML lived in class state shared by every loader and every thread -- two configs built at the same time read each other's files. It now travels as an init kwarg, consumed in `settings_customise_sources` before validation
- **`ConfigLoader.project_root` reads and writes under the lock**: `reset()` clears both fields, and an unsynchronised reader could see the resolved flag set with the value already cleared
- **Invalid configuration raises chartkit's `ValidationError`**: pydantic's `ValidationError` leaked out of `get_config()`, without indicating that the cause was a setting

### Added
- **`MetricRegistry.unregister(name)` and `reset_to_builtins()`**: the suite's conftest reached into `_metrics` directly for lack of a public API
- **`CHARTKIT_NO_AUTO_CONFIG`**: turns off automatic TOML discovery. Without it the library reads whatever `pyproject.toml` sits above the working directory -- surprising for an application that wants only its own settings

### Removed
- **`cachetools` dependency**: it was there to lock the `find_project_root` cache. The recorded justification -- "`lru_cache` is not thread-safe" -- was inaccurate: CPython guards its internal bookkeeping. What is not guaranteed is once-per-key execution under concurrency, and for a side-effect-free filesystem walk that costs at most a redundant `stat()`

## [2026-08-05 01:26]
### Fixed
- **`points_formatter` truncated instead of rounding**: `int(x)` cuts towards zero, so the label for the maximum of a series peaking at 110.85 read `110`. On a chart whose whole job is to mark the extreme, that understated the peak by nearly a full point. The `test_highlight_modes_snapshot` records the fix (`"110"` -> `"111"`)
- **`footer_format` with an unknown placeholder**: `str.format` raised a bare `KeyError` in the middle of `plot()`, naming the key but not where it lives. It is now a `ValidationError` citing the setting and the valid placeholders
- **`std_band_full_format` did not accept `{window}`**: the full-series branch passed only `deviations`, so a template mentioning `{window}` -- valid in the rolling branch -- died with a `KeyError`. Both branches now receive the same fields
- **`vband` with an unparseable date**: leaked pandas' `DateParseError`, outside the `ChartKitError` hierarchy
- **Empty `formatters.magnitude.suffixes`**: the formatter indexes the last entry as a ceiling, so an empty list was an `IndexError` waiting for a large enough number. Rejected in the schema via `min_length=1`

### Pending decision
- **F3.26 -- `min_periods=1` on the moving average**: the first 11 points of an `MM12` are averages of 1 to 11 samples, with the legend reading `MM12`; the same holds for `std_band`. Changing the `lines.moving_avg_min_periods` default to the full window makes the line honest about its label at the cost of 11 empty leading points, and is breaking. Awaiting a decision

## [2026-08-05 00:41]
### Fixed
- **`despike(method='interpolate')` imputed the input's own NaNs**: `interpolate()` fills every gap it finds, so the NaNs the caller supplied came back as invented values. Only the positions the filter blanked out are now filled
- **`resample` outside the contract of its neighbours**: it ran neither `validate_numeric` nor `sanitize_result`, so text columns travelled through untouched and infinities survived. The `DatetimeIndex` check comes before the numeric validation, so a rejected index does not first draw a warning about frequency detection
- **`normalize(base_date=)` leaked raw pandas errors**: `get_indexer` raises `TypeError` on a non-temporal index and `InvalidIndexError` on a duplicated one -- neither is a `ChartKitError`
- **`zscore` blamed constant data**: the log said `constant data, std=0` even when the cause was a `window` larger than the series, sending the reader to investigate the data rather than the call
- **`accum` used a monthly window on daily data**: `pd.infer_freq` demands a perfectly regular index, which no market series has -- one public holiday is enough. The fallback landed on the config's `accum_window` (12), accumulating over 12 *days*

### Added
- **`estimate_freq()` in `_internal/frequency.py`**: estimates frequency from the median spacing between observations, for when `pd.infer_freq` gives up. It tells `B` from `D` by whether the index ever lands on a weekend -- 252 against 365 periods a year is too large a gap to guess. Used only in the `accum` fallback; `variation` and `annualize` still demand an explicit frequency

### Not fixed
- **False spikes at the `despike` edges (A2-22)**: the centred window is one-sided at the extremities. Edge flags do occur on trending, noisy series, but that they are false was never established, and both attempted treatments regressed -- requiring a full window blinds the filter on short series (a 350 in a ~100 neighbourhood stopped being caught), and odd reflection flagged more edges than before. Left as is

## [2026-08-04 23:18]
### Fixed
- **Non-temporal axes received date formatting**: with `ticks.date_format` configured -- the normal way to use this library -- `hist`, `ecdf`, `boxplot` and `violinplot` labelled the X axis with `"Jan/1970"`, because `finalize_chart` applied a `DateFormatter` without looking at what the kind puts on that axis. Only the `series` group of `KindCaps` now receives a date locator and formatter
- **Collision resolved before the final geometry**: `resolve_collisions` ran before `finalize_chart` applied limits, rotation and margins. Placement is measured in pixels, so labels were positioned against geometry that changed immediately afterwards -- with a compressing `ylim`, two labels overlapped by 46x14 px. The two steps swapped order in both `engine` and `compose`
- **`stairs` discarded the dates**: `ax.stairs(values)` without `edges` generates `range(n+1)`, throwing the axis to 0..n. Edges are now derived from the real x (datetime or numeric); a categorical index keeps the positional behaviour
- **Highlight anchored to the index label**: `add_highlight` was called without `x=` in the generic path and in the `area`, `stem` and `stairs` enhancers, positioning the marker by the label rather than the coordinate
- **`idxmax`/`idxmin` with a duplicated index**: returned a Series and blew up in `np.isfinite`. Replaced with positional lookup via `argmax`/`argmin`
- **X column re-included in Y**: `plot(x='ano')` with `y=None` left `ano` in the `select_dtypes` and drew the column against itself
- **`y=['a','a']`**: `df[['a','a']]['a']` returns a DataFrame and broke the enhancers' broadcasting. Now rejected with a clear message
- **`xlim=('2023','2024')` on a date axis**: the coercion tried `float` before date, turning it into 2023.0 -- two millennia away from the data. On a temporal axis the order is inverted
- **`sort` on a datetime/numeric axis was a no-op**: the bars were reordered but drawn back at their own dates, reproducing the original chart. Now rejected -- ranking is a categorical operation, and `barh` already works, being ordinal by construction
- **`y_origin='auto'` with a constant series**: `set_ylim(v, v)` emitted a singular-transformation `UserWarning`, which becomes an error under `-W error`
- **`tick_rotation=True` accepted as an angle**: `isinstance(True, int)` made `True` mean 1 degree
- **`normalize_highlight` with a non-iterable value**: leaked `TypeError` outside the `ChartKitError` hierarchy
- **Empty palette**: `resolve_color` raised `ZeroDivisionError` on the modulo
- **Numeric index read as nanoseconds**: `_coerce_datetime_index([2020, 2021])` returned 1970-01-01
- **Empty object index classified as categorical**: `all([])` is `True`

### Changed
- **BREAKING -- `PlotResult` no longer has a `plotter` field**: `save()` now writes `self.fig`. It used to delegate to the plotter that built the chart, whose `_fig` every subsequent `plot()` overwrote -- a reused `ChartingPlotter` made the first `PlotResult` save the second figure
- **BREAKING -- `ChartingPlotter.save()` removed**: it existed only for that stateful path. The figure's owner is the `PlotResult`
- **`Saveable` Protocol and `_ComposePlotter` removed**: they existed only to satisfy the `plotter` field

## [2026-08-04 22:02]
### Changed
- **BREAKING -- `layer()` reordered to mirror `plot()`**: positional order went from `(kind, x, y)` to `(x, y)` with `kind` keyword-only. `layer('data', 'valor')` now selects the same columns as `plot('data', 'valor')`. Calls that passed `kind` positionally must use `kind=`
- **BREAKING -- `kind` validated against an allowlist**: validation accepted any callable attribute of `Axes`; only 9 generic kinds actually work with the `(x, y_series)` convention. Methods with an incompatible signature (`hlines`, `psd`, `hexbin`) and methods that do not plot (`clear`, `set_title`, `twinx`) now raise `ValidationError` listing the available kinds, instead of leaking a raw matplotlib `TypeError`
- **BREAKING -- `barh` rejects `highlight`**: `KindCaps` declared `highlight=True` but the enhancer discarded the parameter silently. The capability was aligned to the behaviour -- the markers position themselves against a vertical value axis, which `barh` does not have
- **`normalize(base=)` accepts a `float`**: it was `PositiveInt`, which prevented rebasing to `1.0` -- the convention for index and multiple charts
- **Transform types exposed as `Literal`**: `horizon`, `freq` and `method` are no longer `str` in the public signatures (`chartkit.transforms.types`), giving autocomplete and static checking of the values the validators already demanded at runtime
- **`tick_freq` annotated as `TickFreq`**: it was `str` on the facades, although `plot_validation` already restricted the values

### Added
- **`decimals` and `figsize` on the public facades**: `decimals` existed only on `ChartingPlotter.plot`; `figsize` only on `compose()`. Both now appear in `plot()` on both accessors, and `decimals` also on `Layer` -- next to the `units` it refines, since each axis is formatted independently
- **`FillsConfig`**: `fills.area_alpha` (default `0.3`) and `fills.violin_alpha` (default `0.7`) make configurable the opacities previously hardcoded in the enhancers
- **`ChartKind` as `Literal | str`**: 24 known kinds gain autocomplete without closing the type to user-registered enhancers
- **`tests/test_api_parity.py`**: compares name, order, default and annotation across the three copies of `plot()` and the two of `layer()`, and verifies by sentinel that every accepted parameter actually reaches the engine. A parameter that exists in the signature but is never forwarded now breaks the build
- **`highlight` validation at `Layer` construction**: invalid modes were discovered only midway through `compose()` rendering
- **`zorder` applied to `pie` wedges**: `ax.pie()` does not accept `zorder`, so the `RenderContext` value was lost

## [2026-03-22 22:17]
### Added
- **Chart kind classification system (`_classification.py`)**: the declarative `KindCaps` table defines each chart kind's capabilities (highlight, temporal metrics, composability, axis group). Early-fail validation in `engine.py`, `create_layer()` and `compose()` blocks incompatible combinations before rendering
- **Per-kind highlight validation**: kinds without highlight support (stackplot, boxplot, violinplot, hist, ecdf, pie, eventplot) now reject `highlight=True` with a clear error
- **Per-kind metrics validation**: kinds without metrics support (distribution, aggregation, isolated, event) reject any metric. Kinds without temporal support reject `ma`, `std_band` and `vband`
- **Composability validation**: `compose()` rejects kinds incompatible with multi-layer charts (boxplot, violinplot, hist, ecdf, pie, eventplot) with a descriptive message

### Changed
- **`ChartRenderer._ALIASES` references the centralised `KIND_ALIASES`**: a single source of truth for chart kind aliases, eliminating duplication between renderer and classification

## [2026-03-22 21:11]
### Changed
- **Config renamed from `charting` to `chartkit`**: TOML discovery now looks for `.chartkit/config.toml` (was `.charting.toml`/`charting.toml`), pyproject.toml uses `[tool.chartkit]` (was `[tool.charting]`), user config in `~/.config/chartkit/` and `%APPDATA%/chartkit/` (was `charting/`). Breaking change -- existing configs must be migrated manually
- **Example config moved to `.chartkit/config.example.toml`**: replaced `charting.example.toml` at the project root. The new location follows the dotfolder convention and sits next to the user's config
- **`.gitignore` updated**: `.chartkit/config.toml` ignored to prevent accidentally committing a user config

### Removed
- **`charting.example.toml`**: replaced by `.chartkit/config.example.toml`
- **Support for `.charting.toml`/`charting.toml` at the root**: discovery simplified to look only for `.chartkit/config.toml`

## [2026-02-20 11:47]
### Changed
- **Collision: unified artist dispatch via `_classify_artist()`**: duplicated Artist -> `_PathObstacle` conversion logic in `_collect_obstacles()` and `_collect_passive_obstacles()` extracted into a single function with structural dispatch (Collection > Patch > Line > extent fallback)
- **Debug overlay distinguishes passive lines from passive shapes**: unfilled passive obstacles (lines) now render with line styling (transparent face, thin linewidth) instead of shape styling -- facecolor simplified to depend only on `_filled`
- **Auto-rotation escalates to 90 degrees when the configured angle does not resolve overlap**: `apply_tick_rotation()` with `"auto"` now applies the configured angle first and, if overlap persists, escalates to 90 degrees. Rotation logic extracted into the `_apply_angle()` helper
- **Moving average and std_band centre line promoted to active obstacles**: `register_passive()` replaced by `register_artist_obstacle(filled=False)` -- moving average lines and the standard deviation band's centre now cause real repulsion in the collision engine, not just appear in the debug overlay

### Added
- **Area fills registered as passive obstacles**: `fill_between` PolyCollections from the area enhancer are now registered via `register_passive()`, making area fills visible in the collision engine's debug overlay

## [2026-02-20 10:44]
### Changed
- **Collision engine: cost-based candidate selection**: the greedy system (first free candidate wins) replaced by a continuous cost function with 3 weighted components -- distance from anchor (w=1.0), axis preference (w=3.0) and edge proximity (w=5.0). The solver now evaluates every valid candidate and picks the cheapest
- **Proactive candidates in 8 cardinal directions**: the new `_generate_proactive_candidates()` positions candidates at N/NE/E/SE/S/SW/W/NW at multiple distances (configurable via `candidate_distances`), with diagonal normalisation for uniform distance
- **Reactive candidates renamed**: `_compute_displacement_options()` renamed to `_generate_reactive_candidates()` -- snap-to-edge semantics preserved as a complement to the proactive candidates
- **Anchor bbox snapshot**: `_resolve_all()` now captures the original bounding boxes before any movement, so the cost function measures distance to the real anchor point

### Added
- **`CollisionConfig.candidate_distances`**: tuple of distance multipliers (in label heights) for proactive candidate generation. Default: `(1.0, 1.5, 2.0)`
- **`CollisionConfig.edge_margin_factor`**: edge margin as a fraction of label height. Labels within that margin receive an increasing penalty. Default: `1.0`
- **`_edge_proximity_cost()`**: linear penalty when a label is near any axes border -- returns 0.0 when safely away, scaling to 1.0 when touching
- **`_compute_placement_cost()`**: unified cost function combining normalised distance, axis preference and edge proximity
- **Tests for proactive candidates and the cost function**: `TestProactiveCandidates` (8-direction generation, bounds check, diagonal normalisation), `TestPlacementCost` (monotonicity, axis preference, edge penalty), `TestBestCostSelection` (realistic resolution with two overlapping labels)

### Removed
- **`_axis_priority()`**: replaced by the continuous `_compute_placement_cost()` -- a discrete sort by priority bins does not scale to multi-criteria evaluation
- **Diagonal fallback in `_find_free_position()`**: eliminated -- proactive candidates in 8 directions already cover diagonals natively

## [2026-02-20 02:13]
### Added
- **`_internal/frequency.py`**: a new shared module for frequency detection and display -- centralises `FREQ_ALIASES`, `normalize_freq_code()`, `infer_freq()` (previously in `transforms/_validation.py`) and adds `FREQ_DISPLAY_MAP` with short pt-BR labels (D, DU, S, M, T, A) plus `freq_display_label()` for conversion
- **Frequency-aware metrics**: `MetricRegistry.register()` accepts `uses_freq=True` -- marked metrics receive `detected_freq` automatically via `MetricRegistry.apply()`, which infers the frequency once and propagates it to every metric that needs it
- **`{freq}` placeholder in metric labels**: `moving_average_format` and `std_band_format` now support `{freq}` to display the detected data frequency (e.g. "MM12M" for a 12-month moving average) -- opt-in via TOML config
- **`draw_debug_overlay()` and `draw_composed_debug_overlay()`**: standalone functions for the debug overlay with updated geometry -- called after `finalize_chart()` so they reflect the final axes position (tick rotation, subplots_adjust)

### Changed
- **Debug overlay decoupled from collision resolution**: `resolve_collisions()` and `resolve_composed_collisions()` no longer take `debug` -- the overlay is now a separate pipeline step (step 9 in engine, step 7 in compose), guaranteeing the geometry reflects the final layout
- **`infer_freq()` accepts `pd.Index` directly**: in addition to DataFrame and Series, simplifying use in MetricRegistry where x_data may be an Index
- **`ma` and `std_band` marked `uses_freq=True`**: moving average and standard deviation band labels display the frequency when available

### Removed
- **`_infer_freq()` and `_normalize_freq_code()` from `transforms/_validation.py`**: moved to `_internal/frequency.py` as `infer_freq()` and `normalize_freq_code()` (public API of the internal module)
- **`_ANCHORED_PREFIXES` and `FREQ_ALIASES` from `transforms/_validation.py`**: moved to `_internal/frequency.py`
- **`debug` parameter of `resolve_collisions()` and `resolve_composed_collisions()`**: replaced by standalone overlay functions

## [2026-02-20 01:07]
### Added
- **Debug logging in the internal pipeline**: full instrumentation with `logger.debug()` at the key points of the plotting flow -- `extract_plot_data` (x/y/rows), `create_figure` (figsize/grid), `apply_legend` (handles/skip), `finalize_chart` (steps applied), `coerce_axis_limits` (conversions), `apply_tick_formatting` (locator type/freq/format)
- **`tick_freq` validation via Pydantic**: `validate_plot_params()` now validates `tick_freq` with the `TickFreq` Literal type, catching invalid values before they reach the tick engine
- **Type validation on `tick_rotation`**: a defensive guard rejects values that are neither `int` nor `"auto"`, with a descriptive `ValidationError`
- **Complete docstrings across the public API**: Args/Attributes documentation in `ChartingAccessor` (plot, layer, transforms), `TransformAccessor` (plot with an explicit signature, layer, transforms), `PlotResult` (save, show, axes, figure), `Layer`, `create_layer()`, `MetricSpec`, `MetricRegistry.apply()`, `ChartingTheme` properties, and all 17 config models in `settings/schema.py`
- **Centralised `TickFreq` type**: a new Literal type in `plot_validation.py` reused by `tick_formatting.py` and `PlotParamsModel`

### Changed
- **`TransformAccessor.plot()` with an explicit signature**: replaced the opaque `**kwargs` with every typed parameter (x, y, kind, title, units, source, highlight, metrics, legend, xlabel, ylabel, xlim, ylim, grid, tick_rotation, tick_format, tick_freq, collision, debug) -- enabling autocomplete and type checking in the IDE
- **`ValidationError` instead of `ValueError`**: `tick_formatting.py` and `tick_rotation.py` now use `chartkit.exceptions.ValidationError` for invalid input, consistent with the rest of the library
- **Data extraction logging moved to `extraction.py`**: the x/y_columns/rows debug log moved from `engine.py` to `extract_plot_data()`, where the extraction logic actually lives
- **`_validate_layers()` propagates `tick_freq`**: compose validation now passes `tick_freq` to `validate_plot_params()`, guaranteeing the same validation as a direct plot

## [2026-02-19 23:45]
### Added
- **`_internal/pipeline.py`**: a new module with shared pipeline steps (`create_figure`, `apply_legend`, `finalize_chart`) -- eliminating duplication between engine and compose
- **`RenderContext`**: a frozen dataclass in `charts/_helpers.py` encapsulating config, colour cycle, user_color, zorder and pre-processed y_data for enhancers
- **`prepare_render_context()` and `resolve_color()`**: helpers extracting boilerplate repeated across every enhancer (config loading, Series->DataFrame coercion, colour resolution)
- **Thread-safety in `ConfigLoader`**: `threading.Lock` with double-checked locking in `configure()`, `reset()` and `get_config()`

### Changed
- **Enhancers unified via RenderContext**: all 9 enhancers (area, ecdf, eventplot, hist, stacked_bar, stackplot, stairs, statistical, stem) and `ChartRenderer` now use `RenderContext` instead of repeating config/colour/zorder boilerplate individually
- **Engine and compose unified via the pipeline**: duplicated steps (theme.apply, figure creation, tick formatting, tick rotation, axis limits, labels, decorations) extracted into shared functions in `pipeline.py`
- **`apply_y_origin()` generalised**: a new `axis` parameter lets the same function serve vertical (y) and horizontal (x) bars, eliminating duplicated logic in the barh enhancer
- **`compute_bar_offsets()` used in the bar enhancer**: replaced an inline offset calculation with the existing helper
- **`theme.apply()` resets the font cache**: invalidates `_font` before reloading config, avoiding a stale font after reconfiguration

### Removed
- **`_apply_composed_legend()`** from `compose.py` -- replaced by the shared `apply_legend()`
- **`ChartingPlotter._apply_legend()`** from `engine.py` -- replaced by the same shared function
- **Duplicated pipeline steps**: ~50 lines of identical code removed between engine and compose (theme.apply, plt.subplots, grid override, tick formatting, tick rotation, axis limits, labels, title, footer)
- **Duplicated barh origin logic**: 12 lines of manual xlim calculation in the barh enhancer, replaced by `apply_y_origin(axis="x")`

## [2026-02-19 21:21]
### Added
- **Smart tick alignment**: ticks positioned at real data points instead of fixed calendar boundaries -- end-of-quarter quarterly data (Mar/Jun/Sep/Dec) now gets ticks on the correct months, without drifting to Jan/Apr/Jul/Oct
- **Tick frequency auto-inference**: when `tick_freq` is not specified, `pd.infer_freq()` detects the temporal pattern and aligns ticks automatically for sparse frequencies (quarterly, semestral, annual)
- **Phantom tick clipping**: removes ticks outside the real data range, caused by xlim padding (common in bar charts)
- **`coerce_axis_limits()`**: `xlim`/`ylim` now accept strings (`"2024-01-01"`, `"100"`) with automatic conversion to datetime or float
- **`AxisLimits` type alias**: a semantic type for axis limit tuples supporting str/int/float/datetime/Timestamp/None

### Changed
- Tick frequency `"quarter"` now uses end-of-quarter months (3,6,9,12) instead of start-of-quarter (1,4,7,10)
- Tick frequency `"semester"` now uses end-of-semester months (6,12) instead of start (1,7)
- Horizontal alignment of rotated tick labels changed from angle-dependent (right/left) to always `center`
- `apply_tick_formatting()` takes a new `x_data` parameter for data-aware tick positioning

### Removed
- **`add_right_margin()`**: function removed along with its calls in engine and compose -- a right margin for highlight labels is no longer needed

## [2026-02-18 22:36]
### Changed
- **Collision engine modularised**: the monolithic `_internal/collision.py` (877 lines) split into an `_internal/collision/` package with 4 specialised sub-modules: `_registry.py` (global state and artist registration), `_obstacles.py` (PathObstacle and obstacle collection), `_engine.py` (collision resolution), `_debug.py` (debug overlay)
- Public API kept identical via re-exports in `__init__.py`

## [2026-02-18 21:53]
### Added
- **Financial edge case fixtures** (`conftest.py`): `irregular_daily_prices` (irregular dates), `quarterly_rates` (quarterly data), `gapped_prices` (prices with NaN gaps) -- real problematic scenarios
- **Integration tests** (`tests/integration/`): `test_accessor_pipeline.py` and `test_end_to_end.py` for end-to-end validation of the full flow
- **Formatting tests** (`tests/formatting/`): `test_axis_formatters.py` and `test_highlight.py` in a dedicated directory
- **Financial edge case tests** in transforms: quarterly data with `variation`, irregular timeseries, NaN gaps in `drawdown`, a -100% rate in `accum`, multi-column in `normalize`/`zscore`/`drawdown`/`accum`
- **`MetricRegistry.apply` tests** (`test_registry.py`): validation of handler calls with ax/data and parameter passing

### Changed
- **Test suite rewritten**: fully reorganised by business domain instead of implementation detail -- tests focus on behaviour and correctness, not on type-checking inputs
- **Descriptive test names**: classes and methods renamed to express intent (`TestAccumKnownValues`, `test_minus_100_rate_zeroes_product`, etc.)
- **Docstrings on every test**: each test documents what it validates (`"""[1%, 2%, 3%] window=3 -> compound product."""`)
- **Charts tests restructured**: individual tests per enhancer (`test_area_enhancer.py`, `test_bar_enhancer.py`, `test_stacked_bar_enhancer.py`) plus the generic renderer (`test_renderer.py`)
- **Collision tests consolidated**: `test_collision_engine.py` replaces `test_collect_obstacles.py` and `test_pos_to_numeric.py`
- **Composing tests reorganised**: `test_compose_pipeline.py` and `test_layer_validation.py` replace 6 separate files
- **Settings tests focused**: `test_config_precedence.py` replaces `test_deep_merge.py`, `test_loader.py` and `test_schema.py`
- **Transform tests trimmed**: `test_freq_resolution.py` and `test_input_pipeline.py` consolidate cross-cutting validation

### Removed
- **41 old test files** deleted: granular tests exercising implementation details (input type acceptance, empty raises, internal state access) replaced by behaviour-focused tests
- **Redundant input type tests**: `test_accepts_series`, `test_accepts_dataframe` removed from every transform test -- they tested framework coercion, not business logic
- **Generic empty-raises tests**: removed from `accum`, `annualize`, `diff`, `normalize`, `zscore` -- empty input validation is the coercion layer's responsibility
- **Directories `tests/decorations/`, `tests/engine/`, `tests/internal/`**: removed along with their `__init__.py`

## [2026-02-18 21:11]
### Added
- **Axis controls** (`xlabel`, `ylabel`, `xlim`, `ylim`) in `plot()`, `compose()` and the accessor: direct control of axis labels and limits without reaching for matplotlib
- **Per-call grid** (`grid` parameter): `grid=True/False` in `plot()` and `compose()` enables/disables the grid for a specific chart, taking precedence over global config
- **`GridConfig`** (`settings/schema.py`): structured config replacing the old `grid: bool` -- `enabled`, `alpha`, `color`, `linestyle` and `axis` fields configurable via TOML
- **Tick formatting system** (`_internal/tick_formatting.py`): control of temporal tick frequency and format on the X axis via `tick_format` (strftime) and `tick_freq` (`"day"`, `"week"`, `"month"`, `"quarter"`, `"semester"`, `"year"`) -- uses `matplotlib.dates` locators/formatters
- **`TicksConfig.date_format` and `TicksConfig.date_freq`**: config fields for tick formatting, configurable via TOML and env vars
- **Area chart fill-between semantics**: 2 columns now fill between the pair (spread/interval) instead of independently from zero; 3+ columns keep the independent behaviour
- **Passive obstacles in the debug overlay**: passive obstacles rendered in dashed grey under `debug=True`
- **Stackplot registers PolyCollections as passive**: the collision engine now recognises stacked areas as passive obstacles

### Changed
- **Theme applies the full grid config** (`theme.py`): rcParams now include `axes.grid.axis`, `grid.alpha`, `grid.color` and `grid.linestyle` in addition to `axes.grid`
- **Debug overlay refactored** (`collision.py`): a `_draw_obstacles()` helper with passive support and `_collect_passive_obstacles()` for cross-axis collection
- **`label_padding_px` default reduced** from 4.0 to 2.0 (`CollisionConfig`)
- **Tick rotation: alignment for negative angles** corrected from `"center"` to `"left"`
- **Non-PathCollection collections left unregistered** in the renderer's post-render -- auto-detected by `_collect_obstacles()` instead of explicit passive registration
- **`charting.example.toml` updated** with a `[layout.grid]` section and `date_format`/`date_freq` fields under `[ticks]`

### Removed
- **`fill_between` parameter** from `plot()`, `compose()`, `Layer`, `create_layer()`, the accessor and `TransformAccessor` -- functionality absorbed by the area enhancer (2-column mode)
- **`overlays/fill_between.py`** -- whole module deleted
- **`add_fill_between()` from the public overlays API**
- **`scripts/test_tick_rotation.py`** -- replaced by `test_axis_controls.py`

## [2026-02-18 15:30]
### Added
- **`collision` parameter** in `plot()`, `compose()` and the accessor: `collision=False` fully disables the collision resolution engine -- useful for simple charts where resolution is unnecessary or interferes with the layout
- **Automatic bottom margin adjustment** (`_internal/tick_rotation.py`): after rotating tick labels, `_adjust_bottom_margin()` pushes the axes up if the labels overlap the footer area

### Changed
- **Conditional collision engine** (`engine.py`, `compose.py`): registering the legend as an obstacle and resolving collisions now run only when `collision=True` (the default), avoiding unnecessary processing
- **Rotation skipped when the angle is zero** (`tick_rotation.py`): an early return avoids setting rotation/ha unnecessarily and skipping the margin adjustment

## [2026-02-18 15:07]
### Added
- **`units="x"` (multiplier formatter)**: a new Y axis format for data representing multiples (P/E, EV/EBITDA, etc.) -- formats values as `12,3x`, `0,8x`, respecting the locale's decimal separator

## [2026-02-18 14:48]
### Added
- **Tick rotation system** (`_internal/tick_rotation.py`): auto-rotation of X axis labels to prevent overlap -- `"auto"` mode detects overlap via `get_window_extent()` and rotates only when necessary; fixed mode accepts an angle in degrees
- **`TicksConfig`** (`settings/schema.py`): a new sub-config with `rotation` (`"auto"` or an angle) and `auto_rotation_angle` (default 45) -- configurable via TOML and env vars
- **`tick_rotation` parameter** in `plot()`, `compose()` and the accessor: per-call control of tick rotation, taking precedence over global config
- **`[ticks]` section in `charting.example.toml`**: an example configuration with `rotation` and `auto_rotation_angle`

### Changed
- **Engine pipeline** (`engine.py`): a new step 5d applies tick rotation after the right margin and before the legend
- **Compose pipeline** (`compose.py`): tick rotation inserted as step 4, renumbering subsequent steps (5-8)

## [2026-02-18 14:25]
### Added
- **9 new chart enhancers** (`charts/enhancers/`): specialised support for area, ecdf, eventplot, hist, pie, stackplot, stairs, statistical (boxplot/violinplot) and stem -- each registered via `@ChartRenderer.register_enhancer` with colour cycling, labels and the correct kwargs for matplotlib's API
- **Horizontal bar chart** (`charts/enhancers/bar.py`): `kind='barh'` with multi-column (grouped) support, sort, colour cycling and y_origin
- **`compute_bar_offsets()`** (`charts/_helpers.py`): computes width and per-column offsets for grouped bar charts (vertical and horizontal)
- **`_UNSUPPORTED_KINDS`** (`charts/renderer.py`): an explicit blocklist for incompatible chart kinds (imshow, contour, quiver, etc.) with descriptive error messages
- **Collection auto-detection in the collision engine** (`collision.py`): `ax.collections` from sibling axes are now auto-detected as obstacles -- `PathCollection` (scatter) as filled, others as passive
- **Alias `area` -> `fill_between`** (`renderer.py`): `kind='area'` maps to `ax.fill_between()` via the enhancer
- **Tests for every new chart type** (11 files): test_area, test_barh, test_ecdf, test_eventplot, test_hist, test_pie, test_stackplot, test_stairs, test_statistical, test_stem, test_unsupported

### Changed
- **Collision engine unified with `_PathObstacle`** (`collision.py`): the dual system (bbox obstacles + `_LinePathObstacle`) replaced by a single `_PathObstacle` class that extracts real geometry from any Artist via factory functions (`_path_from_line`, `_path_from_patch`, `_path_from_collection`, `_path_from_extent`)
- **`register_artist_obstacle()` replaces `register_fixed()` + `register_line_obstacle()`**: a single API with `filled` (shape vs line) and `colocate` (skip for labels starting on their own line) parameters
- **`_collect_obstacles()` with dispatch by type**: takes a renderer, auto-detects collections in siblings, and dispatches registered artists by type (Line2D -> path, Collection -> paths, Patch -> patch transform, fallback -> extent)
- **`_resolve_all()` uses a unified `_PathObstacle` list**: conditional padding (obstacle_pad for filled, 0 for lines) instead of separating bbox and path obstacles
- **Post-render in `ChartRenderer`**: PathCollection (scatter) registered as a filled obstacle, other collections as passive -- alongside the existing Line2D
- **Scatter markers registered as passive** (`overlays/markers.py`): prevents highlight points from automatically becoming collision obstacles
- **Debug overlay updated** (`collision.py`): renders every geometry (filled with a face colour, unfilled with a thick edge), replacing the previous translucent-rect system
- **Documentation updated**: architecture.md, extending.md, internals.md, collision.md and api.md reflect the new unified API

### Removed
- **`register_fixed()`**: replaced by `register_artist_obstacle(ax, artist, filled=True)`
- **`register_line_obstacle()`**: replaced by `register_artist_obstacle(ax, artist, filled=False, colocate=True)`
- **`_LinePathObstacle`**: replaced by the unified `_PathObstacle`
- **`_obstacles` and `_line_obstacles` WeakKeyDictionaries**: consolidated into `_artist_obstacles`
- **Type alias `Obstacle`**: unnecessary -- everything is a `_PathObstacle`

## [2026-02-13 21:14]
### Added
- **`ChartRenderer` with generic rendering** (`charts/renderer.py`): a new rendering engine that dispatches to `ax.{kind}()` for any matplotlib chart type, removing the need to register each type manually
  - Enhancers for complex types via `@ChartRenderer.register_enhancer("name")` -- bar grouping and stacking keep their specialised logic
  - The `Enhancer` Protocol defines the interface for specialised handlers
  - `_generic_render()` with automatic colour cycling, per-type kind defaults, and highlight inference via a patch snapshot diff
  - `_ALIASES` maps `"line"` -> `"plot"` (matplotlib uses `ax.plot()`)
  - `_KIND_DEFAULTS` applies per-kind defaults (e.g. `linewidth` for `plot`)
  - Post-render: a snapshot diff of `ax.lines` registers new Line2D as collision obstacles
  - Public `validate_kind()` for eager validation in `create_layer()`
- **`charts/enhancers/` package**: bar and stacked_bar enhancers moved into a dedicated subpackage, auto-registered via import in `__init__.py`

### Changed
- **`ChartKind` is now `str`** (`engine.py`): the type widened from `Literal["line", "bar", "stacked_bar"]` to `str` -- any valid matplotlib Axes method (scatter, step, stem, hist, etc.) works automatically
- **Engine and compose use `ChartRenderer.render()`**: unified dispatch replaces `ChartRegistry.get(kind)` plus a manual call in both pipelines
- **Layer validation via `ChartRenderer.validate_kind()`** (`layer.py`): eager validation now raises `ValidationError` (instead of `RegistryError`) for invalid kinds
- **Tests updated**: the `plot_bar` import points to `charts/enhancers/bar.py`, and the layer test expects `ValidationError` instead of `RegistryError`

### Removed
- **`ChartRegistry`** (`charts/registry.py`): whole class deleted -- replaced by `ChartRenderer`
- **`charts/line.py`**: line rendering is now handled generically by `ChartRenderer._generic_render()`
- **`charts/bar.py` and `charts/stacked_bar.py`** (top-level): moved to `charts/enhancers/` as registered enhancers

## [2026-02-13 00:48]
### Fixed
- **Right margin for highlight labels** (`engine.py`): the single-chart pipeline now applies `add_right_margin()` (a 6% xlim expansion) when highlights are present, preventing labels from being clipped at the last datapoint -- the behaviour already existed in `compose()` but was missing from `engine.py`
- **Implicit `ax.lines[-1]`** (`line.py`): explicitly capture the return of `ax.plot()` instead of relying on the order of `ax.lines`, preventing fragility with hooks/callbacks

### Changed
- **Compose pipeline validation simplified** (`compose.py`, `layer.py`): removed a redundant triple validation -- `create_layer()` validates eagerly, and `_validate_layers()` now contains only compose-level checks (empty layers, all-right, legend)
- **`MetricRegistry.apply()` accepts `str` directly** (`registry.py`): the `str -> [str]` normalisation is internalised in the registry, removing duplicated isinstance checks from `engine.py` and `compose.py`
- **Stat line API with explicit parameters** (`reference_lines.py`): `add_ath_line`, `add_atl_line` and `add_avg_line` take `color`, `linestyle`, `label`, `linewidth` and `series` instead of `**kwargs`
- **Consistent `prepare_categorical_axis`** (`stacked_bar.py`): uses the return of `prepare_categorical_axis()` directly (as `bar.py` does), removing a manual `np.arange` and a redundant call
- **Imports via the facade** (`charts/`, `_internal/highlight.py`): every overlay import now uses `from ..overlays import ...` via the package `__init__.py`
- **Type alias `Obstacle`** (`collision.py`): `Obstacle = Artist | _LinePathObstacle` for honest type annotations in `_collect_obstacles`, `_resolve_all` and `_draw_debug_overlay`
- **Top-level import of `ValidationError`** (`_validation.py`): moved from an unnecessary deferred import to top-level alongside the other pydantic imports

### Added
- **`resolve_series()` helper** (`_internal/extraction.py`): extracts a column from a DataFrame with a fallback to the first, eliminating a duplicated block in 3 overlays
- **Shared `add_right_margin()`** (`_internal/extraction.py`): extracted from `compose.py` for use in both pipelines (engine + compose)
- **`__all__` in 4 modules**: `temporal.py`, `reference_lines.py`, `moving_average.py`, `bands.py` -- aligned with the project convention

### Removed
- **Dead code in `collision.py`**: `_LinePathObstacle.get_visible()` (never called), the `movement` parameter in `_compute_displacement_options` (always `"xy"`), and the redundant `collision` parameter in `_add_connectors`
- **`_validate_params` static method** (`engine.py`): pure delegation removed, the call site uses `validate_plot_params()` directly
- **`_needs_right_axis()` one-liner** (`compose.py`): inlined into its single call site
- **Obsolete tests** (`test_layer.py`, `test_validate.py`): redundant validation tests removed -- coverage kept via the full pipeline

## [2026-02-12 23:40]
### Changed
- **Collision engine: path-based detection** (`collision.py`): `_LineSampleObstacle` (N obstacle objects per data point) replaced by `_LinePathObstacle` (1 object per line), using `Path.intersects_bbox()` (Cython/C) for continuous, exact detection along the entire curve
  - Bulk transform via numpy instead of N individual calls to `ax.transData.transform()`
  - Quick-reject via `get_extents().overlaps()` before the detailed per-segment check
  - `local_bbox()` filters vertices by X-range with a numpy mask to generate displacement candidates
  - Display path cached per `_LinePathObstacle` (the transform is stable during a resolution pass)
  - Reduction from ~3000 Python objects to 1 per line, an estimated ~10s to <1s on long series
- **`_resolve_all()` separates bbox and path obstacles**: a new flow distinguishes discrete obstacles (patches, labels) from continuous ones (line paths), with same-axis co-location logic preserved via `obs.intersects()` instead of `raw_bbox.overlaps(obs_ext)`
- **`_find_free_position()` validates against paths**: the new `_position_is_free()` unifies validation against bbox overlaps and path intersections, used both in the candidate check and the diagonal fallback
- **`_collect_obstacles()` simplified**: the per-data-point sampling loop (with an `isfinite` check, zip, and creation of N `_LineSampleObstacle`) replaced by direct creation of 1 `_LinePathObstacle` per registered line

### Added
- **`debug=True` in `plot()` and `compose()`**: parameter propagated down to `resolve_collisions()` / `resolve_composed_collisions()`, enabling a visual collision overlay without external scripts
- **`_draw_debug_overlay()`** (`collision.py`): an internal function rendering translucent bboxes over the figure -- fixed obstacles (red), line paths (orange with a PathPatch), moveable labels (blue), and the axes bounds (green)
- **`_position_is_free()`** (`collision.py`): a helper validating a position against a list of bbox obstacles and a list of path obstacles in a single call

### Removed
- **`_LineSampleObstacle`**: whole class deleted (replaced by `_LinePathObstacle`)
- **`isfinite` import**: its only use was in the point sampling loop, removed with it

## [2026-02-12 17:52]
### Added
- **Chart composition system** (`composing/`): the new `compose()` function combines multiple `Layer` objects into one chart with dual-axis support
  - `Layer` (frozen dataclass) captures plotting intent without rendering; `create_layer()` validates eagerly
  - `AxisSide = Literal["left", "right"]` for per-layer axis control
  - `df.chartkit.layer()` on `ChartingAccessor` and `TransformAccessor` to create layers
  - `compose(*layers, title, source, legend, figsize)` renders every layer, consolidates the legend from both axes, and returns a `PlotResult`
  - `_ComposePlotter` satisfies the `Saveable` Protocol to integrate with `PlotResult`
  - Validation: requires at least one layer, rejects all-on-the-right, warns on conflicting units on the same axis
  - Automatic right margin when highlights are present (avoids labels clipped at the border)
- **`Saveable` Protocol** (`result.py`): a structural interface for objects that save figures -- `PlotResult.plotter` accepts `ChartingPlotter` or `_ComposePlotter`
- **Cross-axis collision resolution** (`resolve_composed_collisions`): merges labels from every axes into a single pool and resolves in pixel space, respecting each axes' individual transforms
- **Line path obstacle sampling**: `_LineSampleObstacle` creates virtual obstacles at each data point of registered lines, letting labels avoid the visible path of the line (Line2D bboxes span the entire area and are useless as a collision target)
- **`register_line_obstacle()`**: a new API to register a Line2D as a collision obstacle via point sampling
- **Highlight mode `"all"`** in `markers.py`: annotates every data point (not just last/max/min), with automatic vertical positioning by the value's sign
- **Label offset** (`_apply_label_offset`): configurable vertical breathing room between label and data point via `markers.label_offset_fraction`
- **`add_title()` as a reusable decoration** (`decorations/title.py`): the title extracted from the engine into its own module, available to composition and simple plotting
- **Shared `_internal` modules**: logic extracted from the engine for reuse between `engine.py` and `compose.py`
  - `extraction.py`: `extract_plot_data()` and `should_show_legend()` -- data selection and legend logic
  - `formatting.py`: the `FORMATTERS` dispatch table for Y axis formatters
  - `highlight.py`: `normalize_highlight()` for highlight input normalisation
  - `plot_validation.py`: `validate_plot_params()`, `PlotParamsModel` and `UnitFormat`
  - `saving.py`: `save_figure()` with relative path resolution against the charts directory
- **Categorical index support** in bar/stacked_bar: `is_categorical_index()` and `prepare_categorical_axis()` for textual indices
- **Bar chart `sort`**: ascending/descending ordering for single-column bar charts
- **Bar chart `color='cycle'`**: per-bar colour cycling using the theme palette (single-column only)
- **`MarkersConfig.label_offset_fraction`**: a new config field controlling labels' vertical breathing room
- **`CollisionConfig.movement` typed as `Literal["x", "y", "xy"]`**: static validation instead of a free-form string

### Changed
- **Collision engine rewritten**:
  - `_resolve_all()` unifies resolution against fixed obstacles and between labels (replacing `_resolve_against_fixed` + `_resolve_between_moveables`)
  - `_find_free_position()` generates candidates from every colliding obstacle, validates against all, with a diagonal fallback
  - `_pad_bbox()` replaces `_get_padded_bbox()` (fixed padding, simpler)
  - `_compute_displacement_options()` returns every option (replacing `_best_displacement()`, which returned only the best)
  - `_shift_label()` uses `label.axes` instead of taking an explicit ax
  - `_add_connectors()` groups labels by parent axes for correct transforms
  - `_collect_obstacles()` walks sibling axes (twinx) for cross-axis collision -- detecting patches, labels and line samples from every shared axis
  - `fig.canvas.draw()` replaced by `fig.draw_without_rendering()` (lighter)
- **`bar.py` renders multi-column as grouped bars**: individual `ax.bar()` calls with colour cycling and per-column offsets (replacing pandas' `.plot(kind="bar")`, which used a categorical axis)
- **`highlight` mandatory in `bar.py`/`stacked_bar.py`**: the type changed from `list | None = None` to `list` (normalisation done by the caller)
- **`engine.py` simplified**: private methods extracted into `_internal` and `decorations`, the engine now delegates
- **Legend registered as a fixed obstacle** for collision resolution
- **`to_month_end()` consolidates monthly observations**: keeps only the chronologically last observation per month instead of allowing duplicate indices
- **`detect_bar_width()` more robust**: `_coerce_datetime_index()` handles object-dtype and non-datetime indices gracefully
- **`_resolve_x_position()` in markers**: handles duplicate indices by returning the first scalar match
- **Tests updated**: matplotlib backend `Agg` forced in conftest, imports updated to the new `_internal` paths

### Removed
- **`_best_displacement()`**: replaced by `_compute_displacement_options()` + `_find_free_position()`
- **`_get_padded_bbox()`**: replaced by `_pad_bbox()`
- **`_resolve_against_fixed()` and `_resolve_between_moveables()`**: unified into `_resolve_all()`
- **`_FORMATTERS`, `_normalize_highlight()`, `_PlotParams`, `UnitFormat` from the engine**: moved to `_internal/`
- **`_apply_title()` from the engine**: moved to `decorations/title.py`
- **`_apply_decorations()` from the engine**: replaced by direct calls to `add_footer()` and `add_title()`
- **Save logic from the engine**: moved to `_internal/saving.py`
- **`plot_lines` accumulator in `line.py`**: unused list removed
- **Tests `test_best_displacement.py` and `test_get_padded_bbox.py`**: API replaced by the new collision engine

## [2026-02-12 00:53]
### Added
- **Test suite with 283 tests**: full coverage of the modules with their own logic, preparing the library for open source
  - `tests/transforms/` (150 tests): validation, coercion, frequency resolution, pydantic models, and all 8 transform functions (variation, accum, diff, normalize, annualize, drawdown, zscore, to_month_end) plus TransformAccessor delegation
  - `tests/metrics/` (30 tests): `MetricRegistry.parse()` with simple/compound/targeting/labelled specs, type coercion, errors, and registry registration/lifecycle
  - `tests/settings/` (39 tests): _deep_merge, find_project_root/find_config_files, ConfigLoader (cache, reset, path resolution, TOML loading), ChartingConfig defaults and env vars
  - `tests/collision/` (16 tests): _best_displacement with exact geometry (Bbox), _pos_to_numeric, _get_padded_bbox with a mock artist
  - `tests/engine/` (13 tests): _normalize_highlight (valid/invalid modes, bool, list) and _PlotParams validation (Pydantic)
  - `tests/test_formatters.py` (15 tests): currency, compact_currency, percent, human_readable and points formatters with a mocked config
- **Shared fixtures** (`tests/conftest.py`): realistic financial DataFrames (fixed seed rng=42), edge cases (empty, all-NaN, constant, non-datetime index)
- **Per-module fixtures**: known-value data for transforms (pre-computed results), registry snapshot/restore for metrics, config isolation for settings
- **pytest config** (`pyproject.toml`): `[tool.pytest.ini_options]` with strict-markers, strict-config, filterwarnings error plus an ignore for matplotlib UserWarning

## [2026-02-11 21:18]
### Added
- **Custom exception hierarchy**: `ValidationError`, `RegistryError` and `StateError` with multiple inheritance from the built-in types (`ValueError`, `LookupError`, `RuntimeError`) to stay compatible with existing `except ValueError`
- **`disable_logging()`**: a new public function to revert `configure_logging()` -- removes handlers and disables the logger
- **Structured logging throughout**: `logger.debug` for internal tracing (plot params, dispatch, collision counts, transform resolution) and `logger.warning` for potential problems (empty series, NaN data, inverted dates, differing lengths)
- **`diff(periods=0)` validation**: rejected with a descriptive message (it returns all-zeros, almost certainly a user error)
- **`zscore(window=1)` validation**: rejected (the std of a single value is undefined and would produce all-NaN)
- **`BME`/`BMS` frequencies (Business Month End/Start)**: supported in `FREQ_ALIASES` and `FREQ_PERIODS_MAP`
- **`BQE`/`BQS`/`BYE`/`BYS` frequencies (Business Quarter/Year)**: added to `FREQ_PERIODS_MAP` and restored in `_ANCHORED_PREFIXES` for auto-detection via `pd.infer_freq()`
- **Specific error for a detected but unsupported frequency**: `resolve_periods()` now distinguishes "could not detect" from "detected but not supported", with a message listing the valid frequencies

### Changed
- **`ValueError`/`RuntimeError`/`TypeError` migrated to the custom hierarchy**: every internal raise now uses `ValidationError`, `RegistryError`, `StateError` or `TransformError` -- catching `ChartKitError` captures them all
- **`configure_logging()` idempotent**: repeated calls remove the previous handler before adding a new one, avoiding duplicated logs
- **`_PctChangeParams` renamed to `_FreqResolvedParams`**: a more descriptive name (used by `variation` and `annualize`)
- **`normalize(base_date)` with error handling**: an invalid `pd.Timestamp()` now raises `TransformError` instead of a raw exception
- **`diff()` and `zscore()` validated via pydantic**: parameters validated before execution, with clean error messages
- **`TransformsConfig.normalize_base` and `accum_window` validated as `PositiveInt`**: config with values <= 0 rejected at load
- **Logs standardised in English**: warning messages in `bar.py` and `stacked_bar.py` converted from Portuguese to English

### Fixed
- **Incomplete `_ANCHORED_PREFIXES`**: the `BQE-`/`BQS-`/`BYE-`/`BYS-` prefixes had been removed, breaking auto-detection for business quarter/year data
- **Stripping the multiplier from freq codes produced wrong calculations**: `"2D"` (bi-daily) was normalised to `"D"` (daily), producing incorrect periods. Multiplied frequencies now fall into the "not supported" error with a suggestion to use an explicit `periods=`
- **`coerce_input()` raised `TypeError` instead of `TransformError`**: inconsistent with the rest of the validation module

### Removed
- **Ambiguous aliases `"day"`, `"bday"`, `"week"`, `"month"`, `"quarter"`, `"year"` from `FREQ_ALIASES`**: they conflicted with `horizon='month'`/`'year'` in `variation()`. The existing aliases `"daily"`, `"business"`, `"weekly"`, `"monthly"`, `"quarterly"`, `"yearly"` cover the same cases without ambiguity
- **Underscore names from `__all__` in `_validation.py`**: `_FreqResolvedParams`, `_DiffParams`, `_ZScoreParams`, `_infer_freq`, `_normalize_freq_code` removed -- an internal module should not export private names

## [2026-02-10 05:00]
### Changed
- **`yoy()` and `mom()` unified into `variation(horizon)`**: a simplified API -- `variation(horizon='year')` replaces `yoy()`, `variation(horizon='month')` replaces `mom()`. The horizon is a semantic parameter rather than separate functions
- **`compound_rolling()` absorbed by `accum()`**: `accum()` now falls back to `config.transforms.accum_window` when the frequency cannot be inferred, covering `compound_rolling`'s use case
- **Config `rolling_window` renamed to `accum_window`**: reflects the transform consolidation -- the field now belongs exclusively to `accum()`
- **`MetricRegistry` uses a `_MetricEntry` NamedTuple**: replaces a raw tuple with a named type carrying `func`, `param_names`, `required_params` and `uses_series`. Required parameters are introspected via `inspect.signature`
- **`accum()` uses `np.prod` instead of `np.nanprod`**: more correct semantics -- NaN propagates rather than being silently ignored

### Added
- **Required parameter validation in metrics**: `MetricRegistry.parse()` now raises `ValueError` with a descriptive message when required params are missing (e.g. `"Metric 'ma' requires parameter(s): window"`)
- **Guard clauses in overlays**: `add_moving_average` validates `window >= 1`, `add_std_band` validates `window >= 2` and `num_std > 0`
- **Protection against non-finite values in formatters**: every formatter (currency, compact, %, human, points) returns `""` for `inf`/`NaN`, avoiding matplotlib crashes

### Removed
- **`yoy()`**: replaced by `variation(horizon='year')`
- **`mom()`**: replaced by `variation(horizon='month')`
- **`compound_rolling()`**: use case covered by `accum()` with a config fallback
