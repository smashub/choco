"""
Interfaces and basic primitives for validating indentifiers and attempting
correction / autocompletion when possible.
"""
import re
import logging

from urllib.request import urlopen
from urllib.error import URLError, HTTPError

logger = logging.getLogger("choco.autolink")


class InvalidIdentifierError(Exception):
    """Raised if a given URL or identifier is not valid or cannot be resolved."""
    pass


def make_request(url: str, timeout: int = 10):
    """Perform an HTTP request at the given URL and record the outcome."""
    try:  # performing a timed-out GET request from the URL
        with urlopen(url, timeout=timeout) as response:
            code =  response.status
    except HTTPError as error:  # error at the protocol level
        logger.warn(f"HTTPError {error.status} : {error.reason}")
        code = 0
    except URLError as error:  # error at the URL level
        logger.warn(f"URLError {error.reason}")
        code = 0
    except TimeoutError:  # not necessarily a URL problem
        logger.warn("Request timed-out: server may be offline")
        code = 0

    return code == 200


class IdentifierSolver(object):

    def check_valid_url(self, url: str):
        """Check whether a given URL is valid for the specific portal."""
        pass

    def attempt_resolution(self, url: str, hook_name: str = None):
        """Attempt resolving a URL that is potentially wrong or incomplete."""
        pass

    def register_hook(self, hook_name:str, hook_template: str):
        """Register a new hook to extend the resolution process."""
        pass


class SimpleIdentifierSolver(IdentifierSolver):
    
    def __init__(self, hook_map: dict = None):
        """Basic constructor with optional initialisation of hooks."""
        self.hook_map = {}
        if hook_map is not None:  # populate hooks
            for hook_name, hook_template in hook_map.items():
                self.register_hook(hook_name, hook_template)

    def _template_to_regexpr(self, hook_template: str):
        """Convert a URL template into a regular expression."""
        hook_re = hook_template.replace("/", "\/")
        hook_re = hook_re.replace(".", "\.")
        hook_re = hook_re.replace("{}", ".+")
        return hook_re

    def check_valid_url(self, url: str):
        """
        Perform a validation of a given URL into 2 steps: consistency with the
        registered hooks (if the URL matches at least one of the templates) and
        GET request using the same URL to check the status of the response.
        """
        # Basic pre-processing on the URL, filling the prefix if needed
        if not url.startswith("https://"):
            url = "https://" + url

        valid = False
        if self.hook_map is not None:  # internal check on the templates
            for hook_name, hook_template in self.hook_map.items():
                hook_re = self._template_to_regexpr(hook_template)
                if re.fullmatch(hook_re, url):  # GET if URL matches pattern
                    logger.info(f"Checking potentially valid URL: {url}")
                    valid = make_request(url)

        return valid

    def attempt_resolution(self, url: str, hook_name: str = None):
        """
        Attempt a resolution of a given URL, in case it cannot be already
        validated as it is. This is done via template filling, using all the
        possible hooks that have been registered. If a specific hook needs to
        be used, its name can be given as an additional (optional) parameter.
        """
        if self.check_valid_url(url):
            return url  # URL is already good to go

        if hook_name is not None and hook_name not in self.hook_map:
            raise ValueError(f"Hook {hook_name} has not been registered yet.")
        candidates = {hook_name: self.hook_map[hook_name]} \
            if hook_name else self.hook_map

        for hook, hook_template in candidates.items():  # attempt simple infill
            tentative_url = hook_template.format(url)
            logger.info(f"Attempting {hook} resolution: {tentative_url}")
            if make_request(tentative_url):
                logger.info(f"Succesfully resolved: {tentative_url}")
                return tentative_url

        raise InvalidIdentifierError(f"{url} cannot be resolved.")

    def register_hook(self, hook_name: str, hook_template: str):
        """
        Register a new hook after running some basic sanity checks. The hook's
        template is expected as a string with a single formatting placeholder.
        """
        if hook_name in self.hook_map:
            logger.warn(f"Hook {hook_name} already registered. Overriding.")

        if len(re.findall(r"\{\}", hook_template)) != 1:
            raise ValueError("Hook's template needs to have a placeholder.")

        self.hook_map[hook_name] = hook_template


# Some built-in service-specific identifier solvers

SOLVER_BUNDLE = {
    "musicbrainz": SimpleIdentifierSolver({
        "work": "https://musicbrainz.org/work/{}",
        "artist": "https://musicbrainz.org/artist/{}",
        "release": "https://musicbrainz.org/release/{}",
        "recording": "https://musicbrainz.org/recording/{}",})
}