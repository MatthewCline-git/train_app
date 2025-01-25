from difflib import get_close_matches
import re
from mta_api.utils.logger import get_logger
from mta_api.data.subway_lines import LINE_TO_STOPS

logger = get_logger(__name__)


class SubwayStationMatcher:
    def __init__(self, station_names):
        """
        Initialize the matcher with a list of official station names.
        """
        logger.info(
            f"Initializing SubwayStationMatcher with {len(station_names)} stations"
        )
        self.official_names = station_names
        self.normalized_names = {
            self._normalize_name(name): name for name in station_names
        }
        logger.debug(f"Created {len(self.normalized_names)} normalized station names")

    def _normalize_name(self, name):
        """
        Normalize station names for better matching
        """
        try:
            name = name.lower()
            substitutions = {
                "st": "street",
                "sq": "square",
                "pk": "park",
                "pkwy": "parkway",
                "rd": "road",
                "av": "avenue",
                "plaza": "plz",
                "junction": "jct",
                "heights": "hts",
            }

            words = name.split()
            normalized_words = []

            for word in words:
                word = substitutions.get(word, word)
                word = re.sub(r"[^\w\s]", "", word)
                normalized_words.append(word)

            result = " ".join(normalized_words)
            logger.debug(f"Normalized '{name}' to '{result}'")
            return result
        except Exception as e:
            logger.error(f"Error normalizing station name '{name}': {str(e)}")
            return name

    def find_matches(self, query, n=3, cutoff=0.0):
        """
        Find the best matching station names for a given query.
        """
        logger.info(f"Finding matches for query: '{query}'")
        try:
            normalized_query = self._normalize_name(query)
            matches = get_close_matches(
                normalized_query, list(self.normalized_names.keys()), n=n, cutoff=cutoff
            )

            results = []
            for match in matches:
                official_name = self.normalized_names[match]
                score = self._calculate_similarity(normalized_query, match)
                results.append((official_name, score))

            results = sorted(results, key=lambda x: x[1], reverse=True)

            if results:
                logger.info(f"Found {len(results)} matches for '{query}'")
                logger.debug(
                    f"Best match: '{results[0][0]}' with score {results[0][1]:.2f}"
                )
            else:
                logger.warning(f"No matches found for query '{query}'")

            return results

        except Exception as e:
            logger.error(f"Error finding matches for query '{query}': {str(e)}")
            return []

    def _calculate_similarity(self, query, match):
        """Calculate similarity score between query and match."""
        try:
            if query in match:
                return 1.0

            shorter = min(query, match, key=len)
            longer = max(query, match, key=len)

            if len(longer) == 0:
                return 0.0

            matches = sum(a == b for a, b in zip(shorter, longer))
            return matches / len(longer)
        except Exception as e:
            logger.error(
                f"Error calculating similarity between '{query}' and '{match}': {str(e)}"
            )
            return 0.0


if __name__ == "__main__":
    logger.info("Starting station matcher test")
    stations = [
        "Times Sq-42 St",
        "28 St",
        "Penn Station",
        "Grand Central-42 St",
        "Union Sq-14 St",
        "Herald Sq-34 St",
        "Atlantic Ave-Barclays Ctr",
    ]

    matcher = SubwayStationMatcher(stations)
    query = input("Enter station to search: ")
    logger.info(f"Testing with query: {query}")

    matches = matcher.find_matches(query)
    for station, score in matches:
        print(f"Match: {station} (score: {score:.2f})")
