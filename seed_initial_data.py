"""
ASMA Accordi Next Generation - Initial Database Seeder
Populates the archive with realistic, high-quality songs, setlists, and repertoires.
"""

from asma_core.models import Song, Repertoire, Setlist, SetlistItem, LiveEvent
from asma_core.storage_manager import StorageManager


def seed():
    storage = StorageManager()

    # 1. Ensure Repertoires
    reps = storage.list_repertoires()
    wip_rep = next(r for r in reps if "Working In Progress" in r.name)
    def_rep = next(r for r in reps if "Definitivo" in r.name)
    acu_rep = next(r for r in reps if "Acustico" in r.name)

    # 2. Songs
    songs_data = [
        {
            "title": "Hotel California",
            "artist": "Eagles",
            "author": "Don Henley, Glenn Frey, Don Felder",
            "genre": "Classic Rock",
            "key": "Bm",
            "bpm": 74,
            "time": "4/4",
            "tags": ["live", "chitarra-12-corde", "assolo-finale"],
            "notes": "Doppio assolo incrociato Don Felder e Joe Walsh.",
            "rep": def_rep,
            "aml": """{title: Hotel California}
{artist: Eagles}
{key: Bm}
{tempo: 74}
{time: 4/4}

{intro}
| Bm | F#7 | A | E | G | D | Em | F#7 |

{verse}
[Bm]On a dark desert highway, [F#7]cool wind in my hair
[A]Warm smell of colitas, [E]rising up through the air
[G]Up ahead in the distance, [D]I saw a shimmering light
[Em]My head grew heavy and my sight grew dim, [F#7]I had to stop for the night

{chorus}
[G]Welcome to the Hotel Cali[D]fornia
Such a [Em]lovely place, such a [F#7]lovely face
[G]Plenty of room at the Hotel Cali[D]fornia
Any [Em]time of year, you can [F#7]find it here

{solo}
| Bm | F#7 | A | E | G | D | Em | F#7 |
{guitar: Assolo finale chitarra 1 (Felder) poi chitarra 2 (Walsh)}
"""
        },
        {
            "title": "Canzone per un'amica",
            "artist": "Nomadi",
            "author": "Francesco Guccini",
            "genre": "Cantautore",
            "key": "SOL",
            "bpm": 92,
            "time": "4/4",
            "tags": ["live", "italiano", "acustico"],
            "notes": "Ingresso chitarra acustica e flauto.",
            "rep": def_rep,
            "aml": """{title: Canzone per un'amica}
{artist: Nomadi}
{key: SOL}
{tempo: 92}
{time: 4/4}

{intro}
| SOL | RE | DO | SOL |

{verse}
[SOL]Lunga e diritta [RE]correva la strada,
l'auto [DO]veloce cor[SOL]reva
La dolce estate era [MIm]già cominciata,
[DO]vicino a lui sorri[RE]deva

{chorus}
[SOL]Non correre, [DO]diceva [SOL]bella,
che c'è [RE]tempo per arrivare
[SOL]Non correre, [DO]diceva [SOL]bella,
che c'è [RE]tempo per arri[SOL]vare
"""
        },
        {
            "title": "Sultans of Swing",
            "artist": "Dire Straits",
            "author": "Mark Knopfler",
            "genre": "Rock",
            "key": "Dm",
            "bpm": 148,
            "time": "4/4",
            "tags": ["rock", "chitarra", "fingerpicking"],
            "notes": "Suonare in fingerpicking stile Mark Knopfler.",
            "rep": def_rep,
            "aml": """{title: Sultans of Swing}
{artist: Dire Straits}
{key: Dm}
{tempo: 148}
{time: 4/4}

{intro}
| Dm | C Bb | A | A |
| Dm | C Bb | A | A |

{verse}
You get a [Dm]shiver in the dark, it's raining [C]in the [Bb]park but mean[A]time
[Dm]South of the river you stop and you [C]hold every[Bb]thing [A]
[F]A band is blowing Dixie double [C]four time
[Bb]You feel alright when you hear the music [Dm]ring [Bb] [C]

{chorus}
And then you [Dm]step inside, but you don't [C]see too many [Bb]faces [A]
Coming in [Dm]out of the rain to hear the [C]jazz go [Bb]down [A]
"""
        },
        {
            "title": "Il Mio Canto Libero",
            "artist": "Lucio Battisti",
            "author": "Mogol, Lucio Battisti",
            "genre": "Pop / Cantautore",
            "key": "LA",
            "bpm": 78,
            "time": "4/4",
            "tags": ["acustico", "classico", "coro"],
            "notes": "Crescendo continuo fino al finale corale a squarciagola.",
            "rep": acu_rep,
            "aml": """{title: Il Mio Canto Libero}
{artist: Lucio Battisti}
{key: LA}
{tempo: 78}
{time: 4/4}

{verse}
In un [LA]mondo che
non ci [FA#m]vuole più
il mio [RE]canto libero [MI]sei tu

{chorus}
Nasce il [LA]sole e l'ar[FA#m]cobaleno
sopra un [RE]cielo limpido e se[MI]reno
"""
        },
        {
            "title": "Knockin' On Heaven's Door",
            "artist": "Bob Dylan",
            "author": "Bob Dylan",
            "genre": "Folk Rock",
            "key": "G",
            "bpm": 110,
            "time": "4/4",
            "tags": ["medley-ready", "jam"],
            "notes": "Ideale per assoli e jam finale di concerto.",
            "rep": wip_rep,
            "aml": """{title: Knockin' On Heaven's Door}
{artist: Bob Dylan}
{key: G}
{tempo: 110}
{time: 4/4}

{intro}
| G | D | Am | Am |
| G | D | C | C |

{verse}
[G]Mama, take this [D]badge off of [Am]me
[G]I can't [D]use it any[C]more
[G]It's gettin' [D]dark, too dark for me to [Am]see
[G]I feel I'm [D]knockin' on heaven's [C]door

{chorus}
[G]Knock, knock, [D]knockin' on heaven's [Am]door
[G]Knock, knock, [D]knockin' on heaven's [C]door
"""
        }
    ]

    saved_songs = []
    for s_info in songs_data:
        s = Song(
            title=s_info["title"],
            artist=s_info["artist"],
            author=s_info["author"],
            genre=s_info["genre"],
            key_original=s_info["key"],
            key_current=s_info["key"],
            bpm=s_info["bpm"],
            time_signature=s_info["time"],
            tags=s_info["tags"],
            shared_notes=s_info["notes"],
            aml_content=s_info["aml"]
        )
        saved = storage.save_song(s, "admin@band.org", "Amministratore", "Inizializzazione catalogo")
        storage.move_song_to_repertoire(saved.uuid, s_info["rep"].uuid, "admin@band.org", "Amministratore")
        saved_songs.append(saved)
        print(f"[OK] Inserito: {saved.title} ({saved.artist}) -> {s_info['rep'].name}")

    # 3. Create Default Live Setlist
    setlist = Setlist(
        title="Concerto Live Tour Estate 2027",
        date="20/07/2027",
        description="Scaletta ufficiale per il festival estivo principale.",
        items=[
            SetlistItem(song_uuid=saved_songs[0].uuid, notes="Apertura potente"),
            SetlistItem(song_uuid=saved_songs[1].uuid, notes="Stacco acustico"),
            SetlistItem(song_uuid=saved_songs[2].uuid, notes="Assolo chitarra"),
            SetlistItem(song_uuid=saved_songs[3].uuid, is_medley=True, notes="Medley canto libero"),
            SetlistItem(song_uuid=saved_songs[4].uuid, is_medley=True, notes="Chiusura con jam e saluti")
        ]
    )
    storage.save_setlist(setlist, "admin@band.org", "Amministratore")
    print(f"[OK] Creata Scaletta: {setlist.title} ({len(setlist.items)} brani)")

    # 4. Create Default Live Event
    event = LiveEvent(
        name="Summer Rock Festival 2027",
        venue="Piazza del Popolo, Roma",
        event_date="20/07/2027",
        setlist_uuid=setlist.uuid,
        logistics_notes="Arrivo furgone ore 15:00. Soundcheck ore 17:00. Inizio concerto ore 21:30. Forniti 4 monitor spia e D.I. box."
    )
    storage.save_event(event, "admin@band.org", "Amministratore")
    print(f"[OK] Creato Evento Live: {event.name} ({event.event_date})")

    print("\n[OK] Inizializzazione completata con successo!")


if __name__ == "__main__":
    seed()
