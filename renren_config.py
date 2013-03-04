#!/usr/bin/env python2
# vim:fileencoding=utf-8

"""Config Module for RenrenCLI
"""

__all__ = ['Config']


import json
import logging
import os


class Config:

    DEFAULT_FILENAME = '.renren.config'

    def __init__(self, filename=None):
        """Load the specified/default config file if available."""
        self._config = {}
        self.filename = filename or self.DEFAULT_FILENAME
        if os.path.exists(self.filename):
            self.load(self.filename)
        else:
            logging.debug('File %s does not exist', filename)

    def __str__(self):
        return json.dumps(self._config, indent=4, sort_keys=True)

    def __delitem__(self, key):
        """The whole config file will be saved."""
        self._config.__delitem__(key)
        logging.debug('Key %r deleted', key)
        self.save()

    def __getitem__(self, key):
        """`None` will be returned if key does not exist."""
        if key in self._config:
            return self._config.__getitem__(key)
        logging.debug('Key %r does not exist', key)
        return None

    def __setitem__(self, key, value):
        """The whole config file will be saved."""
        self._config.__setitem__(key, value)
        self.save()

    def clear(self):
        """The whole config file will be saved."""
        self._config = {}
        self.save()

    def load(self, filename):
        """Load config from file."""
        with open(filename, 'rb') as f:
            self._config = json.load(f)
        logging.info('Config loaded from %s', filename)

    def save(self, filename=None):
        """Save config to specified/inited file."""
        filename = filename or self.filename
        with open(filename, 'wb') as f:
            json.dump(self._config, f)
        logging.info('Config saved to %s', filename)


def test():
    logging.basicConfig(level=logging.DEBUG,
                        format='%(levelname)-8s %(message)s')

    # init & str
    config = Config('test.config')
    assert str(config) == '{}', 'Wrong empty presentation'

    # index nonexistent key
    assert not config['void'], 'Nonexistent key should return None'

    # set & get
    config['key'] = 'value'
    assert config['key'] == 'value', 'Wrong value set'

    # delete
    del config['key']
    assert str(config) == '{}', 'Config should be empty after deletion'

    # save & load
    config['saved'] = 'yes'
    config.save('test.copy.config')
    config = Config('test.copy.config')
    assert config['saved'] == 'yes', 'Wrong value after save'

    # clear
    config.clear()
    assert str(config) == '{}', 'Something wrong with clear'

    # clear temporary files
    os.remove(os.path.abspath('test.copy.config'))
    os.remove(os.path.abspath('test.config'))

    print "Don't panic! Everything is fine."


if __name__ == '__main__':
    test()
