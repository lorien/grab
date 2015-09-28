import tempfile
import os


class BaseTransport(object):
    def reset(self):
        self.body_file = None
        self.body_path = None

    def setup_body_file(self, storage_dir, storage_filename, create_dir=False):
        if create_dir:
            if not os.path.exists(storage_dir):
                os.makedirs(storage_dir)
        if storage_filename is None:
            handle, path = tempfile.mkstemp(dir=storage_dir)
            self.body_file = os.fdopen(handle, 'wb')
        else:
            path = os.path.join(storage_dir, storage_filename)
            self.body_file = open(path, 'wb')
        self.body_path = path
        return self.body_file, self.body_path
