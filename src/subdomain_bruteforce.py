import argparse
import datetime
import itertools
import socket
import string
import threading
import time
from typing import Iterable, Optional, List, Set


class Model(object):
    """This class contains the business logic of the program.

    Objects of this class can bruteforce subdomains of the base domain"""

    def __init__(self, domain: str, view, words: Iterable[str], thread_limit: int = 100):

        # set all variables to default values
        self.base_domain, self.view, self.words, self.thread_limit = domain, view, words, thread_limit
        self.found_subdomains: Set[str] = set()                 # the result set containing all found subdomains
        self.checked_subdomains_count: int = 0                  # the number of currently checked seubdomains
        self.latest: Optional[str] = None                       # the latest checked subdomain
        self.subdomain_threads: Set[threading.Thread] = set()   # currently running threads for bruteforce
        self.dns_working, self.dns_not_working = threading.Event(), threading.Event()
        self.complete_bruteforcing = threading.Event()          # event to stop all threads at the end of the script
        self.dns_not_working.set()

        Model.start_daemon_thread(self.dns_checker)  # thread to control if the DNS server resolves the base domain
        self.bruteforce_thread = Model.start_daemon_thread(self.bruteforce)  # thread to make all the subdomain requests
        self.start_time = datetime.datetime.now()

    @staticmethod
    def start_daemon_thread(target: callable, args: tuple = ()) -> threading.Thread:
        """Create and start a new daemon thread"""

        thread = threading.Thread(target=target, args=args)
        thread.daemon = True
        thread.start()
        return thread

    @staticmethod
    def domain_exists(domain: str) -> bool:
        """Check the existence of a domain trying DNS resolution"""

        try:
            socket.gethostbyname(domain)
            return True
        except socket.gaierror:  # an exception is thrown if the domain is not resolved
            return False

    def check_domain(self, domain: str) -> None:
        """If the domain exists add in the found_subdomain set and trigger the view's method"""

        if Model.domain_exists(domain):
            self.found_subdomains.add(domain)
            if self.view:
                self.view.found_subdomain(domain)

    def thread_limiter(self) -> None:
        """If the current number of subdomains threads exceeds the limit joins all subdomain threads

        This function is used to avoid memory leaks making the program wait until all the threads are closed.
        """

        while len(self.subdomain_threads) > self.thread_limit:
            thread = self.subdomain_threads.pop()
            thread.join()

    def dns_checker(self) -> None:
        """Check if DNS resolve the base domain.

        This function is used to check if DNS server is still responding.
        Some DNS servers ban users who make a large number of requests per second.
        """

        while not self.complete_bruteforcing.is_set():
            if Model.domain_exists(self.base_domain):
                self.dns_working.set()
                self.dns_not_working.clear()
            else:
                self.dns_working.clear()
                self.dns_not_working.set()

        time.sleep(0.1)

    def bruteforce(self) -> None:
        """Creates a thread to check every subdomain"""

        for word in self.words:

            # pause if base domain is not resolving
            self.dns_working.wait()

            subdomain = f"{word}.{self.base_domain}".strip(" \n")

            # create and start a thread to check if subdomain exists
            self.subdomain_threads.add(Model.start_daemon_thread(target=self.check_domain, args=(subdomain,)))
            self.thread_limiter()

            self.latest = subdomain
            self.checked_subdomains_count += 1

        # when all subdomains are checked, wait for all threads to close
        for thread in self.subdomain_threads:
            thread.join()

        self.complete_bruteforcing.set()
        if self.view:
            self.view.completed(self.found_subdomains)


