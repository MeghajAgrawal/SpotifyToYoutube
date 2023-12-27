from setuptools import setup, find_packages

requires = [
    'flask',
    'spotipy',
    'html5lib',
    'requests',
    'requests_html',
    'beautifulsoup4',
    'youtube_dl',
    'pathlib',
    'pandas'
]

setup(
    name='SpotifyToYotube',
    version='1.0',
    description='An Application to get my Spotify playlist into Youtube Playlist',
    author='Meghaj Agrawal',
    author_email='meghajcr7@gmail.com',
    keywords='web flask',
    packages=find_packages(),
    include_package_data=True,
    install_requires= requires
)