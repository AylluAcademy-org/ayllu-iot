from pathlib import Path

root_dir_name = 'CardanoPython'

if __name__=="__main__":
    config_path = ''
    for d in str(Path(__file__)).split('/'):
        if d != root_dir_name:
            config_path += d + '/'
        else:
            break
    print(config_path)