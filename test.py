import subprocess
result = subprocess.Popen('sudo apt update', shell=True).wait()
print('refreshed')