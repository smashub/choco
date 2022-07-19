"""
Utility script for renaming invalid files.
"""
import logging
import os
from pathlib import Path

logger = logging.getLogger("choco.rename.files")

partitions_path = Path('../partitions/ireal-pro')


def rename_files() -> None:
    """
    Utility script for renaming invalid files.
    In partcular, the script goes trough all the partitions/raw files anfd removes question marks nd spaces from the
    """
    for path, dirs, files in os.walk(partitions_path):
        if 'raw' in path:
            logger.info(f'\nParsing filenames in {path}\n')
            for file in files:
                if '?' in file or ' ' in file:
                    try:
                        renamed_file = file.replace('?', '').replace(' ', '_')
                        logger.info(f'- Renaming file: {file.ljust(50)} ----> {renamed_file}')
                        os.rename(Path(path) / file, Path(path) / renamed_file)
                    except PermissionError:
                        logger.exception(f'Impossible to rename file due to a permission error.')
                    except (IsADirectoryError, NotADirectoryError):
                        logger.exception(f'Impossible to rename file. The original file and the renamed one are of '
                                         f'different type.')
                    except OSError as os_error:
                        logger.exception(f'Impossible to rename file due to an error: {os_error}')
                    finally:
                        continue
    return


if __name__ == '__main__':
    rename_files()
