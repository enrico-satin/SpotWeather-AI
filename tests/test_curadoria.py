import unittest

from ClimaMusical import curate_track_candidates


def make_tracks(prefix: str, artists: int, tracks_per_artist: int) -> list[dict]:
    return [
        {
            "id": f"{prefix}-{artist}-{number}",
            "uri": f"spotify:track:{prefix}-{artist}-{number}",
            "artists": [{"id": f"{prefix}-artist-{artist}", "name": f"Artist {artist}"}],
        }
        for artist in range(artists)
        for number in range(tracks_per_artist)
    ]


class CurateTrackCandidatesTests(unittest.TestCase):
    def test_respects_requested_ratio_when_pools_are_large_enough(self):
        known = make_tracks("known", artists=10, tracks_per_artist=10)
        discovery = make_tracks("new", artists=10, tracks_per_artist=10)

        selected = curate_track_candidates(
            known, discovery, total_tracks=50, known_ratio=0.7, max_per_artist=5
        )

        self.assertEqual(len(selected), 50)
        known_ids = {track["id"] for track in known}
        discovery_ids = {track["id"] for track in discovery}
        self.assertEqual(sum(track["id"] in known_ids for track in selected), 35)
        self.assertEqual(sum(track["id"] in discovery_ids for track in selected), 15)

    def test_does_not_repeat_tracks_or_exceed_artist_limit(self):
        known = make_tracks("known", artists=2, tracks_per_artist=10)
        discovery = make_tracks("new", artists=2, tracks_per_artist=10)
        selected = curate_track_candidates(
            known, discovery, total_tracks=50, known_ratio=0.7, max_per_artist=3
        )

        ids = [track["id"] for track in selected]
        self.assertEqual(len(ids), len(set(ids)))
        counts = {}
        for track in selected:
            artist_id = track["artists"][0]["id"]
            counts[artist_id] = counts.get(artist_id, 0) + 1
        self.assertTrue(all(count <= 3 for count in counts.values()))

    def test_handles_empty_pools(self):
        self.assertEqual(curate_track_candidates([], [], total_tracks=10), [])

    def test_returns_fewer_tracks_when_candidates_are_insufficient(self):
        known = make_tracks("known", artists=1, tracks_per_artist=2)
        selected = curate_track_candidates(
            known, [], total_tracks=10, known_ratio=0.7, max_per_artist=5
        )
        self.assertEqual(len(selected), 2)


if __name__ == "__main__":
    unittest.main()