class Controller(object):
    """This class controls the model and contains some useful methods to get iterables of strings"""

    def __init__(self, domain: str, view, words: Iterable[str], thread_limit=100):
        """Checks the arguments and executes the model"""

        if domain is None:
            raise TypeError("Base domain is not set")

        # create a Model object which will start bruteforce in a new thread
        self.model = Model(domain, view, words, thread_limit=thread_limit)

        self.view: ConsoleView = view
        if self.view:

            # start view's threads to check model's update
            event_listener_threads = [
                (self.model.dns_working, lambda: self.view.dns_working()),
                (self.model.dns_not_working, lambda: self.view.dns_not_working()),
            ]
            for args in event_listener_threads:
                Model.start_daemon_thread(target=self.event_listener, args=args)

            # print start message
            self.view.start()

            # wait for user input and then print the current status
            while not self.model.complete_bruteforcing.is_set():
                try:
                    input()
                    self.view.print_status(self.current_status())
                except KeyboardInterrupt:  # raised when the user forces program interruption
                    self.view.print_status(self.current_status())
                    exit(1)

    def current_status(self) -> dict:
        """Returns a dictionary with some useful data from the Model object"""

        return {
            "time": str(datetime.datetime.now() - self.model.start_time),   # execution time
            "latest subdomain": self.model.latest,                          # latest checked subdomain
            "count": self.model.checked_subdomains_count,                   # number of checked subdomains
            "subdomains/second": round(self.model.checked_subdomains_count / (datetime.datetime.now() - self.model.start_time).total_seconds()),
            "subdomain threads": len(self.model.subdomain_threads)          # currently running threads for bruteforce
        }

    def event_listener(self, event: threading.Event, action: callable) -> None:
        """Waits for the event and then executes the action.

        This function is always used as a thread"""

        completed = self.model.complete_bruteforcing  # the completed event
        while not completed.is_set():  # repeat until the bruteforce is complete

            while event.is_set():  # if event is already set, wait for clear
                time.sleep(0.1)

            event.wait(1)
            if event.is_set():
                action()

    @staticmethod
    def get_words_from_file(file_name: str, start_from: str = None) -> str:
        """Reads the file and return all words as a generator"""

        with open(file_name, "r") as f:
            found = False

            for line in f:
                word = line.strip(" \n")

                if word == start_from:  # found the start_from words
                    found = True

                if start_from is None or found:  # yield word if start_from is not set or if it's already found
                    yield word

    @staticmethod
    def generate_word(letter_count: int, start_from: str = "", alphabet: str = string.ascii_lowercase):
        """Generates all words with the provided number of letters"""

        letters: List[List[str]] = []  # a list of lists of chars

        for i in range(letter_count):
            try:
                first = start_from[i]  # the first letter
                all_chars = alphabet[alphabet.index(first):]  # all chars after the first (included)
                letters.append(list(all_chars))
            except IndexError:
                letters.append(list(alphabet))

        return ("".join(comb) for comb in itertools.product(*letters))


class ConsoleView(object):
    """This class controls the interaction with the user using the CLI"""

    def __init__(self, result_file: str = None):
        self.result_file: str = result_file

    @staticmethod
    def start() -> None:
        print("Started. Press ENTER to check current status...")

    def found_subdomain(self, subdomain: str) -> None:
        print(f"{datetime.datetime.now()} FOUND {subdomain}")
        if self.result_file is not None:
            with open(self.result_file, "a") as f:
                f.write(subdomain + "\n")

    @staticmethod
    def dns_not_working() -> None:
        print(f"{datetime.datetime.now()} PAUSED: base domain not resolving. Your DNS server may have banned your IP.")

    @staticmethod
    def dns_working() -> None:
        print(f"{datetime.datetime.now()} RESUMED")

    def completed(self, subdomains: Set[str]) -> None:
        print(f"{datetime.datetime.now()} COMPLETED {subdomains}")
        if self.result_file is not None:
            with open(self.result_file, "w") as f:
                f.write(str(subdomains))

    @staticmethod
    def print_status(status: dict) -> None:
        print(status)


def parse_arguments() -> dict:
    """Parse arguments passed by CLI.

    Return a dictionary containing the value of all arguments"""

    parser = argparse.ArgumentParser(description="A program to bruteforce subdomains")
    parser.add_argument("domain", help="The domain to bruteforce", type=str, nargs=1)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--file", "-f", help="Bruteforce subdomains from file", type=str)
    group.add_argument("--generator", "-g", help="Bruteforce subdomains generating all combination of letters", type=int)
    parser.add_argument("--from", help="Skip all previous strings", type=str)
    parser.add_argument("--output", "-o", help="Output file for found subdomains", type=str)
    parser.add_argument("--thread-limit", "-t", help="Maximum number of threads", type=int, default=100)
    return vars(parser.parse_args())


def main():
    args = parse_arguments()
    domain = args["domain"][0]
    start_from = args["from"] if args["from"] else None
    view = ConsoleView(args["output"] if args["output"] else None)

    if args["file"]:
        words = Controller.get_words_from_file(args["file"], start_from)
    elif args["generator"]:
        words = Controller.generate_word(args["generator"], start_from)
    else:
        raise ValueError("No word source provided")

    controller = Controller(domain, view, words, args["thread_limit"])


if __name__ == "__main__":
    main()
