import PyInstaller.__main__
import shutil
import os

app_path = str(os.path.dirname(os.path.realpath(__file__)) + '\\app.py')
icon_path = str(os.path.dirname(os.path.realpath(__file__)) + '\\assets\\icon.ico')

def build():
 shutil.rmtree('dist', ignore_errors=True)
 shutil.rmtree('build', ignore_errors=True)

 PyInstaller.__main__.run([
  app_path,
  '--name=discustom',
  '--onefile',
  '--windowed',
  '--icon=' + icon_path,
  '--version-file=' + version_path
 ])

if __name__ == '__main__':
 build()
 print("Build completed successfully.")
