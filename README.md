# Soccer pass maps

Pass visualizations from **StatsBomb [open data](https://github.com/statsbomb/open-data)** using **[mplsoccer](https://mplsoccer.readthedocs.io/)** and **[statsbombpy](https://github.com/statsbomb/statsbombpy)**.

**Notebooks** (`.ipynb`) are the **original exploration**. They are **left as-is on purpose**: ad hoc cells, optional `%pip` / `!pip` lines, and wide dataframe outputs are part of that history. **No further README or code changes are required for the notebooks** unless you choose to edit them yourself.

**Maintained, reusable code** is in **`passmap_logic.py`**, the **`.py` scripts**, and **`tests/`** (shared logic, CLI entry points, and unit tests). The scripts mirror the notebook ideas but stay consistent with each other; they do not need to stay line-identical to the notebooks.

## What’s in this repo

### `individual-pass-maps.ipynb`

- Loads **UEFA Euro 2020** (`competition_id=55`, `season_id=43`) and focuses on **Italy vs Spain** in the semi-final (**match_id `3795220`**).
- Uses **mplsoccer** `Sbopen` for events and lineups, merges **substitution** times onto the lineup, and filters Italy’s passes (throw-ins excluded for player maps; separate logic for receipts).
- Builds a **multi-panel figure**: one small pitch per player with complete vs incomplete passes as arrows, pass counts and completion rate in the title strip, sub on/off minute markers where relevant, and a **team pass-receipt KDE heatmap** on the last panel.
- Adds presentation layers: **Google Scada** font via `FontManager`, **highlight_text** for colored stats, **cmasher** colormap for the heatmap, **StatsBomb logo** from the open-data repo, and **Italy / Spain flag images** (`ita.png`, `sp.png`) from the project folder.

### `team-pass-maps.ipynb`

- Targets the **African Cup of Nations** (`competition_id=1267`, `season_id=107`) and a **Nigeria** match (**match_id `3923881`**, titled in the plot as Nigeria vs Ghana in the AFCON final).
- Loads events with **statsbombpy** and **Sbopen**, keeps **Nigeria** events, extracts **passes**, keeps **successful** passes (null `outcome_name`), and trims the window to **before the first substitution** so the map reflects the main phase of play.
- Joins **jersey numbers** for passers and recipients, aggregates **average x/y** per jersey and **pass counts** between jersey pairs (filtering links with more than one pass).
- Draws a **single pitch**: flow lines between average positions (width scaled by pass volume) and **nodes** sized by touch volume, with **jersey numbers** annotated.

## Assets

- **`ita.png`** / **`sp.png`** — title flags for `individual-pass-maps.ipynb` and **`individual-passmap.py`**. Keep them in the project root next to those files (or change the `Image.open(...)` paths).

## Setup

1. Use Python 3.10+ (as used in local development).
2. Create and activate a virtual environment (for example `.venv` in this folder).
3. Install dependencies from the lockfile:

   ```bash
   pip install -r requirements.txt
   ```

   `requirements.txt` is a full `pip freeze` from this project’s `.venv` (pinned versions). The notebooks may still contain optional `%pip` / `!pip` cells; using the file above once per environment is enough.

   **Note:** `pywinpty` is Windows-only; on Linux or macOS, install on that OS and run `pip freeze` again if you need a platform-specific lockfile.

4. Open a notebook in Cursor/VS Code with the **Python** and **Jupyter** extensions, select the venv’s interpreter, then run cells top to bottom.

Data is fetched from the network on first use; large `DataFrame` displays can slow the UI—use `.head()` or `.shape` when exploring.

## Scripts and shared logic

- **`passmap_logic.py`** — pure pandas helpers: team **pass network** pipeline, **individual** helpers (`merge_sub_times_into_lineup`, `pass_receipts_for_team`, `passes_excluding_throw_in`, `roster_for_team`, `squad_size_and_sub_count`), `opponent_for_match`, and `SET_PIECE_TYPES` for documentation. Used by all three scripts below plus tests.
- **`passmap-with-input.py`** — CLI prompts for competition / season / home team; **jersey network** map (same idea as `team-pass-maps.ipynb`). Exploratory notebook-style lines are kept as **comments** next to the real pipeline.
- **`individual-passmap.py`** — single fixed match (Euro 2020 semi) using the **same** individual layout and shared helpers as **`tournament-passmaps.plot_pass_maps`**.
- **`tournament-passmaps.py`** — prompts for comp / season / team, loops matches, calls **`plot_pass_maps`** (6×4 grid, focal team only, sub times merged, receipt heatmap for that team—aligned with `individual-passmap.py`).

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

`pytest.ini` sets `pythonpath` to the repo root so `import passmap_logic` resolves. Tests live in **`tests/test_passmap_logic.py`** and cover lookups, filtering before first substitution (including **no substitution**), jersey merges, pass-network aggregation, and lineup sub times.

## License / data

StatsBomb open data is provided under their [terms](https://github.com/statsbomb/open-data); use accordingly for any public sharing of derived work.
