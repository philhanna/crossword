import configparser
import os


class Configuration:
    """ Singleton class that handles configuration data """

    _instance = None

    ############################################################
    #  Instance methods
    ############################################################

    def __init__(self, config_filename="~/.crossword_config.ini"):
        """ Constructor """
        filename = os.path.expanduser(config_filename)
        config = configparser.ConfigParser()
        with open(filename) as fp:
            config.read_file(fp)
        self._config = config

    def get(self, section, key):
        return self._config.get(section, key)

    ############################################################
    #  Class methods
    ############################################################

    @staticmethod
    def get_instance():
        """ Returns the singleton instance of this class """
        if not Configuration._instance:
            Configuration._instance = Configuration()
        return Configuration._instance

    @staticmethod
    def get_grids_root():
        """ Returns the grids root """
        config = Configuration.get_instance()
        return config.get('data', 'grids_root')

    @staticmethod
    def get_puzzles_root():
        """ Returns the puzzles root """
        config = Configuration.get_instance()
        return config.get('data', 'puzzles_root')

    @staticmethod
    def get_wordlists_root():
        """ Returns the wordlists root """
        config = Configuration.get_instance()
        return config.get('data', 'wordlists_root')

    @staticmethod
    def get_words_filename():
        """ Returns the path to the words file """
        config = Configuration.get_instance()
        return config.get('data', 'words_filename')

    @staticmethod
    def get_author_name():
        """ Returns the author name """
        config = Configuration.get_instance()
        return config.get('author', 'name')

    @staticmethod
    def get_author_address():
        """ Returns the author address """
        config = Configuration.get_instance()
        return config.get('author', 'address')

    @staticmethod
    def get_author_city_state_zip():
        """ Returns the author city_state_zip """
        config = Configuration.get_instance()
        return config.get('author', 'city_state_zip')

    @staticmethod
    def get_author_email():
        """ Returns the author email """
        config = Configuration.get_instance()
        return config.get('author', 'email')
