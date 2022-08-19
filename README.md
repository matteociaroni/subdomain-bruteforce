# Subdomain Bruteforce
Python command-line application to bruteforce subdomains.

This Python module is useful to check the existence of subdomains of a base domain.
It bruteforces all possible subdomains based on a dictionary file or generating words by letters combinations.

## Installation and execution

- Download the _subdomain-bruteforce.py_ file 
- Run the script with:
  - `python subdomain-bruteforce.py domain --file FILE` to load subdomains from a file
  - `python subdomain-bruteforce.py domain --generator NUMBER_OF_LETTERS` to generate subdomains by combinations of letters

### Arguments
#### Word source
These arguments are mutually exclusive, one is required.
They provide a source of words to bruteforce the domain. 
- `--file` set the file as word source
- `--generator` generate all combination of letters

#### Options
These arguments are optional.
- `--from` start bruteforce from this word, skipping all the previous words
- `--output` the output file to save found subdomains
- `--thread-limit` the maximum number of parallel threads to run
