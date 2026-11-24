"""Rivalry names for game cards (owner, #211): our own list, since CFBD has none (its game
notes name bowls, playoff rounds, title games and a few classics, which win over this list).

One entry per pair of teams (either can be home), by site slug, with the name fans use. Only
names that are certain (owner): fan nicknames and names with no settled form are left out.
Edit freely: a pair that isn't listed simply shows no name. Checked against the teams table
when added (every slug exists); `tests/test_rivalries.py` keeps the list well formed.
"""

RIVALRIES: list[tuple[str, str, str]] = [
    ("alabama", "auburn", "Iron Bowl"),
    ("ohio-state", "michigan", "The Game"),
    ("texas", "oklahoma", "Red River Rivalry"),
    ("ole-miss", "mississippi-state", "Egg Bowl"),
    ("army", "navy", "Army–Navy Game"),
    ("washington", "washington-state", "Apple Cup"),
    ("california", "stanford", "Big Game"),
    ("clemson", "south-carolina", "Palmetto Bowl"),
    ("florida", "florida-state", "Sunshine Showdown"),
    ("georgia", "georgia-tech", "Clean, Old-Fashioned Hate"),
    ("kentucky", "louisville", "Governor's Cup"),
    ("alabama", "tennessee", "Third Saturday in October"),
    ("texas", "texas-am", "Lone Star Showdown"),
    ("oklahoma", "oklahoma-state", "Bedlam"),
    ("kansas", "kansas-state", "Sunflower Showdown"),
    ("indiana", "purdue", "Old Oaken Bucket"),
    ("illinois", "northwestern", "Land of Lincoln Trophy"),
    ("auburn", "georgia", "Deep South's Oldest Rivalry"),
    ("arkansas", "lsu", "Battle for the Golden Boot"),
    ("arizona", "arizona-state", "Territorial Cup"),
    ("colorado", "colorado-state", "Rocky Mountain Showdown"),
    ("iowa", "nebraska", "Heroes Game"),
    ("virginia", "virginia-tech", "Commonwealth Clash"),
    ("duke", "north-carolina", "Victory Bell"),
    ("north-carolina", "virginia", "South's Oldest Rivalry"),
    ("pittsburgh", "west-virginia", "Backyard Brawl"),
    ("iowa", "wisconsin", "Heartland Trophy"),
    ("iowa", "minnesota", "Floyd of Rosedale"),
    ("michigan", "minnesota", "Little Brown Jug"),
    ("minnesota", "wisconsin", "Paul Bunyan's Axe"),
    ("michigan", "michigan-state", "Paul Bunyan Trophy"),
    ("michigan-state", "penn-state", "Land Grant Trophy"),
    ("iowa", "iowa-state", "Cy-Hawk Trophy"),
    ("smu", "tcu", "Battle for the Iron Skillet"),
    ("houston", "rice", "Bayou Bucket"),
    ("southern-miss", "tulane", "Battle for the Bell"),
    ("fresno-state", "san-diego-state", "Old Oil Can"),
    ("boise-state", "fresno-state", "Milk Can"),
    ("nevada", "unlv", "Battle for Nevada"),
    ("new-mexico", "new-mexico-state", "Rio Grande Rivalry"),
    ("miami-oh", "ohio", "Battle of the Bricks"),
    ("bowling-green", "toledo", "Battle of I-75"),
    ("cincinnati", "miami-oh", "Victory Bell"),
    ("arkansas", "texas-am", "Southwest Classic"),
    ("arkansas", "missouri", "Battle Line Rivalry"),
    ("grambling", "southern", "Bayou Classic"),
    ("montana", "montana-state", "Brawl of the Wild"),
    ("harvard", "yale", "The Game"),
    ("lafayette", "lehigh", "The Rivalry"),
    ("north-dakota-state", "south-dakota-state", "Dakota Marker"),
    ("bethune-cookman", "florida-am", "Florida Classic"),
    ("alcorn-state", "jackson-state", "Soul Bowl"),
    ("alabama-am", "alabama-state", "Magic City Classic"),
    ("alabama-state", "tuskegee", "Turkey Day Classic"),
    ("north-carolina-at", "north-carolina-central", "Aggie–Eagle Classic"),
    ("richmond", "william-mary", "Capital Cup"),
    ("delaware", "villanova", "Battle of the Blue"),
    ("sam-houston", "stephen-f-austin", "Battle of the Piney Woods"),
    ("prairie-view-am", "texas-southern", "Labor Day Classic"),
    ("grambling", "prairie-view-am", "State Fair Classic"),
]

_BY_PAIR = {frozenset((a, b)): name for a, b, name in RIVALRIES}


def rivalry_name(slug_a: str, slug_b: str) -> str | None:
    """The rivalry's name for two teams (either order), or None."""
    return _BY_PAIR.get(frozenset((slug_a, slug_b)))
