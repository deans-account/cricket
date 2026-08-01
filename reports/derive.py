from __future__ import annotations
from database.database import Database


def _last_preplay_ltp(con, market_id: str, selection_id: int, first_inplay: int | None):
    if first_inplay is None:
        row = con.execute(
            """SELECT last_traded_price FROM price_history
               WHERE market_id=? AND selection_id=? AND last_traded_price IS NOT NULL
               ORDER BY publish_time DESC LIMIT 1""",
            (market_id, selection_id),
        ).fetchone()
    else:
        row = con.execute(
            """SELECT last_traded_price FROM price_history
               WHERE market_id=? AND selection_id=? AND publish_time < ?
                 AND last_traded_price IS NOT NULL
               ORDER BY publish_time DESC LIMIT 1""",
            (market_id, selection_id, first_inplay),
        ).fetchone()
    return row[0] if row else None


def build_market_summary(path: str) -> dict:
    db=Database(path); db.initialise()
    count=0
    with db.connect() as con:
        markets=con.execute("SELECT * FROM markets ORDER BY market_time,market_id").fetchall()
        for market in markets:
            runners=con.execute(
                "SELECT * FROM runners WHERE market_id=? ORDER BY sort_priority,selection_id",
                (market['market_id'],),
            ).fetchall()
            by_role={r['runner_role']:r for r in runners}
            if not {'home','away','draw'}.issubset(by_role):
                continue
            first_inplay_row=con.execute(
                "SELECT MIN(publish_time) FROM price_history WHERE market_id=? AND in_play=1",
                (market['market_id'],),
            ).fetchone()
            first_inplay=first_inplay_row[0] if first_inplay_row else None
            vals={}
            for role in ('home','away','draw'):
                sid=by_role[role]['selection_id']
                mm=con.execute(
                    """SELECT MIN(last_traded_price),MAX(last_traded_price),COUNT(*)
                       FROM price_history WHERE market_id=? AND selection_id=?
                         AND last_traded_price IS NOT NULL""",
                    (market['market_id'],sid),
                ).fetchone()
                vals[role]=(sid,by_role[role]['runner_name'],
                            _last_preplay_ltp(con,market['market_id'],sid,first_inplay),
                            mm[0],mm[1])
            winner_role=None
            if market['winner_selection_id'] is not None:
                for role,r in by_role.items():
                    if r['selection_id']==market['winner_selection_id']:
                        winner_role=role
            price_rows=con.execute(
                "SELECT COUNT(*) FROM price_history WHERE market_id=?",
                (market['market_id'],),
            ).fetchone()[0]
            con.execute("""INSERT OR REPLACE INTO market_summary(
                market_id,market_time,event_name,
                home_selection_id,home_name,away_selection_id,away_name,
                draw_selection_id,draw_name,winner_role,first_inplay_time,
                home_preplay_ltp,away_preplay_ltp,draw_preplay_ltp,
                home_min_ltp,home_max_ltp,away_min_ltp,away_max_ltp,
                draw_min_ltp,draw_max_ltp,price_rows,derived_at)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,CURRENT_TIMESTAMP)""",
                (market['market_id'],market['market_time'],market['event_name'],
                 vals['home'][0],vals['home'][1],vals['away'][0],vals['away'][1],
                 vals['draw'][0],vals['draw'][1],winner_role,first_inplay,
                 vals['home'][2],vals['away'][2],vals['draw'][2],
                 vals['home'][3],vals['home'][4],vals['away'][3],vals['away'][4],
                 vals['draw'][3],vals['draw'][4],price_rows))
            count+=1
        con.commit()
    return {'status':'completed','summaries_built':count}
