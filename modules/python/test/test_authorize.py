from helper_test import *

if __name__ == "__main__":
    for filename in glob.glob(os.path.join('../src', '*.*')):
        shutil.copy(filename, base)

    init_params()

    from app.authorize import handler

    result = handler()
    print(result)
