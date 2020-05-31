import configparser
import os


class Configuration:
    """ Handles configuration data """
    def __init__(self, config_filename="~/.crossword_config.ini"):
        """ Constructor """
        filename = os.path.expanduser(config_filename)
        config = configparser.ConfigParser()
        with open(filename) as fp:
            config.read_file(fp)
        self.config = config

    def get_grids_root(self):
        """ Returns the grids root """
        return self.config.get('data', 'grids_root')

    def get_puzzles_root(self):
        """ Returns the puzzles root """
        return self.config.get('data', 'puzzles_root')

    def get_author_name(self):
        """ Returns the author name """
        return self.config.get('author', 'name')

    def get_author_address(self):
        """ Returns the author address """
        return self.config.get('author', 'address')

    def get_author_city_state_zip(self):
        """ Returns the author city_state_zip """
        return self.config.get('author', 'city_state_zip')

    def get_author_email(self):
        """ Returns the author email """
        return self.config.get('author', 'email')

