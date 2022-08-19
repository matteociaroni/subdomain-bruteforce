import os
import unittest
from subdomain_bruteforce import Model, Controller


class Tests(unittest.TestCase):

    def test_domain_resolving(self):
        self.assertTrue(Model.domain_exists("google.com"))
        self.assertFalse(Model.domain_exists("cerywibfuyviuedyivuyv.com"))
        self.assertTrue(Model.domain_exists("apple.com"))
        self.assertFalse(Model.domain_exists("pibowcq.com"))

    def test_bruteforce(self):
        bruteforcer = Model("google.com", None, ["cieufhcne", "maps", "oicunf", "drive"])
        bruteforcer.bruteforce_thread.join()
        self.assertEqual({"maps.google.com", "drive.google.com"}, set(bruteforcer.found_subdomains))

    def test_generate_word(self):
        self.assertEqual(sum(1 for _ in Controller.generate_word(3)), 17576)
        self.assertEqual(sum(1 for _ in Controller.generate_word(4)), 456976)
        self.assertEqual(sum(1 for _ in Controller.generate_word(3, "a")), 17576)
        self.assertEqual(sum(1 for _ in Controller.generate_word(3, "b")), 16900)

        generator1 = Controller.generate_word(3)
        self.assertEqual(next(generator1), "aaa")
        self.assertEqual(next(generator1), "aab")
        self.assertEqual(next(generator1), "aac")

        generator2 = Controller.generate_word(3, "fjl")
        self.assertEqual(next(generator2), "fjl")
        self.assertEqual(next(generator2), "fjm")
        self.assertEqual(next(generator2), "fjn")

    def test_word_from_file(self):
        file_name = "testfile.txt"
        file_content = "Lorem ipsum dolor sit amet"
        with open(file_name, "w") as f:
            f.write(file_content.replace(" ", "\n"))

        words = Controller.get_words_from_file(file_name)
        self.assertEqual(file_content.split(" "), list(words))

        os.remove(file_name)

    def test_word_from_file_start_from(self):
        file_name = "testfile.txt"
        file_content = "Lorem ipsum dolor sit amet"
        with open(file_name, "w") as f:
            f.write(file_content.replace(" ", "\n"))

        words = Controller.get_words_from_file(file_name, "dolor")
        self.assertEqual("dolor sit amet".split(" "), list(words))

        os.remove(file_name)

    def test_controller_and_bruteforcer(self):
        controller = Controller("google.com", None, words=["cieufhcne", "maps", "oicunf", "drive"])
        controller.model.bruteforce_thread.join()
        self.assertEqual({"maps.google.com", "drive.google.com"}, set(controller.model.found_subdomains))


if __name__ == '__main__':
    unittest.main()
